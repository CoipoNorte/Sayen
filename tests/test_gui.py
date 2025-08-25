"""
Test simple de la GUI.
"""
import sys
import os

# Asegura que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.gui import SayenGUI


def main():
    print("Iniciando GUI...")
    app = SayenGUI()
    app.mainloop()
    print("GUI cerrada.")


if __name__ == "__main__":
    main()