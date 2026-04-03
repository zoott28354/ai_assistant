import io
import time

import mss
from PIL import Image, ImageGrab
from PyQt6.QtCore import QBuffer, QIODevice, QRect, Qt
from PyQt6.QtWidgets import QApplication, QRubberBand, QWidget

from services.capture_service import image_to_png_bytes, normalize_hdr_capture


class SnippingTool(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3)
        self.rubberband = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.screen = QApplication.primaryScreen()
        self.virtual_geometry = self.screen.virtualGeometry()
        self.setGeometry(self.virtual_geometry)
        self.show()

    def mousePressEvent(self, event):
        self.start_pt = event.pos()
        self.rubberband.setGeometry(QRect(self.start_pt, self.start_pt))
        self.rubberband.show()

    def mouseMoveEvent(self, event):
        self.rubberband.setGeometry(QRect(self.start_pt, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        rect = QRect(self.start_pt, event.pos()).normalized()
        self.rubberband.hide()
        self.close()
        if rect.width() <= 5:
            return

        QApplication.processEvents()
        time.sleep(0.2)
        global_top_left = self.mapToGlobal(rect.topLeft())
        global_bottom_right = self.mapToGlobal(rect.bottomRight())
        global_rect = QRect(global_top_left, global_bottom_right).normalized()

        try:
            grabbed = ImageGrab.grab(
                bbox=(
                    global_rect.x(),
                    global_rect.y(),
                    global_rect.x() + global_rect.width(),
                    global_rect.y() + global_rect.height(),
                ),
                all_screens=True,
            )
            if grabbed:
                self.callback(image_to_png_bytes(normalize_hdr_capture(grabbed)), False)
                return
        except Exception:
            pass

        target_screen = QApplication.screenAt(global_rect.center()) or self.screen
        screen_rect = target_screen.geometry()
        local_rect = QRect(
            global_rect.x() - screen_rect.x(),
            global_rect.y() - screen_rect.y(),
            global_rect.width(),
            global_rect.height(),
        )

        pixmap = target_screen.grabWindow(0, local_rect.x(), local_rect.y(), local_rect.width(), local_rect.height())
        if not pixmap.isNull():
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            img = Image.open(io.BytesIO(bytes(buffer.data())))
            self.callback(image_to_png_bytes(normalize_hdr_capture(img)), False)
            return

        with mss.mss() as sct:
            img_data = sct.grab(
                {
                    "top": global_rect.y(),
                    "left": global_rect.x(),
                    "width": global_rect.width(),
                    "height": global_rect.height(),
                }
            )
            img = Image.frombytes("RGB", img_data.size, img_data.bgra, "raw", "BGRX")
            self.callback(image_to_png_bytes(normalize_hdr_capture(img)), False)
