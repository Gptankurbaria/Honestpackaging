
import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
        # If this utility is in 'modules/', go up one level
        if os.path.basename(base_path) == "modules":
            base_path = os.path.dirname(base_path)

    return os.path.join(base_path, relative_path)
