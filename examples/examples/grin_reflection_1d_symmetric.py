"""1D symmetric Gaussian sampling for GRIN reflection visualization.

This script generates rays sampled symmetrically from a 1D Gaussian distribution
and traces them through a GRIN medium to study reflection and dispersion effects.
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


def generate_symmetric_gaussian_samples(
    num_samples: int = 20,
    center: float = 0.0,
    sigma: float = 1.0,
    wavelength_mean: float = 0.55,
    wavelength_std: float = 0.05,
    random_seed: int = None,
) -> dict:
    """Generate symmetric samples from 1D Gaussian distribution.

    Args:
        num_samples: Total number of samples (will be rounded to even number)
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

    # Equal-spacing incidence positions (user requirement):
    # use symmetric, uniformly spaced rays across [-3σ, 3σ].
    max_distance = 3.0 * sigma
    spacing = 2.0 * max_distance / (num_samples - 1)
    x_positions = np.linspace(-max_distance, max_distance, num_samples)

    # Add center offset
    x_positions = x_positions + center

    # Calculate Gaussian intensity weights
    intensity_weights = norm.pdf(x_positions, loc=center, scale=sigma)
    intensity_weights = intensity_weights / intensity_weights.max()

    # CRITICAL FIX: Generate wavelengths ONLY for positive side, then mirror
    # This ensures symmetric positions have IDENTICAL wavelengths for true symmetry!

    # Standard normal random sampling in FREQUENCY domain, then convert to wavelength.
    # This follows the requirement of 1D Gaussian random sampled frequency light.
    c_um_ps = 299.792458  # speed of light in µm·ps
    mean_frequency = c_um_ps / wavelength_mean
    std_frequency = mean_frequency * (wavelength_std / wavelength_mean)
    positive_frequencies = np.random.normal(mean_frequency, std_frequency, half_samples)
    positive_frequencies = np.clip(positive_frequencies, 1e-9, None)
    positive_wavelengths = c_um_ps / positive_frequencies

    positive_wavelengths = np.clip(positive_wavelengths, 0.3, 1.0)

    # Mirror wavelengths to negative side for TRUE symmetry
    wavelengths = np.concatenate([
        positive_wavelengths[::-1],  # Negative side (mirrored)
        positive_wavelengths          # Positive side
    ])

    return {
        'x_positions': x_positions,
        'wavelengths': wavelengths,
        'intensity_weights': intensity_weights,
        'position_spacing': spacing,
        'num_samples': num_samples,
        'center': center,
        'sigma': sigma,
    }


def generate_symmetric_samples_with_wavelength_gradient(
    num_samples: int = 20,
    center: float = 0.0,
    sigma: float = 1.0,
    wavelength_mean: float = 0.55,
    wavelength_std: float = 0.05,
    wavelength_gradient: float = 0.0,  # µm per mm
    random_seed: int = None,
) -> dict:
    """Generate symmetric samples with wavelength correlated to position.

    This is useful for studying chirped beams or spatially dispersed light.

    Args:
        num_samples: Total number of samples
        center: Mean of the Gaussian distribution
        sigma: Standard deviation of the Gaussian distribution
        wavelength_mean: Mean wavelength in µm
        wavelength_std: Standard deviation of wavelength in µm
        wavelength_gradient: Wavelength change per unit distance (µm/mm)
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary containing x_positions, wavelengths, and intensity_weights
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Ensure even number for perfect symmetry
    num_samples = max(2, num_samples if num_samples % 2 == 0 else num_samples + 1)
    half_samples = num_samples // 2

    # Generate symmetric positions
    max_distance = 3.0 * sigma
    positive_positions = np.linspace(sigma, max_distance, half_samples)
    x_positions = np.concatenate([
        -positive_positions[::-1],
        positive_positions
    ]) + center

    # Calculate Gaussian intensity weights
    intensity_weights = norm.pdf(x_positions, loc=center, scale=sigma)
    intensity_weights = intensity_weights / intensity_weights.max()

    # Generate wavelengths with spatial gradient (optional)
    base_wavelengths = np.random.normal(
        wavelength_mean,
        wavelength_std * 0.5,  # Reduced std since gradient adds variation
        num_samples
    )

    # Add wavelength gradient (wavelength varies with x position)
    wavelengths = base_wavelengths + wavelength_gradient * x_positions

    # Clip wavelengths to physical range
    wavelengths = np.clip(wavelengths, 0.3, 1.0)

    return {
        'x_positions': x_positions,
        'wavelengths': wavelengths,
        'intensity_weights': intensity_weights,
        'num_samples': num_samples,
        'center': center,
        'sigma': sigma,
        'wavelength_gradient': wavelength_gradient,
    }


def visualize_symmetric_samples(
    num_samples: int = 20,
    sigma: float = 1.0,
    wavelength_std: float = 0.05,
    wavelength_gradient: float = 0.0,
    output_file: str = 'symmetric_samples_1d.png',
    use_gradient: bool = False,
):
    """Visualize symmetric Gaussian sampling.

    Args:
        num_samples: Number of samples
        sigma: Standard deviation for spatial distribution
        wavelength_std: Standard deviation for wavelength distribution
        wavelength_gradient: Wavelength gradient (if use_gradient=True)
        output_file: Output filename
        use_gradient: Whether to use wavelength gradient
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib is required for visualization")
        return

    # Generate samples
    if use_gradient:
        data = generate_symmetric_samples_with_wavelength_gradient(
            num_samples=num_samples,
            sigma=sigma,
            wavelength_std=wavelength_std,
            wavelength_gradient=wavelength_gradient,
        )
    else:
        data = generate_symmetric_gaussian_samples(
            num_samples=num_samples,
            sigma=sigma,
            wavelength_std=wavelength_std,
        )

    x_pos = data['x_positions']
    wavelengths = data['wavelengths']
    intensities = data['intensity_weights']

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Spatial distribution
    ax1 = axes[0, 0]
    x_plot = np.linspace(-4*sigma, 4*sigma, 200)
    gaussian_curve = norm.pdf(x_plot, loc=0, scale=sigma)

    ax1.plot(x_plot, gaussian_curve, 'b-', linewidth=2, label='Gaussian distribution')
    ax1.scatter(x_pos, intensities, c=wavelengths, cmap='rainbow',
                s=100*intensities, alpha=0.7, edgecolors='black',
                label='Sampled rays')
    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.3, label='Center')
    ax1.set_xlabel('X Position (mm)', fontsize=12)
    ax1.set_ylabel('Probability Density', fontsize=12)
    ax1.set_title('1D Symmetric Gaussian Sampling', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Add colorbar for wavelength
    cbar1 = plt.colorbar(ax1.collections[0], ax=ax1)
    cbar1.set_label('Wavelength (µm)', fontsize=10)

    # Plot 2: Wavelength distribution
    ax2 = axes[0, 1]
    ax2.scatter(range(len(wavelengths)), wavelengths, c=range(len(wavelengths)),
                cmap='rainbow', s=80, alpha=0.7, edgecolors='black')
    ax2.axhline(y=np.mean(wavelengths), color='r', linestyle='--',
                label=f'Mean: {np.mean(wavelengths):.3f} µm')
    ax2.set_xlabel('Ray Index', fontsize=12)
    ax2.set_ylabel('Wavelength (µm)', fontsize=12)
    ax2.set_title('Wavelength Distribution', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Plot 3: Position vs Wavelength (correlation)
    ax3 = axes[1, 0]
    scatter = ax3.scatter(x_pos, wavelengths, c=intensities, cmap='viridis',
                         s=80, alpha=0.7, edgecolors='black')
    ax3.set_xlabel('X Position (mm)', fontsize=12)
    ax3.set_ylabel('Wavelength (µm)', fontsize=12)
    ax3.set_title('Position-Wavelength Correlation', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax3.axhline(y=0.55, color='r', linestyle='--', alpha=0.3, label='Reference (0.55µm)')
    ax3.legend()

    cbar3 = plt.colorbar(scatter, ax=ax3)
    cbar3.set_label('Intensity Weight', fontsize=10)

    # Plot 4: Intensity weights
    ax4 = axes[1, 1]
    ax4.bar(range(len(x_pos)), intensities, color=plt.cm.rainbow(
        (wavelengths - wavelengths.min()) / (wavelengths.max() - wavelengths.min() + 1e-9)),
            alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Ray Index (sorted by position)', fontsize=12)
    ax4.set_ylabel('Intensity Weight', fontsize=12)
    ax4.set_title('Intensity Weights', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved symmetric sampling visualization to '{output_file}'")

    # Print statistics
    print(f"\n{'='*60}")
    print("1D Symmetric Gaussian Sampling Statistics")
    print(f"{'='*60}")
    print(f"Number of samples: {num_samples}")
    print(f"Spatial distribution: N(0, σ={sigma:.3f})")
    print(f"X position range: [{x_pos.min():.3f}, {x_pos.max():.3f}] mm")
    print(f"Wavelength range: [{wavelengths.min():.3f}, {wavelengths.max():.3f}] µm")
    print(f"Wavelength mean: {np.mean(wavelengths):.3f} ± {np.std(wavelengths):.3f} µm")
    if use_gradient:
        print(f"Wavelength gradient: {wavelength_gradient:.4f} µm/mm")
    print(f"Intensity weight range: [{intensities.min():.3f}, {intensities.max():.3f}]")
    print(f"{'='*60}\n")

    plt.close(fig)


def trace_rays_1d_symmetric(
    num_samples: int = 20,
    sigma: float = 1.0,
    wavelength_mean: float = 0.55,
    wavelength_std: float = 0.08,
    angle_deg: float = 15.0,
    use_drude: bool = True,
    plasma_wl0: float = 0.8,
    plasma_wl1: float = -0.05,
    n_floor: float = 1e-3,
    random_seed: int = 42,
    enforce_cutoff_reflection: bool = True,
    output_file: str = 'grin_reflection_1d_symmetric.png',
):
    """Trace rays from symmetric 1D Gaussian distribution through GRIN medium.

    Args:
        num_samples: Number of rays
        sigma: Spatial distribution width
        wavelength_mean: Mean wavelength
        wavelength_std: Wavelength standard deviation
        angle_deg: Incidence angle in degrees
        use_drude: Whether to use Drude dispersion model
        plasma_wl0: Drude plasma wavelength at z=0
        plasma_wl1: Drude plasma wavelength gradient
        output_file: Output filename
    """
    try:
        from optiland.materials.gradient_material import GradientMaterial
        from optiland.propagation.grin import GRINPropagation
        from optiland.rays import RealRays

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
    except ImportError as e:
        print(f"Import error: {e}")
        return

    # Define DispersiveGradientMaterial class here for standalone use
    import optiland.backend as be

    class DispersiveGradientMaterial(GradientMaterial):
        """
        Gradient index material with Drude dispersion model for plasma mirrors.

        PHYSICAL MODEL:
        For a plasma, the refractive index follows the Drude model:
            n(ω) = √(1 - ωp²/ω²) = √(1 - λ²/λp²)
        """
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

        def _get_plasma_wavelength(self, z: float) -> float:
            """Calculate plasma wavelength at position z."""
            return self.plasma_wavelength_0 + self.plasma_wavelength_1 * z

        def _calculate_n(self, wavelength: float, **kwargs) -> float:
            """Calculate refractive index using Drude model."""
            z = kwargs.get("z", 0.0)
            lambda_p = self._get_plasma_wavelength(z)

            ratio_squared = (wavelength / lambda_p) ** 2

            # Use np.where to handle array inputs
            n_drude = np.sqrt(np.maximum(0.0, 1.0 - ratio_squared))
            n_final = 1.0 + self.plasma_density_factor * (n_drude - 1.0)

            # Keep geometric ray tracing in real domain.
            n_final = np.where(ratio_squared < 1.0, n_final, self.n_floor)

            return n_final

        def get_index_and_gradient(self, x, y, z, wavelength: float):
            """Calculate refractive index and its gradient with Drude dispersion."""
            lambda_p = self._get_plasma_wavelength(z)
            ratio = wavelength / lambda_p
            ratio_squared = ratio ** 2

            # Calculate refractive index using Drude model
            n = be.where(
                ratio_squared < 1.0,
                1.0 + self.plasma_density_factor * (be.sqrt(1.0 - ratio_squared) - 1.0),
                self.n_floor,
            )

            # Calculate axial gradient directly:
            # dn/dz = f * lambda_p1 * wavelength^2 / (lambda_p^3 * sqrt(1 - ratio^2))
            sqrt_term = be.sqrt(be.maximum(1.0 - ratio_squared, 1e-12))
            dn_dz = be.where(
                ratio_squared < 1.0,
                self.plasma_density_factor
                * self.plasma_wavelength_1
                * (wavelength ** 2)
                / (lambda_p ** 3 * sqrt_term),
                0.0,
            )

            dn_dx = be.zeros_like(n)
            dn_dy = be.zeros_like(n)

            return n, dn_dx, dn_dy, dn_dz

    # Generate symmetric samples
    samples = generate_symmetric_gaussian_samples(
        num_samples=num_samples,
        sigma=sigma,
        wavelength_mean=wavelength_mean,
        wavelength_std=wavelength_std,
        random_seed=random_seed,
    )

    x_positions = samples['x_positions']
    wavelengths = samples['wavelengths']
    intensities = samples['intensity_weights']

    # Create material
    if use_drude:
        material = DispersiveGradientMaterial(
            plasma_wavelength_0=plasma_wl0,
            plasma_wavelength_1=plasma_wl1,
            plasma_density_factor=1.0,
            n_floor=n_floor,
        )
        model_name = f"Drude Model (λp₀={plasma_wl0}, λp₁={plasma_wl1})"
    else:
        material = GradientMaterial(n0=2.0, nz1=-0.3)
        model_name = "No Dispersion (n=2.0-0.3z)"

    # Initialize propagation
    prop = GRINPropagation(material)
    thickness = 10.0
    angle_rad = np.deg2rad(angle_deg)

    # Create rays
    rays = RealRays(
        x=x_positions,
        y=np.zeros(num_samples),
        z=np.zeros(num_samples),
        L=np.full(num_samples, np.sin(angle_rad)),
        M=np.zeros(num_samples),
        N=np.full(num_samples, np.cos(angle_rad)),
        intensity=intensities,
        wavelength=wavelengths,
    )

    # Store initial positions for path recording
    initial_x = rays.x.copy()
    initial_z = rays.z.copy()

    # Propagate
    print(f"\nTracing {num_samples} rays through GRIN medium...")
    print(f"Model: {model_name}")
    print(f"Incidence angle: {angle_deg}°")
    print(f"Wavelength range: {wavelengths.min():.3f} - {wavelengths.max():.3f} µm")
    print(f"Equal position spacing: {samples['position_spacing']:.4f} mm")

    # Use manual integration for path recording
    dt = 0.001  # Integration step size
    max_steps = 100000

    # Store paths for each ray
    ray_paths_x = [[] for _ in range(num_samples)]
    ray_paths_z = [[] for _ in range(num_samples)]

    for i in range(num_samples):
        # Initialize ray state
        x_curr = float(initial_x[i])
        z_curr = float(initial_z[i])
        L_curr = float(rays.L[i])
        N_curr = float(rays.N[i])
        w_curr = float(wavelengths[i])

        # Record initial point
        ray_paths_x[i].append(x_curr)
        ray_paths_z[i].append(z_curr)

        inside = False
        for step in range(max_steps):
            # Check if entered medium
            if z_curr > 0.001:
                inside = True

            # Check if exited
            if inside and (z_curr <= 0.0 or z_curr >= thickness):
                break

            # Get derivatives
            dx_ds, dy_ds, dz_ds, dL_ds, dM_ds, dN_ds = prop._ray_derivative(
                np.array([x_curr]),
                np.array([0.0]),
                np.array([z_curr]),
                np.array([L_curr]),
                np.array([0.0]),
                np.array([N_curr]),
                np.array([w_curr])
            )

            # Update state (RK4)
            x_curr += dt * dx_ds[0]
            z_curr += dt * dz_ds[0]
            L_curr += dt * dL_ds[0]
            N_curr += dt * dN_ds[0]

            # Normalize direction
            norm = np.sqrt(L_curr**2 + N_curr**2)
            if norm > 0:
                L_curr /= norm
                N_curr /= norm

            # Explicit real-valued reflection trigger at Drude cutoff.
            if use_drude and enforce_cutoff_reflection:
                lambda_p_curr = material._get_plasma_wavelength(z_curr)
                ratio_sq_curr = (w_curr / lambda_p_curr) ** 2
                if ratio_sq_curr >= 1.0 and N_curr > 0.0:
                    N_curr = -abs(N_curr)

            # Record point
            ray_paths_x[i].append(x_curr)
            ray_paths_z[i].append(z_curr)

        # Update final ray state
        rays.x[i] = x_curr
        rays.z[i] = z_curr
        rays.L[i] = L_curr
        rays.N[i] = N_curr

    # Analyze results
    reflected = rays.z < 0
    num_reflected = np.sum(reflected)
    print(f"Reflected rays: {num_reflected}/{num_samples} ({100*num_reflected/num_samples:.1f}%)")

    # Find turning points for reflected rays
    turning_points = []
    turning_wavelengths = []

    if num_reflected > 0:
        # Find turning points from path data (where z is maximum)
        for i in np.where(reflected)[0]:
            z_path = np.array(ray_paths_z[i])
            if len(z_path) > 0:
                turning_z = np.max(z_path)  # Turning point is where z is maximum
                turning_points.append(turning_z)
                turning_wavelengths.append(wavelengths[i])

        if turning_points:
            print(f"Turning point range: {np.min(turning_points):.3f} - {np.max(turning_points):.3f} mm")
            print(f"Turning point spread: {np.max(turning_points) - np.min(turning_points):.3f} mm")

    # Visualization
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[3, 2, 1])

    # Main ray trace plot
    ax_main = fig.add_subplot(gs[0, :])
    for i in range(num_samples):
        color = plt.cm.rainbow((wavelengths[i] - 0.4) / 0.6)
        alpha = 0.3 + 0.7 * intensities[i]
        # Plot complete ray path
        ax_main.plot(ray_paths_z[i], ray_paths_x[i],
                    color=color, alpha=alpha, linewidth=1.5)

    ax_main.axvline(x=0, color='k', linestyle='--', alpha=0.3, label='Entrance')
    ax_main.axvline(x=thickness, color='b', linestyle='--', alpha=0.3, label='Exit')
    ax_main.set_xlabel('Z Position (mm)', fontsize=12)
    ax_main.set_ylabel('X Position (mm)', fontsize=12)
    ax_main.set_title(f'GRIN Ray Tracing - 1D Symmetric Sampling\n{model_name}',
                     fontsize=14, fontweight='bold')
    ax_main.grid(True, alpha=0.3)
    ax_main.legend()

    # Wavelength vs X position (initial)
    ax_wl_x = fig.add_subplot(gs[1, 0])
    scatter = ax_wl_x.scatter(x_positions, wavelengths, c=intensities,
                             cmap='viridis', s=100, alpha=0.7, edgecolors='black')
    ax_wl_x.set_xlabel('Initial X Position (mm)', fontsize=11)
    ax_wl_x.set_ylabel('Wavelength (µm)', fontsize=11)
    ax_wl_x.set_title('Initial Wavelength Distribution', fontsize=12)
    ax_wl_x.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax_wl_x, label='Intensity')

    # Final positions
    ax_final = fig.add_subplot(gs[1, 1])
    if num_reflected > 0:
        ax_final.scatter(rays.x[reflected], rays.z[reflected],
                        c=wavelengths[reflected], cmap='rainbow',
                        s=100*intensities[reflected], alpha=0.7,
                        edgecolors='black', label='Reflected')
    not_reflected = ~reflected
    if np.sum(not_reflected) > 0:
        ax_final.scatter(rays.x[not_reflected], rays.z[not_reflected],
                        c=wavelengths[not_reflected], cmap='rainbow',
                        s=100*intensities[not_reflected], alpha=0.3,
                        edgecolors='black', marker='x', label='Transmitted')
    ax_final.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax_final.set_xlabel('X Position (mm)', fontsize=11)
    ax_final.set_ylabel('Final Z Position (mm)', fontsize=11)
    ax_final.set_title('Final Positions', fontsize=12)
    ax_final.grid(True, alpha=0.3)
    ax_final.legend()

    # Info panel
    ax_info = fig.add_subplot(gs[2, :])
    ax_info.axis('off')

    info_text = f"""
    Symmetric 1D Sampling Results:
    • Total rays: {num_samples}  |  Reflected: {num_reflected} ({100*num_reflected/num_samples:.1f}%)
    • Spatial σ: {sigma:.3f} mm  |  Wavelength: {wavelengths.min():.3f} - {wavelengths.max():.3f} µm
    • Model: {model_name}
    • Incidence angle: {angle_deg}°
    """
    if turning_points:
        info_text += f" • Turning point spread: {np.max(turning_points) - np.min(turning_points):.3f} mm"

    ax_info.text(0.5, 0.5, info_text, ha='center', va='center',
                fontsize=12, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved ray tracing visualization to '{output_file}'")
    print(f"{'='*60}\n")

    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="1D Symmetric Gaussian Sampling for GRIN Reflection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize symmetric sampling (no ray tracing)
  python grin_reflection_1d_symmetric.py --visualize-only --num-samples 20

  # Visualize with wavelength gradient
  python grin_reflection_1d_symmetric.py --visualize-only --wavelength-gradient 0.05

  # Ray tracing with Drude model
  python grin_reflection_1d_symmetric.py --num-samples 30 --sigma 1.5 --use-drude

  # Ray tracing without dispersion
  python grin_reflection_1d_symmetric.py --no-drude --num-samples 20
        """
    )

    parser.add_argument('--visualize-only', '-v', action='store_true',
                       help='Only visualize sampling, no ray tracing')
    parser.add_argument('--num-samples', '-n', type=int, default=20,
                       help='Number of samples (default: 20)')
    parser.add_argument('--sigma', '-s', type=float, default=1.0,
                       help='Standard deviation of spatial distribution (default: 1.0)')
    parser.add_argument('--wavelength-mean', type=float, default=0.55,
                       help='Mean wavelength in µm (default: 0.55)')
    parser.add_argument('--wavelength-std', type=float, default=0.05,
                       help='Wavelength standard deviation in µm (default: 0.05)')
    parser.add_argument('--wavelength-gradient', '-g', type=float, default=0.0,
                       help='Wavelength gradient (µm/mm, for --visualize-only)')
    parser.add_argument('--angle', type=float, default=15.0,
                       help='Incidence angle in degrees (default: 15.0)')
    parser.add_argument('--use-drude', action='store_true', default=True,
                       help='Use Drude dispersion model (default: True)')
    parser.add_argument('--no-drude', dest='use_drude', action='store_false',
                       help='Disable Drude dispersion model')
    parser.add_argument('--plasma-wl0', type=float, default=0.8,
                       help='Drude plasma wavelength at z=0 (default: 0.8)')
    parser.add_argument('--plasma-wl1', type=float, default=-0.05,
                       help='Drude plasma wavelength gradient (default: -0.05)')
    parser.add_argument('--output', '-o', type=str,
                       default='grin_reflection_1d_symmetric.png',
                       help='Output filename (default: grin_reflection_1d_symmetric.png)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducible frequency sampling (default: 42)')
    parser.add_argument('--n-floor', type=float, default=1e-3,
                       help='Real refractive-index floor in evanescent region (default: 1e-3)')
    parser.add_argument('--disable-cutoff-reflection', action='store_true',
                       help='Disable explicit reflection trigger at Drude cutoff')

    args = parser.parse_args()

    print("="*60)
    print("1D Symmetric Gaussian Sampling for GRIN Reflection")
    print("="*60)

    if args.visualize_only:
        # Only visualize sampling
        output_file = args.output.replace('.png', '_sampling.png')
        visualize_symmetric_samples(
            num_samples=args.num_samples,
            sigma=args.sigma,
            wavelength_std=args.wavelength_std,
            wavelength_gradient=args.wavelength_gradient,
            output_file=output_file,
            use_gradient=(args.wavelength_gradient != 0.0),
        )
    else:
        # Full ray tracing
        trace_rays_1d_symmetric(
            num_samples=args.num_samples,
            sigma=args.sigma,
            wavelength_mean=args.wavelength_mean,
            wavelength_std=args.wavelength_std,
            angle_deg=args.angle,
            use_drude=args.use_drude,
            plasma_wl0=args.plasma_wl0,
            plasma_wl1=args.plasma_wl1,
            n_floor=args.n_floor,
            random_seed=args.seed,
            enforce_cutoff_reflection=(not args.disable_cutoff_reflection),
            output_file=args.output,
        )
