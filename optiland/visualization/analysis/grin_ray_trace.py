"""Simple 2D/3D GRIN ray-trace visualization helpers.

This module focuses on visualization-oriented trajectory tracing for rays
propagating inside gradient-index media.
"""

from __future__ import annotations

import itertools

import matplotlib.pyplot as plt
import numpy as np

import optiland.backend as be
from optiland.visualization.analysis.gradient_field import GradientFieldViewer


class GRINRayTraceViewer:
    """Trace and visualize ray trajectories in a gradient-index material."""

    _VALID_PROJECTIONS = {"XY", "XZ", "YZ"}

    def __init__(self, material):
        self.material = material
        self.field_viewer = GradientFieldViewer(material)

    def trace_fan(
        self,
        num_rays: int = 5,
        spread: float = 1.0,
        angle_span: float = 0.2,
        plane: str = "XZ",
        wavelength: float = 0.55,
        start_coordinate: float = 0.0,
        z_start: float = 0.0,
        step_size: float = 0.02,
        num_steps: int = 600,
        z_bounds: tuple[float, float] | None = None,
    ) -> list[dict[str, np.ndarray]]:
        """Trace a simple symmetric ray fan."""
        plane = plane.upper()
        if plane not in {"XZ", "YZ"}:
            raise ValueError("plane must be 'XZ' or 'YZ' for fan tracing.")

        offsets = np.linspace(-spread, spread, num_rays)
        tilts = np.linspace(-angle_span, angle_span, num_rays)

        rays = []
        for offset, tilt in zip(offsets, tilts, strict=False):
            x0, y0 = 0.0, 0.0
            L0, M0 = 0.0, 0.0
            if plane == "XZ":
                x0 = offset
                y0 = start_coordinate
                L0 = tilt
            else:
                x0 = start_coordinate
                y0 = offset
                M0 = tilt

            N0 = float(np.sqrt(max(1.0 - L0**2 - M0**2, 1e-12)))
            rays.append({
                "x": x0,
                "y": y0,
                "z": z_start,
                "L": L0,
                "M": M0,
                "N": N0,
                "wavelength": wavelength,
            })

        return self.trace_rays(
            rays,
            step_size=step_size,
            num_steps=num_steps,
            z_bounds=z_bounds,
        )

    def trace_rays(
        self,
        rays: list[dict[str, float]],
        step_size: float = 0.02,
        num_steps: int = 600,
        z_bounds: tuple[float, float] | None = None,
    ) -> list[dict[str, np.ndarray]]:
        """Trace a list of rays and return their recorded histories."""
        return [
            self._trace_single_ray(
                ray=ray,
                step_size=step_size,
                num_steps=num_steps,
                z_bounds=z_bounds,
            )
            for ray in rays
        ]

    def view_2d(
        self,
        histories: list[dict[str, np.ndarray]],
        projection: str = "XZ",
        ax=None,
        linewidth: float = 1.8,
        show_start: bool = True,
        show_end: bool = True,
        field: str | None = None,
        contour_lines: bool = True,
        fixed_coordinate: float = 0.0,
        wavelength: float = 0.55,
        extent: float | None = None,
    ):
        """Plot traced trajectories on a 2D projection."""
        projection = projection.upper()
        if projection not in self._VALID_PROJECTIONS:
            raise ValueError("projection must be one of 'XY', 'XZ', or 'YZ'.")

        if ax is None:
            fig, ax = plt.subplots(figsize=(7, 5))
        else:
            fig = ax.get_figure()

        if extent is None:
            extent = self._default_extent(histories, projection)

        if field is not None:
            self.field_viewer.view(
                wavelength=wavelength,
                field=field,
                plane=projection,
                extent=extent,
                fixed_coordinate=fixed_coordinate,
                contour_lines=contour_lines,
                ax=ax,
            )

        coord_a, coord_b = projection
        colors = itertools.cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])
        for history, color in zip(histories, colors, strict=False):
            a = history[coord_a.lower()]
            b = history[coord_b.lower()]
            ax.plot(a, b, linewidth=linewidth, color=color)
            if show_start:
                ax.scatter(a[0], b[0], color=color, s=22, marker="o", zorder=5)
            if show_end:
                ax.scatter(a[-1], b[-1], color=color, s=28, marker="x", zorder=5)

        ax.set_xlabel(f"{coord_a} [mm]")
        ax.set_ylabel(f"{coord_b} [mm]")
        ax.set_title(f"GRIN ray tracing ({projection} view)")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.25)

        return fig, ax

    def view_3d(
        self,
        histories: list[dict[str, np.ndarray]],
        ax=None,
        linewidth: float = 1.8,
        show_start: bool = True,
        show_end: bool = True,
    ):
        """Plot traced trajectories in 3D using Matplotlib."""
        if ax is None:
            fig = plt.figure(figsize=(7, 6))
            ax = fig.add_subplot(111, projection="3d")
        else:
            fig = ax.get_figure()

        colors = itertools.cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])
        for history, color in zip(histories, colors, strict=False):
            ax.plot(
                history["x"],
                history["y"],
                history["z"],
                linewidth=linewidth,
                color=color,
            )
            if show_start:
                ax.scatter(
                    history["x"][0],
                    history["y"][0],
                    history["z"][0],
                    color=color,
                    s=24,
                    marker="o",
                )
            if show_end:
                ax.scatter(
                    history["x"][-1],
                    history["y"][-1],
                    history["z"][-1],
                    color=color,
                    s=28,
                    marker="x",
                )

        ax.set_xlabel("X [mm]")
        ax.set_ylabel("Y [mm]")
        ax.set_zlabel("Z [mm]")
        ax.set_title("GRIN ray tracing (3D view)")

        return fig, ax

    def _trace_single_ray(
        self,
        ray: dict[str, float],
        step_size: float,
        num_steps: int,
        z_bounds: tuple[float, float] | None,
    ) -> dict[str, np.ndarray]:
        state = np.array(
            [
                ray["x"],
                ray["y"],
                ray["z"],
                ray["L"],
                ray["M"],
                ray["N"],
            ],
            dtype=float,
        )
        state[3:6] /= np.linalg.norm(state[3:6])

        history = [state.copy()]
        wavelength = ray.get("wavelength", 0.55)
        z_min, z_max = z_bounds if z_bounds is not None else (-np.inf, np.inf)

        for _ in range(num_steps):
            if state[2] < z_min or state[2] > z_max:
                break

            k1 = self._ray_derivative(state, wavelength)
            k2 = self._ray_derivative(state + 0.5 * step_size * k1, wavelength)
            k3 = self._ray_derivative(state + 0.5 * step_size * k2, wavelength)
            k4 = self._ray_derivative(state + step_size * k3, wavelength)

            state = state + (step_size / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            state[3:6] /= np.linalg.norm(state[3:6])
            history.append(state.copy())

        data = np.asarray(history)
        return {
            "x": data[:, 0],
            "y": data[:, 1],
            "z": data[:, 2],
            "L": data[:, 3],
            "M": data[:, 4],
            "N": data[:, 5],
            "wavelength": np.full(len(data), wavelength),
        }

    def _ray_derivative(self, state: np.ndarray, wavelength: float) -> np.ndarray:
        x, y, z, L, M, N = state
        if hasattr(self.material, "get_index_and_gradient"):
            n, dn_dx, dn_dy, dn_dz = self.material.get_index_and_gradient(
                be.array([x]),
                be.array([y]),
                be.array([z]),
                wavelength,
            )
            n = float(be.to_numpy(n)[0])
            dn_dx = float(be.to_numpy(dn_dx)[0])
            dn_dy = float(be.to_numpy(dn_dy)[0])
            dn_dz = float(be.to_numpy(dn_dz)[0])
        else:
            n = float(
                be.to_numpy(
                    self.material._calculate_n(
                        wavelength,
                        x=be.array([x]),
                        y=be.array([y]),
                        z=be.array([z]),
                    )
                )[0]
            )
            dn_dx = 0.0
            dn_dy = 0.0
            dn_dz = 0.0

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

    @staticmethod
    def _default_extent(
        histories: list[dict[str, np.ndarray]],
        projection: str,
    ) -> float:
        values = []
        for history in histories:
            for axis in projection:
                values.extend(history[axis.lower()].tolist())
        return max(max(abs(v) for v in values), 1.0) * 1.1
