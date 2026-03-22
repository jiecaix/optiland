"""Export turning-point / reflected 3D GRIN ray trajectories to VTP.

This script launches a 3D ring bundle from the entrance plane ``z=0`` with the
main propagation direction along ``+z``. It supports two models:

- ``axial``: strong axial GRIN, e.g. ``n(z)=n0 + nz1*z`` with ``nz1 < 0``
- ``drude``: a simple real-domain Drude cutoff model that produces turning
  points near the plasma cutoff without entering the complex domain

The resulting trajectories, including the reflected / turning segment, are
saved as a ``.vtp`` file that can be inspected interactively in ParaView.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import vtk

from optiland.materials import GradientMaterial


class DrudeTurningMaterial(GradientMaterial):
    """Minimal real-domain Drude material for turning-point visualization."""

    def __init__(
        self,
        plasma_wavelength_0: float = 0.8,
        plasma_wavelength_1: float = -0.05,
        plasma_density_factor: float = 1.0,
        n_floor: float = 1e-3,
    ):
        super().__init__(n0=1.0, nz1=0.0)
        self.plasma_wavelength_0 = plasma_wavelength_0
        self.plasma_wavelength_1 = plasma_wavelength_1
        self.plasma_density_factor = plasma_density_factor
        self.n_floor = n_floor

    def _get_plasma_wavelength(self, z):
        return self.plasma_wavelength_0 + self.plasma_wavelength_1 * z

    def _calculate_n(self, wavelength: float, **kwargs):
        z = kwargs.get("z", 0.0)
        lambda_p = self._get_plasma_wavelength(z)
        ratio_squared = (wavelength / lambda_p) ** 2
        n_drude = np.sqrt(np.maximum(0.0, 1.0 - ratio_squared))
        n_final = 1.0 + self.plasma_density_factor * (n_drude - 1.0)
        return np.where(ratio_squared < 1.0, n_final, self.n_floor)

    def get_index_and_gradient(self, x, y, z, wavelength: float):
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        z = np.atleast_1d(np.asarray(z, dtype=float))

        lambda_p = self._get_plasma_wavelength(z)
        ratio_squared = (wavelength / lambda_p) ** 2
        sqrt_term = np.sqrt(np.maximum(1.0 - ratio_squared, 1e-12))

        n = np.where(
            ratio_squared < 1.0,
            1.0 + self.plasma_density_factor * (sqrt_term - 1.0),
            self.n_floor,
        )
        dn_dz = np.where(
            ratio_squared < 1.0,
            self.plasma_density_factor
            * self.plasma_wavelength_1
            * (wavelength**2)
            / (lambda_p**3 * sqrt_term),
            0.0,
        )
        dn_dx = np.zeros_like(n)
        dn_dy = np.zeros_like(n)
        return n, dn_dx, dn_dy, dn_dz


def ray_derivative(material, state: np.ndarray, wavelength: float) -> np.ndarray:
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
    material,
    state: np.ndarray,
    wavelength: float,
    step_size: float,
    num_steps: int,
    z_bounds: tuple[float, float],
) -> tuple[np.ndarray, int]:
    state = state.astype(float).copy()
    state[3:6] /= np.linalg.norm(state[3:6])
    history = [state.copy()]
    z_min, z_max = z_bounds
    inside = False
    turning_index = -1
    prev_n = state[5]

    for _ in range(num_steps):
        if state[2] > z_min + 1e-6:
            inside = True
        if inside and state[2] <= z_min:
            break
        if state[2] > z_max:
            break

        k1 = ray_derivative(material, state, wavelength)
        k2 = ray_derivative(material, state + 0.5 * step_size * k1, wavelength)
        k3 = ray_derivative(material, state + 0.5 * step_size * k2, wavelength)
        k4 = ray_derivative(material, state + step_size * k3, wavelength)
        state = state + (step_size / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        state[3:6] /= np.linalg.norm(state[3:6])
        history.append(state.copy())

        curr_n = state[5]
        if turning_index < 0 and prev_n > 0 and curr_n <= 0:
            turning_index = len(history) - 1
        prev_n = curr_n

    return np.asarray(history), turning_index


def generate_entrance_bundle(
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
        # Aim slightly inward while propagating toward +z.
        L0 = -math.sin(cone_angle) * math.cos(phi)
        M0 = -math.sin(cone_angle) * math.sin(phi)
        N0 = math.cos(cone_angle)
        rays.append(np.array([x0, y0, z_start, L0, M0, N0], dtype=float))

    rays.append(np.array([0.0, 0.0, z_start, 0.0, 0.0, 1.0], dtype=float))
    return rays


def write_vtp(
    histories: list[np.ndarray],
    turning_indices: list[int],
    output_path: Path,
) -> None:
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    ray_ids = vtk.vtkIntArray()
    ray_ids.SetName("ray_id")
    turning_mask = vtk.vtkIntArray()
    turning_mask.SetName("turning_point")

    point_offset = 0
    for ray_id, (history, turning_idx) in enumerate(zip(histories, turning_indices)):
        poly_line = vtk.vtkPolyLine()
        poly_line.GetPointIds().SetNumberOfIds(len(history))
        for local_idx, state in enumerate(history):
            x, y, z = state[:3]
            points.InsertNextPoint(float(x), float(y), float(z))
            poly_line.GetPointIds().SetId(local_idx, point_offset + local_idx)
            ray_ids.InsertNextValue(ray_id)
            turning_mask.InsertNextValue(1 if local_idx == turning_idx else 0)
        point_offset += len(history)
        lines.InsertNextCell(poly_line)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)
    poly_data.GetPointData().AddArray(ray_ids)
    poly_data.GetPointData().AddArray(turning_mask)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputData(poly_data)
    writer.Write()


def build_material(args):
    if args.model == "drude":
        return DrudeTurningMaterial(
            plasma_wavelength_0=args.plasma_wavelength_0,
            plasma_wavelength_1=args.plasma_wavelength_1,
            plasma_density_factor=args.plasma_density_factor,
            n_floor=args.n_floor,
        )
    return GradientMaterial(n0=args.n0, nz1=args.nz1, nz2=args.nz2, nz3=args.nz3)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Trace a 3D ray bundle from z=0, generate turning/reflection-like "
            "segments in a strong axial GRIN or Drude medium, and export VTP."
        )
    )
    parser.add_argument("--output", type=Path, default=Path("turning_point_ray_bundle.vtp"))
    parser.add_argument("--model", choices=["axial", "drude"], default="axial")
    parser.add_argument("--num-rays", type=int, default=12)
    parser.add_argument("--radius", type=float, default=1.5)
    parser.add_argument("--cone-angle-deg", type=float, default=8.0)
    parser.add_argument("--wavelength", type=float, default=0.55)
    parser.add_argument("--step-size", type=float, default=0.01)
    parser.add_argument("--num-steps", type=int, default=4000)
    parser.add_argument("--z-max", type=float, default=10.0)
    parser.add_argument("--n0", type=float, default=2.0)
    parser.add_argument("--nz1", type=float, default=-0.3)
    parser.add_argument("--nz2", type=float, default=0.0)
    parser.add_argument("--nz3", type=float, default=0.0)
    parser.add_argument("--plasma-wavelength-0", type=float, default=0.8)
    parser.add_argument("--plasma-wavelength-1", type=float, default=-0.05)
    parser.add_argument("--plasma-density-factor", type=float, default=1.0)
    parser.add_argument("--n-floor", type=float, default=1e-3)
    args = parser.parse_args()

    material = build_material(args)
    rays = generate_entrance_bundle(
        num_rays=args.num_rays,
        radius=args.radius,
        cone_angle_deg=args.cone_angle_deg,
        z_start=0.0,
    )

    histories = []
    turning_indices = []
    for ray in rays:
        history, turning_idx = trace_single_ray(
            material,
            ray,
            wavelength=args.wavelength,
            step_size=args.step_size,
            num_steps=args.num_steps,
            z_bounds=(0.0, args.z_max),
        )
        histories.append(history)
        turning_indices.append(turning_idx)

    write_vtp(histories, turning_indices, args.output)
    turned = sum(idx >= 0 for idx in turning_indices)
    print(f"Saved turning-point 3D ray bundle to '{args.output}'")
    print(f"Model: {args.model}; rays with detected turning points: {turned}/{len(histories)}")
    print("Open the file in ParaView; threshold by 'turning_point' to mark the turn.")


if __name__ == "__main__":
    main()
