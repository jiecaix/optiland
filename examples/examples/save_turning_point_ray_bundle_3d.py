"""Visualize dispersive turning-point ray bundles in 3D.

This example builds a physically richer ray bundle than the earlier ring export:

- rays launch from the entrance plane ``z=0`` with mutually parallel directions
- transverse launch positions are sampled from a 2D Gaussian beam profile
- ray frequencies are sampled from a Gaussian spectrum to exercise dispersion
- the medium can be either a strong axial GRIN profile or a Drude-like cutoff
- full 3D trajectories, including reflected segments after the turning point,
  are exported to VTP and plotted in a 3-panel matplotlib figure

The figure is designed to work well with matplotlib's ``WebAgg`` backend and
contains:

1. the full 3D ray trajectories,
2. refractive index versus axial position for representative wavelengths,
3. a 2D histogram of the random Gaussian beam samples at ``z=0``.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import vtk

from optiland.materials import GradientMaterial

C_UM_PER_S = 299_792_458.0 * 1e6


@dataclass(frozen=True)
class RayBundle:
    """Input ray states and their sampled wavelengths."""

    states: np.ndarray
    wavelengths: np.ndarray
    frequencies_thz: np.ndarray


class DispersiveAxialGRINMaterial(GradientMaterial):
    """Axially varying GRIN medium with simple Cauchy-like dispersion."""

    def __init__(
        self,
        n0: float = 1.62,
        cauchy_b: float = 0.015,
        cauchy_c: float = 0.0008,
        nz1: float = -0.085,
        nz2: float = -0.001,
        nz3: float = 0.0,
        n_floor: float = 0.15,
    ):
        super().__init__(n0=n0, nz1=nz1, nz2=nz2, nz3=nz3)
        self.cauchy_b = cauchy_b
        self.cauchy_c = cauchy_c
        self.n_floor = n_floor

    def _dispersion_term(self, wavelength: np.ndarray) -> np.ndarray:
        wavelength = np.asarray(wavelength, dtype=float)
        return self.cauchy_b / wavelength**2 + self.cauchy_c / wavelength**4

    def get_index_and_gradient(self, x, y, z, wavelength: float):
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        z = np.atleast_1d(np.asarray(z, dtype=float))
        wavelength_array = np.full_like(z, float(wavelength), dtype=float)

        n = (
            self.n0
            + self._dispersion_term(wavelength_array)
            + self.nz1 * z
            + self.nz2 * z**2
            + self.nz3 * z**3
        )
        n = np.maximum(n, self.n_floor)
        dn_dx = np.zeros_like(n)
        dn_dy = np.zeros_like(n)
        dn_dz = self.nz1 + 2.0 * self.nz2 * z + 3.0 * self.nz3 * z**2
        return n, dn_dx, dn_dy, dn_dz


class DrudeTurningMaterial(GradientMaterial):
    """Real-domain Drude-like material with axial plasma-wavelength ramp."""

    def __init__(
        self,
        background_n: float = 1.05,
        background_b: float = 0.006,
        plasma_wavelength_0: float = 0.92,
        plasma_wavelength_1: float = -0.055,
        plasma_density_factor: float = 1.0,
        n_floor: float = 0.03,
    ):
        super().__init__(n0=background_n, nz1=0.0)
        self.background_n = background_n
        self.background_b = background_b
        self.plasma_wavelength_0 = plasma_wavelength_0
        self.plasma_wavelength_1 = plasma_wavelength_1
        self.plasma_density_factor = plasma_density_factor
        self.n_floor = n_floor

    def _background_index(self, wavelength: np.ndarray) -> np.ndarray:
        return self.background_n + self.background_b / wavelength**2

    def _get_plasma_wavelength(self, z: np.ndarray) -> np.ndarray:
        return self.plasma_wavelength_0 + self.plasma_wavelength_1 * z

    def get_index_and_gradient(self, x, y, z, wavelength: float):
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        z = np.atleast_1d(np.asarray(z, dtype=float))
        wavelength_array = np.full_like(z, float(wavelength), dtype=float)

        lambda_p = self._get_plasma_wavelength(z)
        ratio_squared = (wavelength_array / lambda_p) ** 2
        sqrt_term = np.sqrt(np.maximum(1.0 - ratio_squared, 1e-12))
        background = self._background_index(wavelength_array)

        n = np.where(
            ratio_squared < 1.0,
            background + self.plasma_density_factor * (sqrt_term - 1.0),
            self.n_floor,
        )
        dn_dz = np.where(
            ratio_squared < 1.0,
            self.plasma_density_factor
            * self.plasma_wavelength_1
            * (wavelength_array**2)
            / (lambda_p**3 * sqrt_term),
            0.0,
        )
        dn_dx = np.zeros_like(n)
        dn_dy = np.zeros_like(n)
        return n, dn_dx, dn_dy, dn_dz


def ray_derivative(material, state: np.ndarray, wavelength: float) -> np.ndarray:
    x, y, z, l_dir, m_dir, n_dir = state
    n, dn_dx, dn_dy, dn_dz = material.get_index_and_gradient(
        np.array([x]), np.array([y]), np.array([z]), wavelength
    )
    n = float(np.asarray(n)[0])
    dn_dx = float(np.asarray(dn_dx)[0])
    dn_dy = float(np.asarray(dn_dy)[0])
    dn_dz = float(np.asarray(dn_dz)[0])

    dot_product = l_dir * dn_dx + m_dir * dn_dy + n_dir * dn_dz
    return np.array(
        [
            l_dir,
            m_dir,
            n_dir,
            (dn_dx - l_dir * dot_product) / n,
            (dn_dy - m_dir * dot_product) / n,
            (dn_dz - n_dir * dot_product) / n,
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
    """Trace one ray and keep the reflected segment after the turning point."""

    state = state.astype(float).copy()
    state[3:6] /= np.linalg.norm(state[3:6])
    history = [state.copy()]
    z_min, z_max = z_bounds
    turning_index = -1
    entered_medium = False
    prev_n_dir = state[5]

    for _ in range(num_steps):
        if state[2] > z_min + 1e-8:
            entered_medium = True
        if entered_medium and state[2] <= z_min:
            break
        if state[2] > z_max:
            break

        k1 = ray_derivative(material, state, wavelength)
        k2 = ray_derivative(material, state + 0.5 * step_size * k1, wavelength)
        k3 = ray_derivative(material, state + 0.5 * step_size * k2, wavelength)
        k4 = ray_derivative(material, state + step_size * k3, wavelength)
        state = state + (step_size / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        state[3:6] /= np.linalg.norm(state[3:6])
        history.append(state.copy())

        current_n_dir = state[5]
        if turning_index < 0 and prev_n_dir > 0.0 and current_n_dir <= 0.0:
            turning_index = len(history) - 1
        prev_n_dir = current_n_dir

    return np.asarray(history), turning_index


def build_parallel_direction(incident_angle_deg: float, azimuth_deg: float) -> np.ndarray:
    """Create a common direction vector for all incident rays."""

    incident_angle = math.radians(incident_angle_deg)
    azimuth = math.radians(azimuth_deg)
    transverse = math.sin(incident_angle)
    l_dir = transverse * math.cos(azimuth)
    m_dir = transverse * math.sin(azimuth)
    n_dir = math.sqrt(max(1e-12, 1.0 - l_dir**2 - m_dir**2))
    return np.array([l_dir, m_dir, n_dir], dtype=float)


def sample_gaussian_ray_bundle(
    num_rays: int,
    beam_sigma_x: float,
    beam_sigma_y: float,
    z_start: float,
    incident_angle_deg: float,
    azimuth_deg: float,
    central_frequency_thz: float,
    frequency_sigma_thz: float,
    rng: np.random.Generator,
) -> RayBundle:
    """Sample parallel rays from a 2D Gaussian source and Gaussian spectrum."""

    xy = rng.normal(
        loc=np.zeros(2, dtype=float),
        scale=np.array([beam_sigma_x, beam_sigma_y], dtype=float),
        size=(num_rays, 2),
    )
    direction = build_parallel_direction(incident_angle_deg, azimuth_deg)
    direction_block = np.repeat(direction[None, :], num_rays, axis=0)

    frequencies_thz = rng.normal(
        loc=central_frequency_thz,
        scale=frequency_sigma_thz,
        size=num_rays,
    )
    min_frequency = max(1e-6, central_frequency_thz - 4.0 * frequency_sigma_thz)
    frequencies_thz = np.clip(frequencies_thz, min_frequency, None)
    wavelengths = C_UM_PER_S / (frequencies_thz * 1e12)

    states = np.column_stack(
        [
            xy[:, 0],
            xy[:, 1],
            np.full(num_rays, z_start, dtype=float),
            direction_block,
        ]
    )
    return RayBundle(states=states, wavelengths=wavelengths, frequencies_thz=frequencies_thz)


def write_vtp(
    histories: list[np.ndarray],
    turning_indices: list[int],
    wavelengths: np.ndarray,
    frequencies_thz: np.ndarray,
    output_path: Path,
) -> None:
    """Export traced trajectories and metadata to VTK PolyData."""

    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    ray_ids = vtk.vtkIntArray()
    ray_ids.SetName("ray_id")
    turning_mask = vtk.vtkIntArray()
    turning_mask.SetName("turning_point")
    wavelength_array = vtk.vtkFloatArray()
    wavelength_array.SetName("wavelength_um")
    frequency_array = vtk.vtkFloatArray()
    frequency_array.SetName("frequency_thz")

    point_offset = 0
    for ray_id, (history, turning_idx, wavelength, frequency_thz) in enumerate(
        zip(histories, turning_indices, wavelengths, frequencies_thz)
    ):
        poly_line = vtk.vtkPolyLine()
        poly_line.GetPointIds().SetNumberOfIds(len(history))
        for local_idx, state in enumerate(history):
            x, y, z = state[:3]
            points.InsertNextPoint(float(x), float(y), float(z))
            poly_line.GetPointIds().SetId(local_idx, point_offset + local_idx)
            ray_ids.InsertNextValue(ray_id)
            turning_mask.InsertNextValue(1 if local_idx == turning_idx else 0)
            wavelength_array.InsertNextValue(float(wavelength))
            frequency_array.InsertNextValue(float(frequency_thz))
        point_offset += len(history)
        lines.InsertNextCell(poly_line)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)
    poly_data.GetPointData().AddArray(ray_ids)
    poly_data.GetPointData().AddArray(turning_mask)
    poly_data.GetPointData().AddArray(wavelength_array)
    poly_data.GetPointData().AddArray(frequency_array)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputData(poly_data)
    writer.Write()


def build_material(args):
    if args.model == "drude":
        return DrudeTurningMaterial(
            background_n=args.background_n,
            background_b=args.background_b,
            plasma_wavelength_0=args.plasma_wavelength_0,
            plasma_wavelength_1=args.plasma_wavelength_1,
            plasma_density_factor=args.plasma_density_factor,
            n_floor=args.n_floor,
        )
    return DispersiveAxialGRINMaterial(
        n0=args.n0,
        cauchy_b=args.cauchy_b,
        cauchy_c=args.cauchy_c,
        nz1=args.nz1,
        nz2=args.nz2,
        nz3=args.nz3,
        n_floor=args.n_floor,
    )


def configure_matplotlib_backend(backend: str) -> tuple[str, str | None]:
    """Select the requested matplotlib backend before importing pyplot."""

    if backend == "webagg":
        try:
            matplotlib.use("WebAgg")
            return "webagg", None
        except RuntimeError as error:
            matplotlib.use("Agg")
            return "agg", (
                "WebAgg requested but unavailable; falling back to Agg. "
                f"Reason: {error}"
            )

    matplotlib.use("Agg")
    return "agg", None


def create_summary_figure(
    histories: list[np.ndarray],
    turning_indices: list[int],
    bundle: RayBundle,
    material,
    z_max: float,
    figure_path: Path | None,
    backend: str,
    show_plot: bool,
):
    """Create the requested 3-panel figure for WebAgg or static export."""

    import matplotlib.pyplot as plt
    from matplotlib import cm, colors

    fig = plt.figure(figsize=(16, 5.5), constrained_layout=True)
    ax3d = fig.add_subplot(1, 3, 1, projection="3d")
    ax_n = fig.add_subplot(1, 3, 2)
    ax_samples = fig.add_subplot(1, 3, 3)

    norm = colors.Normalize(
        vmin=float(bundle.frequencies_thz.min()),
        vmax=float(bundle.frequencies_thz.max()),
    )
    cmap = matplotlib.colormaps["viridis"]

    turning_points = []
    for history, turning_idx, frequency_thz in zip(
        histories, turning_indices, bundle.frequencies_thz
    ):
        color = cmap(norm(float(frequency_thz)))
        ax3d.plot(history[:, 0], history[:, 1], history[:, 2], color=color, alpha=0.85, lw=1.2)
        if turning_idx >= 0:
            turn_state = history[turning_idx]
            turning_points.append(turn_state[:3])
            ax3d.scatter(
                [turn_state[0]],
                [turn_state[1]],
                [turn_state[2]],
                color="crimson",
                s=14,
                depthshade=False,
            )

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    color_bar = fig.colorbar(sm, ax=ax3d, fraction=0.05, pad=0.02)
    color_bar.set_label("Frequency (THz)")
    ax3d.set_title("3D turning-point trajectories")
    ax3d.set_xlabel("x")
    ax3d.set_ylabel("y")
    ax3d.set_zlabel("z")
    ax3d.view_init(elev=25, azim=130)

    z_values = np.linspace(0.0, z_max, 500)
    representative = np.quantile(bundle.wavelengths, [0.1, 0.5, 0.9])
    for wavelength in representative:
        n_values, *_ = material.get_index_and_gradient(
            np.zeros_like(z_values),
            np.zeros_like(z_values),
            z_values,
            float(wavelength),
        )
        ax_n.plot(z_values, n_values, label=f"λ={wavelength:.3f} μm")
    if turning_points:
        turning_z = np.array(turning_points)[:, 2]
        ax_n.axvline(np.median(turning_z), color="crimson", ls="--", lw=1.0, label="median turning z")
    ax_n.set_title("Dispersive refractive-index profile")
    ax_n.set_xlabel("z")
    ax_n.set_ylabel("n(z, λ)")
    ax_n.grid(True, alpha=0.25)
    ax_n.legend(loc="best", fontsize=8)

    hist = ax_samples.hist2d(
        bundle.states[:, 0],
        bundle.states[:, 1],
        bins=40,
        cmap="magma",
    )
    fig.colorbar(hist[3], ax=ax_samples, fraction=0.05, pad=0.02, label="count")
    ax_samples.set_title("Random 2D Gaussian launch samples")
    ax_samples.set_xlabel("x at z=0")
    ax_samples.set_ylabel("y at z=0")
    ax_samples.set_aspect("equal", adjustable="box")

    fig.suptitle(
        "Parallel Gaussian beam with spectral dispersion in a turning-point medium",
        fontsize=14,
    )

    if figure_path is not None:
        fig.savefig(figure_path, dpi=180)

    if show_plot:
        if backend != "webagg":
            raise ValueError(
                "--show-plot requires an active WebAgg backend; install tornado or "
                "rerun without --show-plot."
            )
        plt.show()
    else:
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sample a Gaussian beam with a Gaussian frequency spectrum, trace "
            "real 3D turning/reflection trajectories in a dispersive axial "
            "GRIN or Drude medium, export VTP, and generate a WebAgg-ready "
            "summary figure."
        )
    )
    parser.add_argument("--model", choices=["axial", "drude"], default="axial")
    parser.add_argument("--backend", choices=["agg", "webagg"], default="agg")
    parser.add_argument("--show-plot", action="store_true")
    parser.add_argument("--output-vtp", type=Path, default=Path("turning_point_ray_bundle.vtp"))
    parser.add_argument(
        "--output-figure",
        type=Path,
        default=Path("turning_point_ray_bundle_webagg.png"),
    )
    parser.add_argument("--num-rays", type=int, default=180)
    parser.add_argument("--beam-sigma-x", type=float, default=0.7)
    parser.add_argument("--beam-sigma-y", type=float, default=0.4)
    parser.add_argument("--incident-angle-deg", type=float, default=30.0)
    parser.add_argument("--azimuth-deg", type=float, default=35.0)
    parser.add_argument("--central-frequency-thz", type=float, default=520.0)
    parser.add_argument("--frequency-sigma-thz", type=float, default=22.0)
    parser.add_argument("--step-size", type=float, default=0.01)
    parser.add_argument("--num-steps", type=int, default=3200)
    parser.add_argument("--z-max", type=float, default=11.0)
    parser.add_argument("--seed", type=int, default=7)

    parser.add_argument("--n0", type=float, default=1.72)
    parser.add_argument("--cauchy-b", type=float, default=0.02)
    parser.add_argument("--cauchy-c", type=float, default=0.001)
    parser.add_argument("--nz1", type=float, default=-0.15)
    parser.add_argument("--nz2", type=float, default=-0.005)
    parser.add_argument("--nz3", type=float, default=0.0)
    parser.add_argument("--background-n", type=float, default=1.06)
    parser.add_argument("--background-b", type=float, default=0.004)
    parser.add_argument("--plasma-wavelength-0", type=float, default=0.92)
    parser.add_argument("--plasma-wavelength-1", type=float, default=-0.055)
    parser.add_argument("--plasma-density-factor", type=float, default=1.0)
    parser.add_argument("--n-floor", type=float, default=0.03)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    active_backend, backend_warning = configure_matplotlib_backend(args.backend)

    rng = np.random.default_rng(args.seed)
    material = build_material(args)
    bundle = sample_gaussian_ray_bundle(
        num_rays=args.num_rays,
        beam_sigma_x=args.beam_sigma_x,
        beam_sigma_y=args.beam_sigma_y,
        z_start=0.0,
        incident_angle_deg=args.incident_angle_deg,
        azimuth_deg=args.azimuth_deg,
        central_frequency_thz=args.central_frequency_thz,
        frequency_sigma_thz=args.frequency_sigma_thz,
        rng=rng,
    )

    histories: list[np.ndarray] = []
    turning_indices: list[int] = []
    for state, wavelength in zip(bundle.states, bundle.wavelengths):
        history, turning_idx = trace_single_ray(
            material,
            state,
            wavelength=float(wavelength),
            step_size=args.step_size,
            num_steps=args.num_steps,
            z_bounds=(0.0, args.z_max),
        )
        histories.append(history)
        turning_indices.append(turning_idx)

    write_vtp(
        histories,
        turning_indices,
        bundle.wavelengths,
        bundle.frequencies_thz,
        args.output_vtp,
    )
    create_summary_figure(
        histories,
        turning_indices,
        bundle,
        material,
        z_max=args.z_max,
        figure_path=args.output_figure,
        backend=active_backend,
        show_plot=args.show_plot,
    )

    turned = sum(index >= 0 for index in turning_indices)
    print(f"Saved VTP trajectories to '{args.output_vtp}'.")
    print(f"Saved summary figure to '{args.output_figure}'.")
    print(
        "Model: "
        f"{args.model}; detected turning points in {turned}/{len(turning_indices)} rays; "
        f"backend={active_backend}."
    )
    if backend_warning is not None:
        print(backend_warning)
    if args.show_plot and active_backend == "webagg":
        print("WebAgg server started via matplotlib; open the printed local URL in a browser.")


if __name__ == "__main__":
    main()
