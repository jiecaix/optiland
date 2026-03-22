"""Minimal example for visualizing a GRIN field slice.

Run:
    python examples/examples/grin_gradient_field_viewer.py
"""

from __future__ import annotations

import matplotlib
matplotlib.use('webagg')
import matplotlib.pyplot as plt

from optiland.materials import GradientMaterial
from optiland.visualization.analysis import GradientFieldViewer


def main() -> None:
    material = GradientMaterial(
        n0=1.62,
        nr2=-0.015,
        nz1=-0.04,
        nz2=0.002,
    )
    viewer = GradientFieldViewer(material)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    viewer.view(
        field="index",
        plane="XZ",
        extent=5.0,
        num_points=200,
        contour_lines=True,
        ax=axes[0],
    )
    viewer.view(
        field="grad_mag",
        plane="XZ",
        extent=5.0,
        num_points=200,
        contour_lines=False,
        ax=axes[1],
    )
    fig.suptitle("Simple GRIN slice visualization")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
