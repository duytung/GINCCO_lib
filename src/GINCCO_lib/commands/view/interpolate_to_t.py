"""Compatibility wrapper for viewer code.

Use :mod:`GINCCO_lib.modules.interpolate_to_t` for new code. This wrapper
preserves the old viewer behavior of returning only the interpolated field.
"""

from GINCCO_lib.modules.interpolate_to_t import interpolate_to_t as _interpolate_to_t


def interpolate_to_t(A, *, stagger, mask_t):
    return _interpolate_to_t(A, stagger=stagger, mask_t=mask_t)[0]
