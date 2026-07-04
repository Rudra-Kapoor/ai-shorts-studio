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

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        return None

    centers = []
    for p in frame_paths:
        img = cv2.imread(p)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                           minSize=(40, 40))
        if len(faces) == 0:
            continue
        # Use the largest face in the frame.
        fx, fy, fw, fh = max(faces, key=lambda b: b[2] * b[3])
        centers.append((fx + fw / 2) / float(w))

    if not centers:
        return None
    return float(median(centers))
