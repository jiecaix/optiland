"""Tests for ray path recording functionality."""

import numpy as np
import optiland.backend as be
import pytest

from optiland.rays import RealRays
from optiland.samples.objectives import TessarLens
from optiland.surfaces import Surface
from tests.utils import assert_allclose


class TestRealRaysPathRecording:
    """Test RealRays path recording functionality."""

    def test_initial_state_no_path(self):
        """Test that initially there is no path data."""
        rays = RealRays(
            x=be.array([0.0]),
            y=be.array([0.0]),
            z=be.array([0.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        assert not rays.has_path()
        assert rays.get_path() == (None, None, None)

    def test_start_recording(self):
        """Test starting path recording."""
        rays = RealRays(
            x=be.array([0.0]),
            y=be.array([0.0]),
            z=be.array([0.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        rays.start_path_recording()
        assert rays._recording_path
        # Initialize empty arrays
        assert rays._path_x is not None
        assert rays._path_y is not None
        assert rays._path_z is not None

    def test_record_path_point(self):
        """Test recording a single path point."""
        rays = RealRays(
            x=be.array([1.0, 2.0]),
            y=be.array([3.0, 4.0]),
            z=be.array([5.0, 6.0]),
            L=be.array([0.0, 0.0]),
            M=be.array([0.0, 0.0]),
            N=be.array([1.0, 1.0]),
            intensity=be.array([1.0, 1.0]),
            wavelength=be.array([0.587, 0.587]),
        )
        # start_path_recording() automatically records the initial position
        rays.start_path_recording()

        assert rays.has_path()
        path_x, path_y, path_z = rays.get_path()

        # start_path_recording records the initial point as the first entry
        assert path_x.shape == (1, 2)
        assert path_y.shape == (1, 2)
        assert path_z.shape == (1, 2)

        assert_allclose(path_x[0, :], be.array([1.0, 2.0]))
        assert_allclose(path_y[0, :], be.array([3.0, 4.0]))
        assert_allclose(path_z[0, :], be.array([5.0, 6.0]))

    def test_record_multiple_points(self):
        """Test recording multiple path points."""
        rays = RealRays(
            x=be.array([1.0]),
            y=be.array([2.0]),
            z=be.array([3.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        rays.start_path_recording()  # Records initial position at (1, 2, 3)

        # Update position and record again
        rays.x = be.array([4.0])
        rays.y = be.array([5.0])
        rays.z = be.array([6.0])
        rays._record_path_point()

        path_x, path_y, path_z = rays.get_path()

        # 2 points: initial (1,2,3) + updated (4,5,6)
        assert path_x.shape == (2, 1)
        assert path_y.shape == (2, 1)
        assert path_z.shape == (2, 1)

        assert_allclose(path_x[:, 0], be.array([1.0, 4.0]))
        assert_allclose(path_y[:, 0], be.array([2.0, 5.0]))
        assert_allclose(path_z[:, 0], be.array([3.0, 6.0]))

    def test_stop_recording_preserves_data(self):
        """Test that stopping recording preserves existing data."""
        rays = RealRays(
            x=be.array([1.0]),
            y=be.array([2.0]),
            z=be.array([3.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        rays.start_path_recording()  # Records initial position
        rays.stop_path_recording()

        assert not rays._recording_path
        assert rays.has_path()  # Data still available

    def test_restart_recording_clears_data(self):
        """Test that restarting recording clears previous data."""
        rays = RealRays(
            x=be.array([1.0]),
            y=be.array([2.0]),
            z=be.array([3.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        rays.start_path_recording()  # Records initial position at (1, 2, 3)

        # Restart recording
        rays.start_path_recording()

        # Old data should be cleared, new initial position recorded
        path_x, _, _ = rays.get_path()
        assert path_x.shape == (1, 1)  # Only new initial point
        assert_allclose(path_x[0, 0], 1.0)


class TestSurfaceStoredRays:
    """Test Surface._stored_rays functionality."""

    def test_surface_reset_clears_stored_rays(self):
        """Test that Surface.reset() clears _stored_rays."""
        from optiland import optic

        # Create a simple system with a surface
        system = optic.Optic()
        system.add_surface(index=0, thickness=10)

        # Get the first surface
        surf = system.surface_group.surfaces[0]

        # Create rays with path
        rays = RealRays(
            x=be.array([0.0]),
            y=be.array([1.0]),
            z=be.array([0.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )

        # Manually set _stored_rays (simulating what _record() does)
        surf._stored_rays = rays
        assert surf._stored_rays is not None

        surf.reset()
        assert surf._stored_rays is None


class TestSurfaceGroupRayPaths:
    """Test SurfaceGroup ray path collection."""

    def test_has_ray_paths_false_initially(self):
        """Test that has_ray_paths is False initially."""
        optic = TessarLens()
        assert not optic.surface_group.has_ray_paths

    def test_has_ray_paths_false_without_grin(self):
        """Test that has_ray_paths is False for standard lens."""
        optic = TessarLens()
        optic.trace(Hx=0, Hy=0, wavelength=0.587)

        assert not optic.surface_group.has_ray_paths

    def test_get_ray_paths_empty_without_grin(self):
        """Test that get_ray_paths() returns empty list without GRIN."""
        optic = TessarLens()
        optic.trace(Hx=0, Hy=0, wavelength=0.587)

        paths = optic.surface_group.get_ray_paths()
        assert paths == []

    def test_get_ray_paths_filters_surfaces_without_path(self):
        """Test that get_ray_paths() only returns surfaces with path data."""
        from optiland import optic

        # Create a simple system
        system = optic.Optic()
        system.add_surface(index=0, thickness=10)
        system.add_surface(index=1, thickness=5)

        # Manually setup some rays with path data on first surface only
        rays_with_path = RealRays(
            x=be.array([0.0]),
            y=be.array([1.0]),
            z=be.array([0.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        # start_path_recording automatically records initial position
        rays_with_path.start_path_recording()

        # First surface has path
        system.surface_group.surfaces[0]._stored_rays = rays_with_path

        # Second surface has rays without path
        rays_no_path = RealRays(
            x=be.array([0.0]),
            y=be.array([1.0]),
            z=be.array([5.0]),
            L=be.array([0.0]),
            M=be.array([0.0]),
            N=be.array([1.0]),
            intensity=be.array([1.0]),
            wavelength=be.array([0.587]),
        )
        system.surface_group.surfaces[1]._stored_rays = rays_no_path

        paths = system.surface_group.get_ray_paths()

        # Should only return path from first surface
        assert len(paths) == 1
        path_x, path_y, path_z = paths[0]
        assert path_x is not None
        # start_path_recording records initial position, so shape is (1, 1)
        assert path_x.shape == (1, 1)

    def test_surface_group_has_path_methods(self):
        """Test that SurfaceGroup has path-related methods."""
        from optiland import optic

        # Create a simple system
        system = optic.Optic()
        system.add_surface(index=0, thickness=10)

        # Verify the structure is in place for GRIN path recording
        assert hasattr(system.surface_group, "get_ray_paths")
        assert hasattr(system.surface_group, "has_ray_paths")
