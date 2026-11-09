"""Meshy's 4K colour, padded into the gutters, then the same gentle grade as the 2K route."""
import subprocess, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
Image.open('meshy/zombie_body_retex/texture_urls_0_base_color.png').convert('RGB').save('textures/zombie4k_basecolor.png')
