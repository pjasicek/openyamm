"""Prepare the AI bank detail with the accepted material quilting convention."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('material_seams', P.parents[3] / 'seam_repair/build.py')
seams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)
a = np.asarray(Image.open(P / 'generated.png').convert('RGB').resize((512, 512), Image.Resampling.LANCZOS), float)
a = seams.periodic(a)
# The native bank has finer, less saturated gravel than the inland cracked earth.
# Fit this separate bank detail layer at twice the frequency; never rescale the accepted master.
b = np.asarray(Image.fromarray(np.uint8(np.clip(np.rint(a), 0, 255))).resize((256, 256), Image.Resampling.LANCZOS), float)
b = np.tile(b, (2, 2, 1))
luma = b @ np.array([.2126, .7152, .0722])
b = .60 * b + .40 * luma[:, :, None]
Image.fromarray(np.uint8(np.clip(np.rint(b), 0, 255))).save(P / 'periodic.png')
