"""Evidence script for GRIN + Drude model consistency checks.

This script provides lightweight, dependency-free checks to validate two claims:
1) The old dn/dz implementation has an extra lambda_p^-2 factor.
2) Returning complex n in cutoff region makes ray-direction derivatives complex.

Run:
    python examples/examples/grin_drude_evidence.py
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass
class DrudeParams:
    lambda_p0: float = 0.8
    lambda_p1: float = -0.05
    density_factor: float = 1.0


def plasma_wavelength(z: float, p: DrudeParams) -> float:
    return p.lambda_p0 + p.lambda_p1 * z


def n_real(wavelength: float, z: float, p: DrudeParams) -> float:
    """Real-valued Drude refractive index in propagating region."""
    lp = plasma_wavelength(z, p)
    ratio_sq = (wavelength / lp) ** 2
    if ratio_sq >= 1.0:
        return 0.0
    n_drude = math.sqrt(1.0 - ratio_sq)
    return 1.0 + p.density_factor * (n_drude - 1.0)


def n_with_complex_cutoff(wavelength: float, z: float, p: DrudeParams) -> complex:
    """Mimic current example behavior: use -1+0j when ratio_sq>=1."""
    lp = plasma_wavelength(z, p)
    ratio_sq = (wavelength / lp) ** 2
    if ratio_sq < 1.0:
        n_drude = math.sqrt(1.0 - ratio_sq)
        return 1.0 + p.density_factor * (n_drude - 1.0)
    return -1.0 + 0j


def dn_dz_current_bug(wavelength: float, z: float, p: DrudeParams) -> float:
    """Derivative form used in current example implementation (buggy)."""
    lp = plasma_wavelength(z, p)
    ratio = wavelength / lp
    ratio_sq = ratio * ratio
    if ratio_sq >= 1.0:
        return 0.0
    return (
        p.density_factor
        * p.lambda_p1
        * (ratio_sq / (lp**3) / math.sqrt(1.0 - ratio_sq))
    )


def dn_dz_correct(wavelength: float, z: float, p: DrudeParams) -> float:
    """Correct derivative from chain rule.

    n = 1 + f*(sqrt(1 - lambda^2/lp^2)-1), lp = lp(z)
    dn/dz = f * [lambda^2/(lp^3*sqrt(1-lambda^2/lp^2))] * dlp/dz
    """
    lp = plasma_wavelength(z, p)
    ratio_sq = (wavelength / lp) ** 2
    if ratio_sq >= 1.0:
        return 0.0
    return (
        p.density_factor
        * p.lambda_p1
        * (wavelength**2)
        / (lp**3 * math.sqrt(1.0 - ratio_sq))
    )


def finite_diff_dn_dz(wavelength: float, z: float, p: DrudeParams, h: float = 1e-6) -> float:
    n_plus = n_real(wavelength, z + h, p)
    n_minus = n_real(wavelength, z - h, p)
    return (n_plus - n_minus) / (2.0 * h)


def report_gradient_consistency(p: DrudeParams) -> None:
    print("=" * 78)
    print("Check A: dn/dz formula consistency")
    print("=" * 78)
    print("Columns: λ(um), z(mm), dn/dz(correct), dn/dz(finite-diff), rel.err, buggy/correct")

    wavelengths = [0.44, 0.50, 0.55, 0.61]
    z_values = [0.0, 1.0, 2.0, 3.0]

    for wl in wavelengths:
        for z in z_values:
            lp = plasma_wavelength(z, p)
            if (wl / lp) ** 2 >= 1.0:
                continue
            d_correct = dn_dz_correct(wl, z, p)
            d_fd = finite_diff_dn_dz(wl, z, p)
            d_bug = dn_dz_current_bug(wl, z, p)
            rel_err = abs(d_correct - d_fd) / max(abs(d_correct), 1e-14)
            ratio = d_bug / d_correct if d_correct != 0 else float("nan")
            print(
                f"{wl:>4.2f}  {z:>4.1f}  {d_correct:>+12.6e}  {d_fd:>+12.6e}  "
                f"{rel_err:>8.2e}  {ratio:>8.3f}"
            )

    print("\nExpected evidence:")
    print("- rel.err should be tiny for correct derivative (matches finite difference).")
    print("- buggy/correct should be about 1/lambda_p(z)^2, proving extra lambda_p^-2 factor.")


def ray_dN_ds_from_dn_dz(n_value: complex, dn_dz: float, N: float = 0.95) -> complex:
    """Minimal slice of GRIN propagation formula when dn_dx=dn_dy=0.

    dN/ds = (1/n) * (dn_dz - N*(N*dn_dz)) = (1/n) * dn_dz * (1 - N^2)
    """
    return (1.0 / n_value) * dn_dz * (1.0 - N * N)


def report_complex_cutoff_issue(p: DrudeParams) -> None:
    print("\n" + "=" * 78)
    print("Check B: complex n at cutoff leaks into ray-direction derivative")
    print("=" * 78)

    wl = 0.61
    for z in [3.5, 4.0, 4.2, 4.4]:
        lp = plasma_wavelength(z, p)
        ratio_sq = (wl / lp) ** 2
        n_c = n_with_complex_cutoff(wl, z, p)
        dn = dn_dz_correct(wl, z, p)
        dN = ray_dN_ds_from_dn_dz(n_c, dn)
        type_tag = "complex" if isinstance(dN, complex) else "real"
        print(
            f"z={z:>4.1f} mm, lambda_p={lp:>5.3f}, ratio^2={ratio_sq:>6.3f}, "
            f"n={n_c}, dN/ds={dN} ({type_tag})"
        )

    print("\nExpected evidence:")
    print("- Once ratio^2 >= 1, model returns -1+0j.")
    print("- dN/ds follows 1/n and therefore becomes complex-typed in the update chain.")


def main() -> None:
    parser = argparse.ArgumentParser(description="GRIN+Drude evidence checks")
    parser.add_argument("--lambda-p0", type=float, default=0.8)
    parser.add_argument("--lambda-p1", type=float, default=-0.05)
    parser.add_argument("--density-factor", type=float, default=1.0)
    args = parser.parse_args()

    params = DrudeParams(
        lambda_p0=args.lambda_p0,
        lambda_p1=args.lambda_p1,
        density_factor=args.density_factor,
    )

    report_gradient_consistency(params)
    report_complex_cutoff_issue(params)


if __name__ == "__main__":
    main()
