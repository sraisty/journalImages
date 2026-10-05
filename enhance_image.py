import cv2
import numpy as np


def enhance_image(args):
    src, dst, gamma, quality = args
    if dst.exists():
        return dst
    img = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"SKIP (unreadable): {src}")
        return None
    h, w = img.shape

    # Estimate paper background on a downscaled copy: dilation removes ink, blur smooths it.
    small = cv2.resize(
        img, (max(1, w // 8), max(1, h // 8)), interpolation=cv2.INTER_AREA
    )
    bg = cv2.dilate(small, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    bg = cv2.GaussianBlur(bg, (0, 0), 10)
    bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_LINEAR)

    # Flatten lighting/yellowing: paper -> ~white, ink stays darker.
    norm = cv2.divide(img, np.maximum(bg, 1), scale=255).astype(np.float32)

    # Per-image levels: darkest ink -> black, typical paper -> white.
    lo = np.percentile(norm, 0.5)
    hi = np.percentile(norm, 60)
    out = (
        np.clip((norm - lo) / max(hi - lo, 1), 0, 1) ** gamma
    )  # gamma > 1 darkens midtones
    out = (out * 255).astype(np.uint8)

    if dst.suffix.lower() in (".jpg", ".jpeg"):
        cv2.imwrite(str(dst), out, [cv2.IMWRITE_JPEG_QUALITY, quality])
    else:
        cv2.imwrite(str(dst), out)
    return dst
