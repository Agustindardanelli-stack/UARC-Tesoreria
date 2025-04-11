import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

def get_resource_path(relative_path):
    """ Obtener ruta de recursos para PyInstaller """
    try:
        # PyInstaller crea un directorio temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_logo(logo_label, logo_filename, width, height):
    """Cargar y escalar logo desde assets"""
    # Asumiendo que logo_filename ya viene con la extensión correcta (.png)
    logo_path = get_resource_path(os.path.join("assets", logo_filename))
    
    if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
    else:
        print(f"Logo no encontrado en: {logo_path}")