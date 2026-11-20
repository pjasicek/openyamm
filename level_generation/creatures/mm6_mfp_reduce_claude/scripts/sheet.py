"""Contact sheet of close renders: rows = tags, columns = front/q34/side. Usage: sheet.py <spot> <tag> [tag ...]"""
import sys
from PIL import Image, ImageDraw
spot, tags = sys.argv[1], sys.argv[2:]; S = 420
s = Image.new('RGB', (3 * S, len(tags) * S))
for j, t in enumerate(tags):
    for i, v in enumerate(['front', 'q34', 'side']):
        s.paste(Image.open(f'review/close/{t}_{spot}_{v}.png').convert('RGB').resize((S, S)), (i * S, j * S))
    ImageDraw.Draw(s).text((8, j * S + 8), t, fill=(255, 255, 0))
s.save(f'review/close/sheet_{spot}_{"_".join(tags)}.png'); print(f'review/close/sheet_{spot}_{"_".join(tags)}.png')
