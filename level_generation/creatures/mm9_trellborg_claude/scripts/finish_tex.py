#!/usr/bin/env python3
"""Final names: torso from the graded paints, heads from the projections, head ORM flat. Project folder."""
from pathlib import Path
import numpy as np
from PIL import Image
T = Path('textures')
for t in 'abc':
    Image.open(T / f'thrall_head_{t}_raw.png').convert('RGB').save(T / f'thrall_head_{t}_final.png')
Image.fromarray(np.dstack([np.full((64, 64), 255, 'u1'), np.full((64, 64), 190, 'u1'), np.zeros((64, 64), 'u1')])).save(T / 'thrall_head_orm.png')
print('FINISH')
