"""Inspect the source figure locally; outputs stay in the ignored cache."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.cache/pdf-deps'))
import pymupdf
root = Path(__file__).resolve().parents[1]
doc = pymupdf.open(r'P:\Projects\Mocho_DGA\2025-2026\1_DASHBOARD\INFORME FINAL - Mocho 2025-2026_V_final.pdf')
page = doc[16]
page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).save(str(root / '.cache/figure2-page.png'))
print(page.get_images(full=True))
