# Renders the Progress journal tab emblem (the approved study's red shield with a rising gold line) at the size of the
# other journal tab icons, in their painted brass-and-enamel style.
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 1254
K = 2  # supersampling
W = S * K
out = sys.argv[1]

def shield_path(inset):
    # A heater shield: flat-ish top with a slight dip, straight sides curving to a point.
    pts = []
    left, right, top, bottom = 250 + inset, 1004 - inset, 200 + inset, 1090 - inset
    cx = (left + right) / 2
    n = 80
    # top edge, gently curved down in the middle
    for i in range(n + 1):
        t = i / n
        x = left + (right - left) * t
        y = top + 22 * math.sin(math.pi * t)
        pts.append((x, y))
    # right side down to the point
    for i in range(1, n + 1):
        t = i / n
        y = top + (bottom - top) * t
        k = max(0.0, (t - 0.42) / 0.58)
        x = right - (right - cx) * (k ** 1.6)
        pts.append((x, y))
    for i in range(n - 1, 0, -1):
        t = i / n
        y = top + (bottom - top) * t
        k = max(0.0, (t - 0.42) / 0.58)
        x = left + (cx - left) * (k ** 1.6)
        pts.append((x, y))
    return [(x * K, y * K) for x, y in pts]

def mask(poly):
    m = Image.new('L', (W, W), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return m

def vgradient(top, bottom):
    g = Image.new('RGB', (1, W))
    for y in range(W):
        t = y / (W - 1)
        g.putpixel((0, y), tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)))
    return g.resize((W, W))

def radial(center, inner, outer, radius):
    g = Image.new('RGB', (W, W))
    px = g.load()
    cx, cy = center
    step = 4
    small = Image.new('RGB', (W // step, W // step))
    sp = small.load()
    for y in range(W // step):
        for x in range(W // step):
            d = min(1.0, math.hypot(x * step - cx, y * step - cy) / radius)
            sp[x, y] = tuple(int(inner[c] + (outer[c] - inner[c]) * d) for c in range(3))
    return small.resize((W, W), Image.BILINEAR)

random.seed(7)
noise = Image.effect_noise((W // 8, W // 8), 40).resize((W, W), Image.BICUBIC)

outer = mask(shield_path(0))
rim_inner = mask(shield_path(46))
enamel = mask(shield_path(62))

img = Image.new('RGBA', (W, W), (0, 0, 0, 0))

# Drop shadow.
shadow = outer.filter(ImageFilter.GaussianBlur(28 * K))
shadow_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
shadow_layer.putalpha(shadow.point(lambda v: int(v * 0.65)))
img.alpha_composite(shadow_layer, (14 * K, 24 * K))

# Brass rim: a vertical gradient, light at the top, with a bevel highlight.
brass = vgradient((246, 222, 160), (122, 86, 38))
brass = ImageChops.multiply(brass, Image.merge('RGB', [noise.point(lambda v: 200 + v // 5)] * 3))
rim = Image.new('RGBA', (W, W), (0, 0, 0, 0))
rim.paste(brass, (0, 0), outer)
img.alpha_composite(rim)
# Rim bevel: a light inner edge and a dark outer line.
edge = ImageChops.subtract(outer, outer.filter(ImageFilter.MinFilter(9)))
dark = Image.new('RGBA', (W, W), (40, 26, 10, 255)); dark.putalpha(edge)
img.alpha_composite(dark)
inner_edge = ImageChops.subtract(rim_inner.filter(ImageFilter.MaxFilter(9)), rim_inner)
light = Image.new('RGBA', (W, W), (255, 240, 200, 200)); light.putalpha(inner_edge.point(lambda v: v * 3 // 4))
img.alpha_composite(light)
# The dark channel between rim and enamel.
channel = Image.new('RGBA', (W, W), (34, 18, 12, 255)); channel.putalpha(rim_inner)
img.alpha_composite(channel)

# Red enamel: a radial gradient lit from the upper left, with a fine grain.
red = radial((560 * K, 430 * K), (176, 44, 36), (62, 12, 10), 760 * K)
red = ImageChops.multiply(red, Image.merge('RGB', [noise.point(lambda v: 190 + v // 4)] * 3))
enamel_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
enamel_layer.paste(red, (0, 0), enamel)
img.alpha_composite(enamel_layer)
# A soft gloss over the upper left of the enamel.
gloss = Image.new('L', (W, W), 0)
ImageDraw.Draw(gloss).ellipse((330 * K, 250 * K, 760 * K, 560 * K), fill=70)
gloss = ImageChops.multiply(gloss.filter(ImageFilter.GaussianBlur(60 * K)), enamel)
gl = Image.new('RGBA', (W, W), (255, 210, 190, 255)); gl.putalpha(gloss)
img.alpha_composite(gl)

# The rising line: gold, with a dark outline and a bevel, ending in a gold dot.
line = [(390, 820), (520, 650), (630, 760), (830, 470)]
line = [(x * K, y * K) for x, y in line]
def stroke(width, color, offset=(0, 0)):
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = [(x + offset[0], y + offset[1]) for x, y in line]
    d.line(pts, fill=color, width=width, joint='curve')
    for x, y in pts:
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)
    return layer
img.alpha_composite(stroke(96 * K, (20, 10, 4, 150), (10 * K, 16 * K)).filter(ImageFilter.GaussianBlur(10 * K)))
img.alpha_composite(stroke(96 * K, (58, 36, 12, 255)))
gold_mask = stroke(74 * K, (255, 255, 255, 255)).getchannel('A')
gold = vgradient((255, 236, 170), (168, 118, 46))
gold = ImageChops.multiply(gold, Image.merge('RGB', [noise.point(lambda v: 210 + v // 5)] * 3))
gl = Image.new('RGBA', (W, W), (0, 0, 0, 0)); gl.paste(gold, (0, 0), gold_mask)
img.alpha_composite(gl)
hi = stroke(22 * K, (255, 248, 214, 170), (-12 * K, -14 * K)).filter(ImageFilter.GaussianBlur(4 * K))
hi.putalpha(ImageChops.multiply(hi.getchannel('A'), gold_mask))
img.alpha_composite(hi)
# The dot at the peak.
x, y = 900 * K, 360 * K
r = 62 * K
d = ImageDraw.Draw(img)
d.ellipse((x - r - 12 * K, y - r - 12 * K, x + r + 12 * K, y + r + 12 * K), fill=(58, 36, 12, 255))
dot = Image.new('L', (W, W), 0)
ImageDraw.Draw(dot).ellipse((x - r, y - r, x + r, y + r), fill=255)
dl = Image.new('RGBA', (W, W), (0, 0, 0, 0)); dl.paste(radial((x - 20 * K, y - 24 * K), (255, 244, 200), (176, 124, 50), r * 1.3), (0, 0), dot)
img.alpha_composite(dl)

# Rivets along the rim.
def rivet(x, y, r):
    x, y, r = x * K, y * K, r * K
    d = ImageDraw.Draw(img)
    d.ellipse((x - r - 4 * K, y - r - 4 * K, x + r + 4 * K, y + r + 4 * K), fill=(48, 30, 10, 255))
    m = Image.new('L', (W, W), 0)
    ImageDraw.Draw(m).ellipse((x - r, y - r, x + r, y + r), fill=255)
    l = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    l.paste(radial((x - r * 0.35, y - r * 0.4), (255, 246, 210), (130, 92, 40), r * 1.4), (0, 0), m)
    img.alpha_composite(l)
for x, y in [(273, 225), (981, 225), (627, 245), (273, 560), (981, 560), (420, 880), (834, 880)]:
    rivet(x, y, 17)
# Shade the lower part of the whole emblem, as the painted icons are lit from above.
shade = Image.new('L', (W, W), 0)
sp = Image.new('L', (1, W))
for y in range(W):
    sp.putpixel((0, y), int(max(0, (y / W - 0.45) / 0.55) * 120))
shade = ImageChops.multiply(sp.resize((W, W)), img.getchannel('A'))
sl = Image.new('RGBA', (W, W), (10, 4, 2, 255)); sl.putalpha(shade)
img.alpha_composite(sl)
img = img.resize((S, S), Image.LANCZOS)
img.save(out)
