# need to install this for run
#pip install imageio[ffmpeg] imageio[pyav] pillow

import os
import glob
import numpy as np
import imageio.v3 as iio
from PIL import Image

def _ensure_even_hw(arr):
    """Pad last row/col if H or W is odd to keep encoders happy."""
    h, w = arr.shape[:2]
    pad_h = 1 if h % 2 else 0
    pad_w = 1 if w % 2 else 0
    if pad_h or pad_w:
        # pad using edge values
        arr = np.pad(arr, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
    return arr

def pngs_to_video(inputs, output_path, fps=24, resize_to=None):
    """
    Convert a sequence of PNG images into an MP4 video using ``imageio`` with the PyAV plugin.

    This function reads a list or folder of PNG images, ensures that each frame
    is RGB (uint8), contiguous in memory, and has even pixel dimensions, then
    encodes them into an H.264 MP4 video file. Optionally, images can be resized
    before encoding. It provides a fully pure-Python workflow using ``imageio`` and
    ``Pillow``.

    Parameters
    ----------
    inputs : str or list of str
        Either:
          * a directory path containing PNG files,
          * a glob pattern (e.g., ``"./frames/*.png"``), or
          * an explicit list of file paths.
    output_path : str
        Path to the output video file (e.g., ``"./output.mp4"``).
    fps : int, optional
        Frames per second of the output video. Default is 24.
    resize_to : tuple of int, optional
        Target video frame size ``(width, height)`` in pixels.  
        If ``None``, uses the size of the first image. Default is ``None``.

    Returns
    -------
    None
        The video is written directly to ``output_path``.

    Notes
    -----
    - The output codec is **H.264** (requires ``pyav`` plugin in ``imageio``).
    - Any unreadable or malformed image will raise a ``RuntimeError``.

    Examples
    --------
    >>> pngs_to_video("./frames/*.png", "movie.mp4", fps=30)
    >>> pngs_to_video(["frame1.png", "frame2.png", "frame3.png"], "out.mp4", resize_to=(1280, 720))
    """

    try:
        import imageio.v3 as iio
        from PIL import Image

    except ImportError as e:
        raise ImportError(
            "This function requires additional library "
            "Please install it with `pip install imageio[ffmpeg] imageio[pyav] pillow`."
        ) from e

    # Collect files
    if isinstance(inputs, str):
        files = glob.glob(inputs) if not os.path.isdir(inputs) else glob.glob(os.path.join(inputs, "*.png"))
    else:
        files = list(inputs)

    if not files:
        raise ValueError("No PNG files found")
    files.sort()

    # Target size from first image or resize_to
    with Image.open(files[0]) as im0:
        w, h = (resize_to if resize_to is not None else im0.size)

    try:
        with iio.imopen(output_path, "w", plugin="pyav") as writer:
            writer.init_video_stream(fps=fps, codec="h264")

            for idx, path in enumerate(files):
                try:
                    im = Image.open(path).convert("RGB")
                except Exception as e:
                    raise RuntimeError(f"Failed to open image: {path} ({e})")

                if im.size != (w, h):
                    im = im.resize((w, h), Image.LANCZOS)

                frame = np.asarray(im)
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8, copy=False)

                # ensure 3-channel RGB
                if frame.ndim != 3 or frame.shape[2] != 3:
                    raise RuntimeError(f"Unexpected frame shape for {path}: {frame.shape}")

                # contiguous memory
                frame = np.ascontiguousarray(frame)

                # even H, W
                frame = _ensure_even_hw(frame)

                # final guard
                if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
                    raise RuntimeError(f"Incompatible frame for {path}: dtype={frame.dtype}, shape={frame.shape}")

                writer.write_frame(frame)

    except Exception as e:
        # Add more context
        raise RuntimeError(f"Failed to write video: {e}")


