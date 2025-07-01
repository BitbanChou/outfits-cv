# your_app/management/commands/import_images.py
import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import ClothingItem
from PIL import Image
import imagehash
import cv2
import numpy as np
from collections import Counter

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def most_common_color(pixels):
    counts = Counter(map(tuple, pixels))
    return counts.most_common(1)[0][0]

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

class Command(BaseCommand):
    help = 'Import clothing images from a directory into the database'

    def handle(self, *args, **kwargs):
        image_dir = os.path.join(settings.MEDIA_ROOT, 'clothing_images')
        if not os.path.exists(image_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {image_dir}'))
            return

        files = sorted(os.listdir(image_dir))
        user = User.objects.first()  # 或者指定某个用户
        count = 0

        for filename in files:
            match = re.match(r'^([a-zA-Z]+)\s*$(\d+)$', filename)
            if not match:
                continue  # 跳过不符合命名规则的文件

            category_prefix = match.group(1).lower()
            if category_prefix not in dict(ClothingItem.CATEGORY_CHOICES).keys():
                continue  # 跳过不合法分类

            image_path = os.path.join('clothing_images', filename)

            # 创建记录
            cloth = ClothingItem(
                user=user,
                image=image_path,
                category=category_prefix
            )
            cloth.save()

            # 获取颜色
            full_image_path = os.path.join(settings.MEDIA_ROOT, 'clothing_images', filename)
            cloth.color_hex = get_clothing_dominant_color(full_image_path)
            cloth.save(update_fields=['color_hex'])

            count += 1
            self.stdout.write(self.style.SUCCESS(f'Imported: {filename}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} items.'))