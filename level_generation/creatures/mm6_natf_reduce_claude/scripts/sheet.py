"""Contact sheets of close renders: rows = tags, columns = front/q34/side. Usage: sheet.py <name> <tag> [tag ...]"""
import sys
from PIL import Image
name, tags = sys.argv[1], sys.argv[2:]
for spot in ['whole', 'head', 'hand']:
    s = Image.new('RGB', (3 * 400, len(tags) * 400))
    for i, v in enumerate(['front', 'q34', 'side']):
        for j, t in enumerate(tags):
            s.paste(Image.open(f'review/close/{t}_{spot}_{v}.png').convert('RGB').resize((400, 400)), (i * 400, j * 400))
    s.save(f'review/close/{name}_{spot}.png')
