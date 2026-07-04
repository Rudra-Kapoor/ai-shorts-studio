"""Face-aware smart crop (Phase 3, optional).

Given a few sampled frames, find where faces sit horizontally and return that
center as a fraction in [0,1] so the 9:16 crop can follow the speaker instead
of always cropping the middle.

OpenCV is imported lazily and is NOT in the default requirements — if it isn't
installed (lean free-tier image), this returns None and the editor falls back
to a centered crop. To enable: add `opencv-python-headless` to requirements.txt
and set FACE_CROP=1."""
from statistics import median


def face_center_frac(frame_paths) -> "float | None":
    if not frame_paths:
        return None
    try:
        import cv2  # lazy: optional dependency
    except Exception:
        return None
