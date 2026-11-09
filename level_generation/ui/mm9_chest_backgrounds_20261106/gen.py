#!/usr/bin/env python3
"""Generate MM9 chest-screen backgrounds through codex exec image workers (README.md). Usage: gen.py NAME VERSION"""
import subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
PROMPTS = {
    'mm9_chest': (
        "Straight top-down view into an open Norse treasure chest, used as the item-grid background of a classic "
        "Might and Magic style RPG inventory screen. Follow the FIRST attached image exactly for layout and "
        "proportions: the light grey EMPTY FLOOR rectangle is the inside bottom of the chest and must fill exactly "
        "that rectangle: dark weathered oak planks, evenly and softly lit, completely plain and empty, nothing lying "
        "on it, no straps, rivets, carvings or shadows crossing it, so items placed on it stay readable. The brown "
        "RIM band around it is the chest's thick top edge and its inner walls seen from above: dark oak with "
        "blackened iron bands, rivets and Norse knotwork at the corners. The right-hand OPEN LID panel is the inside "
        "of the opened lid lying flat, dark oak with iron hinges and bands. The thin black margin at the top-left "
        "stays deep shadow. Match the materials, palette, detail and mood of the SECOND attached image (a dark "
        "iron-bound oak chest). No text, no labels, no items, no coins, no UI, no grid lines. Landscape, 4:3."),
    'mm9_treasure_bag': (
        "Straight top-down view into a wide open leather treasure bag, used as the item-grid background of a "
        "classic Might and Magic style RPG inventory screen. Follow the FIRST attached image exactly for layout and "
        "proportions: the light grey EMPTY INSIDE rectangle is the bag's flat inner bottom and must fill exactly "
        "that rectangle: dark soft worn leather, evenly and softly lit, completely plain and empty, nothing lying on "
        "it, no folds, cords or coins crossing it, so items placed on it stay readable. The brown RIM band around it "
        "is the bag's rolled leather opening with stitching and a braided drawstring. The right-hand BAG SIDE panel "
        "is the outside of the bag folded back, worn leather with a few coins and a knot of the drawstring. Match the "
        "materials, palette, detail and mood of the SECOND attached image (a dark leather bag). No text, no labels, "
        "no items on the inside, no UI, no grid lines. Landscape, 4:3."),
}
WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using both attached images as reference images and the IMAGE PROMPT below.
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""

name, version = sys.argv[1], sys.argv[2]
target = W / 'raw' / f'{name}_v{version}.png'
prompt = PROMPTS[name]
(W / 'prompts' / f'{name}_v{version}.txt').write_text(prompt + '\n')
with open(W / 'raw' / f'{name}_v{version}.log', 'w') as log:
    subprocess.run(['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(W), '--skip-git-repo-check',
                    '-i', str(W / 'refs' / f'{name}_layout.png'), '-i', str(W / 'refs' / f'{name}_style.png')],
                   input=WORKER.format(prompt=prompt, target=target), text=True, stdout=log,
                   stderr=subprocess.STDOUT, timeout=900)
print(target, target.exists())
