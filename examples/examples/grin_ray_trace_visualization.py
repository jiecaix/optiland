"""Minimal example for 2D/3D GRIN ray-tracing visualization.

Run:
    python examples/examples/grin_ray_trace_visualization.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from optiland.materials import GradientMaterial
from optiland.visualization.analysis import GRINRayTraceViewer


def main() -> None:
    material = GradientMaterial(
        n0=1.62,
        nr2=-0.015,
        nz1=-0.04,
        nz2=0.002,
    )
    viewer = GRINRayTraceViewer(material)
    histories = viewer.trace_fan(
        num_rays=7,
        spread=1.8,
        angle_span=0.22,
        plane="XZ",
        step_size=0.03,
        num_steps=420,
        z_bounds=(0.0, 10.0),
    )

    fig = plt.figure(figsize=(13, 5))
    ax2d = fig.add_subplot(1, 2, 1)
    viewer.view_2d(
        histories,
        projection="XZ",
        field="index",
        contour_lines=True,
        fixed_coordinate=0.0,
        wavelength=0.55,
        ax=ax2d,
    )

    ax3d = fig.add_subplot(1, 2, 2, projection="3d")
    viewer.view_3d(histories, ax=ax3d)

    fig.suptitle("Simple GRIN ray-tracing visualization")
    fig.tight_layout()
    fig.savefig("grin_ray_trace_visualization.png", dpi=150, bbox_inches="tight")
    print("Saved 'grin_ray_trace_visualization.png'")


if __name__ == "__main__":
    main()
