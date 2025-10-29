import numpy as np

def interpolate_to_t(A, *, stagger: str, mask_t: np.ndarray):
    """
    Interpolate a staggered field (U or V) onto the T grid.

    Parameters
    ----------
    A : ndarray
        Staggered array. Last two dims are (y, x).
        - If stagger='u': shape (..., ny_t, nx_t-1)
        - If stagger='v': shape (..., ny_t-1, nx_t)
    stagger : {'u', 'v'}
        Type of staggering.
    mask_t : ndarray of 0 and 1
        0: land point. Will be considered as nan value

    Returns
    -------
    T : ndarray
        Interpolated values on T grid, shape (..., ny_t, nx_t), masked as NaN where mask_t is True.
    single_src : ndarray (uint8)
        1 where T was computed from exactly one valid neighbor, 0 otherwise.
        (Interior points with two valid neighbors → 0; points with both neighbors NaN → 0.)
    """
    A = np.asarray(A)
    mask_t = np.asarray(mask_t, dtype=bool)
    if A.ndim < 2:
        raise ValueError("A must have at least 2 dims (y, x) at the end.")

    # Infer T-grid size from mask_t
    ny_t, nx_t = mask_t.shape[-2], mask_t.shape[-1]

    # Validate shapes vs stagger
    if stagger.lower() == 'u':
        if A.shape[-2] != ny_t or A.shape[-1] != nx_t - 1:
            raise ValueError(f"U shape {-2, -1} must be (ny_t, nx_t-1) = ({ny_t}, {nx_t-1}), got {A.shape[-2:]}")
        # Prepare output
        T = np.full(A.shape[:-1] + (nx_t,), np.nan, dtype=A.dtype)
        single = np.zeros_like(T, dtype=np.uint8)

        # Interior columns i=1..nx_t-2 use left/right U: u[i-1], u[i]
        if nx_t >= 3:
            left  = A[..., :, 0:-1-0]    # u[0..nx_t-2-1] = u[0..nx_t-3]
            right = A[..., :, 1:      ]  # u[1..nx_t-2]
            # Align to T[..., :, 1:-1]
            both_ok = np.isfinite(left) & np.isfinite(right)
            left_ok = np.isfinite(left) & ~np.isfinite(right)
            right_ok= ~np.isfinite(left) & np.isfinite(right)

            T[..., :, 1:-1] = np.where(
                both_ok, 0.5*(left + right),
                np.where(left_ok, left,
                         np.where(right_ok, right, np.nan))
            )
            single[..., :, 1:-1] = (left_ok | right_ok).astype(np.uint8)

        # Left edge i=0 uses u[0]
        u0 = A[..., :, 0]
        ok0 = np.isfinite(u0)
        T[..., :, 0] = np.where(ok0, u0, np.nan)
        single[..., :, 0] = ok0.astype(np.uint8)  # single source if valid

        # Right edge i=nx_t-1 uses u[-1]
        u_last = A[..., :, -1]
        okL = np.isfinite(u_last)
        T[..., :, -1] = np.where(okL, u_last, np.nan)
        single[..., :, -1] = okL.astype(np.uint8)

    elif stagger.lower() == 'v':
        if A.shape[-2] != ny_t - 1 or A.shape[-1] != nx_t:
            raise ValueError(f"V shape {-2, -1} must be (ny_t-1, nx_t) = ({ny_t-1}, {nx_t}), got {A.shape[-2:]}")
        # Prepare output
        T = np.full(A.shape[:-2] + (ny_t, nx_t), np.nan, dtype=A.dtype)
        single = np.zeros_like(T, dtype=np.uint8)

        # Interior rows j=1..ny_t-2 use bottom/top V: v[j-1], v[j]
        if ny_t >= 3:
            bot = A[..., 0:-1, :]   # v[0..ny_t-2-1]
            top = A[..., 1:  , :]   # v[1..ny_t-2]
            both_ok = np.isfinite(bot) & np.isfinite(top)
            bot_ok  = np.isfinite(bot) & ~np.isfinite(top)
            top_ok  = ~np.isfinite(bot) & np.isfinite(top)

            T[..., 1:-1, :] = np.where(
                both_ok, 0.5*(bot + top),
                np.where(bot_ok, bot,
                         np.where(top_ok, top, np.nan))
            )
            single[..., 1:-1, :] = (bot_ok | top_ok).astype(np.uint8)

        # Bottom edge j=0 uses v[0]
        v0 = A[..., 0, :]
        ok0 = np.isfinite(v0)
        T[..., 0, :] = np.where(ok0, v0, np.nan)
        single[..., 0, :] = ok0.astype(np.uint8)

        # Top edge j=ny_t-1 uses v[-1]
        v_last = A[..., -1, :]
        okL = np.isfinite(v_last)
        T[..., -1, :] = np.where(okL, v_last, np.nan)
        single[..., -1, :] = okL.astype(np.uint8)

    else:
        raise ValueError("stagger must be 'u' or 'v'.")

    # Apply T mask (True → NaN and mark single=0)
    # Broadcast mask_t to leading dims if needed
    if mask_t.shape != T.shape[-2:]:
        # Allow broadcasting for leading dims only; last two must match
        pass
    T = np.where(mask_t == 0, np.nan, T)
    single = np.where(mask_t == 0, 0, single).astype(np.uint8)

    return T, single
