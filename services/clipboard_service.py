import pyautogui
import pyperclip
from PIL import Image, ImageGrab


def copy_selection_and_get_text(copy_delay=0.3):
    pyautogui.hotkey("ctrl", "c")
    import time

    time.sleep(copy_delay)
    return pyperclip.paste()


def get_clipboard_image_hash():
    try:
        clip = ImageGrab.grabclipboard()
        if isinstance(clip, Image.Image):
            img = clip.convert("RGB")
            return hash(img.tobytes())
    except Exception:
        pass
    return None


def get_new_clipboard_image(last_hash=None):
    try:
        clip = ImageGrab.grabclipboard()
    except Exception:
        return None, last_hash

    if not isinstance(clip, Image.Image):
        return None, last_hash

    image = clip.convert("RGB")
    current_hash = hash(image.tobytes())
    if current_hash == last_hash:
        return None, last_hash
    return image, current_hash
