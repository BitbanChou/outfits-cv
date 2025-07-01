import os
import cv2
import numpy as np
from PIL import Image
from collections import Counter

# --> Helpers

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def most_common_color(pixels):
    counts = Counter(map(tuple, pixels))
    return counts.most_common(1)[0][0]

def average_color(pixels):
    avg = pixels.mean(axis=0).astype(int)
    return tuple(avg)

# --> Face detection + dominant color

# load the cascade once at import time
_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def get_face_dominant_color(image_path, thumb_size=(100, 100)):
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    if len(faces) == 0:
        # fallback to whole image average
        pixels = np.array(
            Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        ).reshape(-1, 3)
        return rgb_to_hex(average_color(pixels))

    # Get the largest face
    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])

    # Focus on center part of face (avoid hair/edges)
    margin_w = int(w * 0.2)
    margin_h = int(h * 0.3)
    cx, cy = x + margin_w, y + margin_h
    cw, ch = w - 2 * margin_w, h - 2 * margin_h
    face_crop = img_bgr[cy:cy+ch, cx:cx+cw]

    # Convert to RGB and resize
    face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(face_rgb).resize(thumb_size)
    arr = np.array(pil_img).reshape(-1, 3)

    # Optional: filter likely skin colors (simple rule-based in RGB)
    skin_pixels = [tuple(px) for px in arr if 45 < px[0] < 255 and 30 < px[1] < 220 and 20 < px[2] < 200]
    if not skin_pixels:
        skin_pixels = arr.tolist()  # fallback

    dominant = most_common_color(skin_pixels)
    return rgb_to_hex(dominant)

# --> GrabCut segmentation + dominant color for clothing

def get_clothing_dominant_color(image_path, thumb_size=(100,100)):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    # init mask & models
    mask     = np.zeros((h, w), np.uint8)
    bgdModel = np.zeros((1,65), np.float64)
    fgdModel = np.zeros((1,65), np.float64)

    # rectangle: skip 10% border
    rect = (int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))
    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

    # 0,2 = background; 1,3 = foreground
    fg_mask = np.where((mask==1)|(mask==3), 1, 0).astype('uint8')
    fg = img * fg_mask[:,:,None]

    fg_rgb = cv2.cvtColor(fg, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(fg_rgb).resize(thumb_size)
    arr = np.array(pil).reshape(-1,3)

    # drop pure-black pixels (background)
    arr = arr[np.any(arr!=[0,0,0], axis=1)]
    if arr.size == 0:
        # fallback: average over full image
        arr = np.array(
            Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ).reshape(-1,3)

    dom = most_common_color(arr)
    return rgb_to_hex(dom)

# --> For match clothing

def hue_distance(h1, h2):
    """Return the shortest distance between two hues (0–360)."""
    return min(abs(h1 - h2), 360 - abs(h1 - h2))


def is_complementary(h1, h2, tolerance=10):
    """Complementary: hues ≈180° apart."""
    return abs(hue_distance((h1 + 180) % 360, h2)) <= tolerance


def is_analogous(h1, h2, tolerance=30):
    """Analogous: hues within ±30° on the wheel."""
    return hue_distance(h1, h2) <= tolerance


def is_triadic(h1, h2, tolerance=20):
    """Triadic: hues ≈120° or ≈240° apart."""
    return any(
        abs(hue_distance((h1 + offset) % 360, h2)) <= tolerance
        for offset in (120, 240)
    )


def is_monochromatic(h1, h2, s1, s2, l1, l2, hue_tol=10, sl_tol=15):
    """Monochromatic: same hue ±hue_tol, similar sat/lightness."""
    return (
        hue_distance(h1, h2) <= hue_tol and
        abs(s1 - s2) <= sl_tol and
        abs(l1 - l2) <= sl_tol
    )


def get_clothing_based_on_skin_tone(skin_tone, clothing_queryset, strategy=None):
    if not skin_tone.color_hex:
        return {'message': False, 'error': 'No skin tone color found.'}

    if not clothing_queryset:
        return {'message': False, 'error': 'No clothing items found.'}
    
    if not strategy:
        return {'message': False, 'error': 'No strategy provided.'}

    h1, s1, l1 = skin_tone.hex_to_hsl()

    # Categorize items
    accessories = []
    tops = []
    legs = []
    feet = []

    for item in clothing_queryset:
        h2, s2, l2 = item.hex_to_hsl()

        match = False
        if strategy == 'complementary':
            match = is_complementary(h1, h2)
        elif strategy == 'analogous':
            match = is_analogous(h1, h2)
        elif strategy == 'triadic':
            match = is_triadic(h1, h2)
        elif strategy == 'monochromatic':
            match = is_monochromatic(h1, h2, s1, s2, l1, l2)

        if match:
            if item.category == 'accessory':
                accessories.append(item)
            elif item.category == 'top':
                tops.append(item)
            elif item.category == 'legs':
                legs.append(item)
            elif item.category == 'feet':
                feet.append(item)

    # dict of lists
    categorized_items = {
        'message': True,
        'accessories': accessories,
        'tops': tops,
        'legs': legs,
        'feet': feet,
        'skin_tone': skin_tone.color_hex,
    }

    return categorized_items
