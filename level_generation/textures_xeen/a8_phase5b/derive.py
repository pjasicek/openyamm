"""A8 session 13: hand finish of xdbosban (run after `xtex.py finish`).
`finish` crops the 2:3 return to the face's 1:2 (losing the banner's gold side borders) and matched it to bannwc-a with
gain 1.77 (the red clipped). Redone: the whole return resized to 512 x 1024 (the banner a little narrowed), gain 1.0
(the return's mean luma 67 against bannwc-a's 80, kept: a red banner in a brazier-lit hall)."""
from pathlib import Path
from PIL import Image
D = Path(__file__).parent
img = Image.open(D / 'raw' / 'xdbosban_v1.png').convert('RGB').resize((512, 1024), Image.LANCZOS)
img.save(D / 'finished' / 'xdbosban.png')
img.resize((256, 512), Image.LANCZOS).save(D / 'finished' / 'xdbosban_x2.png')
img.resize((128, 256), Image.LANCZOS).save(D / 'finished' / 'xdbosban_x1.png')
print('xdbosban', img.size)
