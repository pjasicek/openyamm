"""Measures the dark seal recess of certificate paintings: the dark region flood-filled from a seed near the top centre
(the first dark pixel down the centre line below the frame), with its bounding box centre and radius.
Usage: python3 -I measure_recess.py <png> [...]"""
import sys
from collections import deque
from PIL import Image

DARK = 60

for path in sys.argv[1:]:
    image = Image.open(path).convert('L')
    width, height = image.size
    pixels = image.load()
    seed = next((768, y) for y in range(90, 300) if pixels[768, y] < DARK)
    seen = {seed}
    queue = deque([seed])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in seen and 0 <= nx < width and 70 <= ny < 320 and pixels[nx, ny] < DARK:
                seen.add((nx, ny))
                queue.append((nx, ny))
    xs = [x for x, _ in seen]
    ys = [y for _, y in seen]
    print(f'{path}: centre ({(min(xs) + max(xs)) / 2:.0f}, {(min(ys) + max(ys)) / 2:.0f}) '
          f'radius {(max(xs) - min(xs)) / 2:.0f} x {(max(ys) - min(ys)) / 2:.0f} pixels {len(seen)}')
