"""Gradient-index field visualization helpers.

This module provides a lightweight viewer for plotting 2D slices through
spatially varying refractive-index materials.

Kramer Harrison, 2026
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import optiland.backend as be


class GradientFieldViewer:
    """Visualize simple 2D slices of a gradient-index material.

    The viewer samples a material on a regular grid and renders one of the
    following scalar fields on an ``XY``, ``XZ``, or ``YZ`` slice:

    - refractive index (``index``)
    - partial derivatives (``dn_dx``, ``dn_dy``, ``dn_dz``)
    - gradient magnitude (``grad_mag``)

    Args:
        material: Material instance to sample. Materials that implement
            ``get_index_and_gradient`` provide full support. Other materials can
            still be viewed with ``field='index'``.
    """

    _VALID_PLANES = {"XY", "XZ", "YZ"}
    _VALID_FIELDS = {"index", "dn_dx", "dn_dy", "dn_dz", "grad_mag"}

    def __init__(self, material):
        self.material = material

    def view(
        self,
        wavelength: float = 0.55,
        field: str = "index",
        plane: str = "XZ",
        extent: float = 5.0,
        fixed_coordinate: float = 0.0,
        num_points: int = 200,
        cmap: str = "viridis",
        contour_lines: bool = False,
        contour_levels: int = 10,
        colorbar: bool = True,
        ax=None,
    ):
        """Render a 2D slice through the material.

        Args:
            wavelength: Wavelength in microns.
            field: Quantity to render. One of ``index``, ``dn_dx``, ``dn_dy``,
                ``dn_dz``, or ``grad_mag``.
            plane: Slice plane. One of ``XY``, ``XZ``, or ``YZ``.
            extent: Half-width of the slice in millimeters.
            fixed_coordinate: Coordinate used for the axis that is not shown in
                the slice plane.
            num_points: Number of sample points per axis.
            cmap: Matplotlib colormap.
            contour_lines: Whether to overlay refractive-index contours.
            contour_levels: Number of contour levels when ``contour_lines`` is
                enabled.
            colorbar: Whether to draw a colorbar.
            ax: Optional matplotlib axes.

        Returns:
            tuple: ``(fig, ax, artist)`` for further customization.
        """
        plane = plane.upper()
        if plane not in self._VALID_PLANES:
            raise ValueError("plane must be one of 'XY', 'XZ', or 'YZ'.")
        if field not in self._VALID_FIELDS:
            raise ValueError(
                "field must be one of 'index', 'dn_dx', 'dn_dy', 'dn_dz', or "
                "'grad_mag'."
            )

        sampled = self.sample_slice(
            wavelength=wavelength,
            field=field,
            plane=plane,
            extent=extent,
            fixed_coordinate=fixed_coordinate,
            num_points=num_points,
        )
        axis_a, axis_b = plane

        if ax is None:
            fig, ax = plt.subplots(figsize=(7, 5))
        else:
            fig = ax.get_figure()

        artist = ax.contourf(
            sampled["grid_a"],
            sampled["grid_b"],
            sampled["values"],
            levels=50,
            cmap=cmap,
        )

        if contour_lines:
            ax.contour(
                sampled["grid_a"],
                sampled["grid_b"],
                sampled["index_values"],
                levels=contour_levels,
                colors="white",
                linewidths=0.7,
                alpha=0.75,
            )

        ax.set_aspect("equal")
        ax.set_xlabel(f"{axis_a} [mm]")
        ax.set_ylabel(f"{axis_b} [mm]")
        ax.set_title(
            f"{self._field_label(field)} on {plane} plane "
            f"({self._fixed_axis(plane)}={fixed_coordinate:.2f} mm)"
        )

        if colorbar:
            cbar = fig.colorbar(artist, ax=ax)
            cbar.set_label(self._field_label(field))

        return fig, ax, artist

    def sample_slice(
        self,
        wavelength: float = 0.55,
        field: str = "index",
        plane: str = "XZ",
        extent: float = 5.0,
        fixed_coordinate: float = 0.0,
        num_points: int = 200,
    ) -> dict[str, np.ndarray]:
        """Sample a 2D slice through the material and return raw arrays."""
        plane = plane.upper()
        if plane not in self._VALID_PLANES:
            raise ValueError("plane must be one of 'XY', 'XZ', or 'YZ'.")
        if field not in self._VALID_FIELDS:
            raise ValueError(
                "field must be one of 'index', 'dn_dx', 'dn_dy', 'dn_dz', or "
                "'grad_mag'."
            )

        axis_a, axis_b = plane
        axis_coords = np.linspace(-extent, extent, num_points)
        grid_a, grid_b = np.meshgrid(axis_coords, axis_coords)

        coords = {
            "X": np.full_like(grid_a, fixed_coordinate, dtype=float),
            "Y": np.full_like(grid_a, fixed_coordinate, dtype=float),
            "Z": np.full_like(grid_a, fixed_coordinate, dtype=float),
        }
        coords[axis_a] = grid_a
        coords[axis_b] = grid_b

        x = be.array(coords["X"])
        y = be.array(coords["Y"])
        z = be.array(coords["Z"])

        if hasattr(self.material, "get_index_and_gradient"):
            n, dn_dx, dn_dy, dn_dz = self.material.get_index_and_gradient(
                x, y, z, wavelength
            )
        else:
            n = self.material._calculate_n(wavelength, x=x, y=y, z=z)
            dn_dx = be.zeros_like(n)
            dn_dy = be.zeros_like(n)
            dn_dz = be.zeros_like(n)

        field_map = {
            "index": n,
            "dn_dx": dn_dx,
            "dn_dy": dn_dy,
            "dn_dz": dn_dz,
            "grad_mag": be.sqrt(dn_dx**2 + dn_dy**2 + dn_dz**2),
        }

        return {
            "grid_a": np.asarray(grid_a),
            "grid_b": np.asarray(grid_b),
            "values": be.to_numpy(field_map[field]),
            "index_values": be.to_numpy(n),
            "plane": plane,
            "fixed_coordinate": fixed_coordinate,
        }

    @staticmethod
    def _fixed_axis(plane: str) -> str:
        return next(axis for axis in "XYZ" if axis not in plane)

    @staticmethod
    def _field_label(field: str) -> str:
        return {
            "index": "Refractive index",
            "dn_dx": "dn/dx",
            "dn_dy": "dn/dy",
            "dn_dz": "dn/dz",
            "grad_mag": "|∇n|",
        }[field]
