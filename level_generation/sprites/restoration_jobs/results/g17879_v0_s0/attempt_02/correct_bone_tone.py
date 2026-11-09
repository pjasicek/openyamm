from pathlib import Path
from PIL import Image
import numpy as np
import json
p = Path(__file__).resolve().parent
f = p / "a_a0b4715d553b6e81ddff.png"
backup = p / "a_a0b4715d553b6e81ddff.before_bone_tone.png"
if not backup.exists():
    backup.write_bytes(f.read_bytes())
im = np.array(Image.open(backup).convert("RGBA"))
rgb = im[:, :, :3].astype(float)
y = np.arange(im.shape[0])[:, None] / im.shape[0]
# Warm bone pixels occupy the lower cage. Neutral iron is left unchanged.
warm = np.clip((rgb[:, :, 0] - rgb[:, :, 2] - 8) / 24, 0, 1)
region = np.clip((y - 0.44) / 0.04, 0, 1) * np.clip((0.94 - y) / 0.04, 0, 1)
weight = warm * region * (im[:, :, 3] > 0)
luma = rgb @ np.array([0.2126, 0.7152, 0.0722])
muted = luma[:, :, None] + (rgb - luma[:, :, None]) * 0.22
im[:, :, :3] = np.clip(np.rint(rgb * (1-weight[:, :, None]) + muted * weight[:, :, None]),0,255).astype(np.uint8)
Image.fromarray(im).save(f)
(p / "bone_tone.json").write_text(json.dumps({"method":"selective warm bone chroma reduction", "chroma_retained":0.22,"luminance":"preserved","alpha":"unchanged","affected_pixels":int((weight>0).sum())},indent=2)+"\n")
