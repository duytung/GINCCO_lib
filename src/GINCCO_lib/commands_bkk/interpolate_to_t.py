import numpy as np

def interpolate_to_t(A, *, stagger: str, mask_t: np.ndarray):
    """
    Interpolate a staggered (U or V) field onto T grid.
    Only 2D arrays are supported.
    """
    A = np.asarray(A)
    mask_t = np.asarray(mask_t, dtype=bool)

    if A.ndim != 2:
        raise ValueError("A must be 2D")

    ny_t, nx_t = mask_t.shape

    if stagger.lower() == "u":
        # U-grid: same ny, nx_t-1
        if A.shape != (ny_t, nx_t - 1):
            raise ValueError(f"U grid shape mismatch: expected ({ny_t},{nx_t-1}), got {A.shape}")
        T = np.full((ny_t, nx_t), np.nan)
        T[:, 1:-1] = 0.5 * (A[:, :-1] + A[:, 1:])
        T[:, 0] = A[:, 0]
        T[:, -1] = A[:, -1]

    elif stagger.lower() == "v":
        # V-grid: ny_t-1, nx
        if A.shape != (ny_t - 1, nx_t):
            raise ValueError(f"V grid shape mismatch: expected ({ny_t-1},{nx_t}), got {A.shape}")
        T = np.full((ny_t, nx_t), np.nan)
        T[1:-1, :] = 0.5 * (A[:-1, :] + A[1:, :])
        T[0, :] = A[0, :]
        T[-1, :] = A[-1, :]

    else:
        raise ValueError("stagger must be 'u' or 'v'")

    # Apply mask (0 = land)
    T[mask_t == 0] = np.nan
    return T
