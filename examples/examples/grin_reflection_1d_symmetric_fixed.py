"""1D TRULY symmetric Gaussian sampling for GRIN reflection.

This version ensures that symmetric positions have identical wavelengths,
so the ray trajectories remain perfectly symmetric even with dispersion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add local optiland to path for development
optiland_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(optiland_root))

import numpy as np
from scipy.stats import norm


def generate_truly_symmetric_samples(
    num_samples: int = 20,
    center: float = 0.0,
    sigma: float = 1.0,
    wavelength_mean: float = 0.55,
    wavelength_std: float = 0.05,
    random_seed: int = None,
) -> dict:
    """Generate TRULY symmetric samples with matched wavelengths.

    For perfect symmetry:
    - Generate only positive-side wavelengths
    - Mirror them to negative side
    - This ensures symmetric positions have identical wavelengths

    Args:
        num_samples: Total number of samples (will be rounded to even)
        center: Mean of the Gaussian distribution
        sigma: Standard deviation of the Gaussian distribution
        wavelength_mean: Mean wavelength in µm
        wavelength_std: Standard deviation of wavelength in µm
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary containing x_positions, wavelengths, and intensity_weights
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Ensure even number for perfect symmetry
    num_samples = max(2, num_samples if num_samples % 2 == 0 else num_samples + 1)
    half_samples = num_samples // 2

    # Generate positive side positions
    max_distance = 3.0 * sigma
    positive_positions = np.linspace(sigma, max_distance, half_samples)

    # Create symmetric positions
    x_positions = np.concatenate([
        -positive_positions[::-1],  # Negative side (reversed)
        positive_positions           # Positive side
    ])

    # Add center offset
    x_positions = x_positions + center

    # Generate wavelengths ONLY for positive side, then mirror
    # This ensures symmetric positions have identical wavelengths!
    positive_wavelengths = np.random.normal(
        wavelength_mean,
        wavelength_std,
        half_samples
    )
    positive_wavelengths = np.clip(positive_wavelengths, 0.3, 1.0)

    # Mirror wavelengths to negative side
    wavelengths = np.concatenate([
        positive_wavelengths[::-1],  # Negative side (mirrored)
        positive_wavelengths          # Positive side
    ])

    # Calculate Gaussian intensity weights
    intensity_weights = norm.pdf(x_positions, loc=center, scale=sigma)
    intensity_weights = intensity_weights / intensity_weights.max()

    return {
        'x_positions': x_positions,
        'wavelengths': wavelengths,
        'intensity_weights': intensity_weights,
        'num_samples': num_samples,
        'center': center,
        'sigma': sigma,
    }


def visualize_symmetric_samples(
    num_samples: int = 20,
    sigma: float = 1.0,
    wavelength_std: float = 0.05,
    output_file: str = 'truly_symmetric_samples.png',
):
    """Visualize TRULY symmetric sampling."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib is required for visualization")
        return

    # Generate TRULY symmetric samples
    np.random.seed(42)
    data = generate_truly_symmetric_samples(
        num_samples=num_samples,
        sigma=sigma,
        wavelength_std=wavelength_std,
    )

    x_pos = data['x_positions']
    wavelengths = data['wavelengths']
    intensities = data['intensity_weights']

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Spatial distribution with symmetry lines
    ax1 = axes[0, 0]
    x_plot = np.linspace(-4*sigma, 4*sigma, 200)
    gaussian_curve = norm.pdf(x_plot, loc=0, scale=sigma)

    ax1.plot(x_plot, gaussian_curve, 'b-', linewidth=2, label='Gaussian distribution')

    # Plot samples with color matching
    for i in range(len(x_pos)):
        color = plt.cm.rainbow((wavelengths[i] - 0.4) / 0.6)
        ax1.scatter(x_pos[i], intensities[i], c=[color],
                   s=100*intensities[i], alpha=0.7, edgecolors='black')

    # Draw symmetry lines
    n = len(x_pos) // 2
    for i in range(n):
        j = len(x_pos) - 1 - i
        ax1.plot([x_pos[i], x_pos[j]], [intensities[i], intensities[j]],
                'r-', alpha=0.3, linewidth=1)

    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.3, label='Center')
    ax1.set_xlabel('X Position (mm)', fontsize=12)
    ax1.set_ylabel('Probability Density', fontsize=12)
    ax1.set_title('TRULY Symmetric Sampling (Red lines show symmetry)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Wavelength symmetry check
    ax2 = axes[0, 1]
    n = len(x_pos) // 2
    left_wavelengths = wavelengths[:n]
    right_wavelengths = wavelengths[n:][::-1]  # Reverse for comparison

    ax2.scatter(left_wavelengths, right_wavelengths, c='blue', alpha=0.7, s=80, edgecolors='black')
    ax2.plot([0.3, 1.0], [0.3, 1.0], 'r--', linewidth=2, label='Perfect symmetry')
    ax2.set_xlabel('Left Side Wavelength (µm)', fontsize=12)
    ax2.set_ylabel('Right Side Wavelength (µm)', fontsize=12)
    ax2.set_title('Wavelength Symmetry Check', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Add correlation coefficient
    correlation = np.corrcoef(left_wavelengths, right_wavelengths)[0, 1]
    ax2.text(0.05, 0.95, f'Correlation: {correlation:.6f}', transform=ax2.transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    # Plot 3: Position-wavelength relationship
    ax3 = axes[1, 0]
    scatter = ax3.scatter(x_pos, wavelengths, c=intensities, cmap='viridis',
                         s=80, alpha=0.7, edgecolors='black')
    ax3.set_xlabel('X Position (mm)', fontsize=12)
    ax3.set_ylabel('Wavelength (µm)', fontsize=12)
    ax3.set_title('Position-Wavelength Relationship', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=0, color='k', linestyle='--', alpha=0.3)

    # Add symmetry arrows
    for i in range(n):
        j = len(x_pos) - 1 - i
        if i % 2 == 0:  # Show every other pair to avoid clutter
            ax3.annotate('', xy=(x_pos[i], wavelengths[i]),
                        xytext=(x_pos[j], wavelengths[j]),
                        arrowprops=dict(arrowstyle='<->', color='red', alpha=0.3))

    plt.colorbar(scatter, ax=ax3, label='Intensity Weight')

    # Plot 4: Side-by-side comparison
    ax4 = axes[1, 1]
    x_left = x_pos[:n]
    x_right = x_pos[n:][::-1]  # Reverse for comparison
    wl_left = wavelengths[:n]
    wl_right = wavelengths[n:][::-1]

    x_pairs = np.arange(n)
    width = 0.35

    ax4.bar(x_pairs - width/2, wl_left, width, label='Left side', alpha=0.7)
    ax4.bar(x_pairs + width/2, wl_right, width, label='Right side', alpha=0.7)
    ax4.set_xlabel('Pair Index (from center outward)', fontsize=12)
    ax4.set_ylabel('Wavelength (µm)', fontsize=12)
    ax4.set_title('Side-by-Side Wavelength Comparison', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved TRULY symmetric sampling visualization to '{output_file}'")

    # Print statistics
    print(f"\n{'='*60}")
    print("TRULY Symmetric Gaussian Sampling Statistics")
    print(f"{'='*60}")
    print(f"Number of samples: {num_samples}")
    print(f"Spatial distribution: N(0, σ={sigma:.3f})")
    print(f"X position range: [{x_pos.min():.3f}, {x_pos.max():.3f}] mm")
    print(f"Wavelength range: [{wavelengths.min():.3f}, {wavelengths.max():.3f}] µm")
    print(f"Wavelength mean: {np.mean(wavelengths):.3f} ± {np.std(wavelengths):.3f} µm")
    print(f"Intensity weight range: [{intensities.min():.3f}, {intensities.max():.3f}]")

    # Check symmetry
    print(f"\nSymmetry verification:")
    for i in range(min(3, n)):  # Show first 3 pairs
        j = len(x_pos) - 1 - i
        print(f"  Pair ({i:2d}, {j:2d}): " +
              f"x = [{x_pos[i]:+7.3f}, {x_pos[j]:+7.3f}] | " +
              f"λ = [{wavelengths[i]:.3f}, {wavelengths[j]:.3f}] | " +
              f"Difference: {abs(wavelengths[i] - wavelengths[j]):.6f}")

    print(f"{'='*60}\n")

    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TRULY Symmetric 1D Gaussian Sampling for GRIN Reflection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize TRULY symmetric sampling
  python grin_reflection_1d_symmetric_fixed.py --visualize-only

  # With more samples
  python grin_reflection_1d_symmetric_fixed.py --visualize-only --num-samples 30
        """
    )

    parser.add_argument('--visualize-only', '-v', action='store_true',
                       help='Only visualize sampling, no ray tracing')
    parser.add_argument('--num-samples', '-n', type=int, default=20,
                       help='Number of samples (default: 20)')
    parser.add_argument('--sigma', '-s', type=float, default=1.0,
                       help='Standard deviation (default: 1.0)')
    parser.add_argument('--wavelength-std', type=float, default=0.05,
                       help='Wavelength standard deviation (default: 0.05)')
    parser.add_argument('--output', '-o', type=str,
                       default='truly_symmetric_samples.png',
                       help='Output filename')

    args = parser.parse_args()

    print("="*60)
    print("TRULY Symmetric 1D Gaussian Sampling")
    print("="*60)

    visualize_symmetric_samples(
        num_samples=args.num_samples,
        sigma=args.sigma,
        wavelength_std=args.wavelength_std,
        output_file=args.output,
    )
