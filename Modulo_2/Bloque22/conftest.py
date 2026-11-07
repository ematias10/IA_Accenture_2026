import sys
from pathlib import Path

# Asegurar que el directorio de Bloque22 esté en sys.path para ejecutar tests desde cualquier ubicación
bloque22_dir = str(Path(__file__).resolve().parent)
if bloque22_dir not in sys.path:
    sys.path.insert(0, bloque22_dir)

