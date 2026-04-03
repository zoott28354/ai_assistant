import io
import os

from PIL import ImageEnhance, ImageOps, ImageStat


def normalize_hdr_capture(image):
    image = image.convert("RGB")
    luminance = image.convert("L")
    histogram = luminance.histogram()
    total_pixels = sum(histogram) or 1
    bright_ratio = sum(histogram[245:]) / total_pixels
    mean_luma = ImageStat.Stat(luminance).mean[0]
    cumulative = 0
    p90 = 255
    p98 = 255
    for idx, count in enumerate(histogram):
        cumulative += count
        if cumulative >= total_pixels * 0.90 and p90 == 255:
            p90 = idx
        if cumulative >= total_pixels * 0.98:
            p98 = idx
            break

    if mean_luma < 168 and bright_ratio < 0.07 and p98 < 242:
        return image

    severe = mean_luma > 190 or bright_ratio > 0.16 or p98 >= 248
    knee = max(150, min(210, p90 + (10 if severe else 18)))
    compression = 0.28 if severe else 0.42
    gamma = 1.18 if severe else 1.10

    def tone_curve(p):
        v = (p / 255.0) ** gamma
        mapped = int(v * 255)
        if mapped > knee:
            mapped = int(knee + (mapped - knee) * compression)
        if mapped > 245:
            mapped = int(245 + (mapped - 245) * 0.18)
        return max(0, min(255, mapped))

    image = image.point(tone_curve)
    image = ImageEnhance.Brightness(image).enhance(0.84 if severe else 0.92)
    image = ImageEnhance.Contrast(image).enhance(1.08 if severe else 1.04)
    image = ImageEnhance.Color(image).enhance(0.93 if severe else 0.97)
    image = ImageOps.autocontrast(image, cutoff=(0.5, 1.5))
    return image


def image_to_png_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def start_native_screen_snip():
    os.startfile("ms-screenclip:")
