"""Pass 7: contact sheet of review/newhead/_v_<head|neck>_<view>.png. Args: <out png>"""
import sys, glob
from PIL import Image
fs = sorted(glob.glob('review/newhead/_v_head_*.png')) + sorted(glob.glob('review/newhead/_v_neck_*.png'))
W = Image.new('RGB', (600 * 5, 600 * ((len(fs) + 4) // 5)), (40, 40, 40))
for i, f in enumerate(fs): W.paste(Image.open(f).convert('RGB'), ((i % 5) * 600, (i // 5) * 600))
W.save(sys.argv[1]); print(sys.argv[1], len(fs))
