"""Export a 3D GRIN ray bundle to a VTK PolyData (.vtp) file.

This is a standalone script meant to keep the repository close to its original
state while still providing a practical 3D export workflow.

Example:
    python examples/examples/save_grin_ray_bundle_3d.py \
        --output grin_ray_bundle.vtp --num-rays 12 --radius 1.5

Open the generated ``.vtp`` file in ParaView for interactive 3D inspection.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import vtk

from optiland.materials import GradientMaterial


def ray_derivative(
    material: GradientMaterial, state: np.ndarray, wavelength: float
) -> np.ndarray:
    x, y, z, L, M, N = state
    n, dn_dx, dn_dy, dn_dz = material.get_index_and_gradient(
        np.array([x]), np.array([y]), np.array([z]), wavelength
    )
    n = float(np.asarray(n)[0])
    dn_dx = float(np.asarray(dn_dx)[0])
    dn_dy = float(np.asarray(dn_dy)[0])
    dn_dz = float(np.asarray(dn_dz)[0])

    dot_product = L * dn_dx + M * dn_dy + N * dn_dz
    return np.array(
        [
            L,
            M,
            N,
            (dn_dx - L * dot_product) / n,
            (dn_dy - M * dot_product) / n,
            (dn_dz - N * dot_product) / n,
        ],
        dtype=float,
    )


def trace_single_ray(
    material: GradientMaterial,
    state: np.ndarray,
    wavelength: float,
    step_size: float,
    num_steps: int,
    z_bounds: tuple[float, float],
) -> np.ndarray:
    state = state.astype(float).copy()
    state[3:6] /= np.linalg.norm(state[3:6])
    history = [state.copy()]
    z_min, z_max = z_bounds

    for _ in range(num_steps):
        if state[2] < z_min or state[2] > z_max:
            break

        k1 = ray_derivative(material, state, wavelength)
        k2 = ray_derivative(material, state + 0.5 * step_size * k1, wavelength)
        k3 = ray_derivative(material, state + 0.5 * step_size * k2, wavelength)
        k4 = ray_derivative(material, state + step_size * k3, wavelength)
        state = state + (step_size / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        state[3:6] /= np.linalg.norm(state[3:6])
        history.append(state.copy())

    return np.asarray(history)


def generate_ring_bundle(
    num_rays: int,
    radius: float,
    cone_angle_deg: float,
    z_start: float,
) -> list[np.ndarray]:
    rays = []
    cone_angle = math.radians(cone_angle_deg)
    for idx in range(num_rays):
        phi = 2.0 * math.pi * idx / num_rays
        x0 = radius * math.cos(phi)
        y0 = radius * math.sin(phi)
        # Slight inward tilt so the 3D file is visually informative.
        L0 = -math.sin(cone_angle) * math.cos(phi)
        M0 = -math.sin(cone_angle) * math.sin(phi)
        N0 = math.cos(cone_angle)
        rays.append(np.array([x0, y0, z_start, L0, M0, N0], dtype=float))

    rays.append(np.array([0.0, 0.0, z_start, 0.0, 0.0, 1.0], dtype=float))
    return rays


def write_vtp(histories: list[np.ndarray], output_path: Path) -> None:
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    ray_ids = vtk.vtkIntArray()
    ray_ids.SetName("ray_id")

    point_offset = 0
    for ray_id, history in enumerate(histories):
        poly_line = vtk.vtkPolyLine()
        poly_line.GetPointIds().SetNumberOfIds(len(history))
        for local_idx, state in enumerate(history):
            x, y, z = state[:3]
            points.InsertNextPoint(float(x), float(y), float(z))
            poly_line.GetPointIds().SetId(local_idx, point_offset + local_idx)
            ray_ids.InsertNextValue(ray_id)
        point_offset += len(history)
        lines.InsertNextCell(poly_line)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)
    poly_data.GetPointData().AddArray(ray_ids)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputData(poly_data)
    writer.Write()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a 3D GRIN ray bundle to VTP"
    )
    parser.add_argument("--output", type=Path, default=Path("grin_ray_bundle.vtp"))
    parser.add_argument("--num-rays", type=int, default=12)
    parser.add_argument("--radius", type=float, default=1.5)
    parser.add_argument("--cone-angle-deg", type=float, default=6.0)
    parser.add_argument("--wavelength", type=float, default=0.55)
    parser.add_argument("--step-size", type=float, default=0.03)
    parser.add_argument("--num-steps", type=int, default=400)
    parser.add_argument("--z-max", type=float, default=10.0)
    parser.add_argument("--n0", type=float, default=1.62)
    parser.add_argument("--nr2", type=float, default=-0.015)
    args = parser.parse_args()

    material = GradientMaterial(n0=args.n0, nr2=args.nr2)
    rays = generate_ring_bundle(
        num_rays=args.num_rays,
        radius=args.radius,
        cone_angle_deg=args.cone_angle_deg,
        z_start=0.0,
    )
    histories = [
        trace_single_ray(
            material,
            ray,
            wavelength=args.wavelength,
            step_size=args.step_size,
            num_steps=args.num_steps,
            z_bounds=(0.0, args.z_max),
        )
        for ray in rays
    ]
    write_vtp(histories, args.output)
    print(f"Saved 3D ray bundle to '{args.output}'")
    print("Open the file in ParaView for interactive 3D exploration.")


if __name__ == "__main__":
    main()
