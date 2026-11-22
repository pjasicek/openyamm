#!/usr/bin/env python3
"""Writes prompts/<sheet>.txt from descriptions.yml and sheets.yml (sheet name -> NPC ids in reading order).
Usage: make_prompts.py SHEET [SHEET ...]; only the named sheets, so the prompts of accepted sheets stay as sent."""
import sys
from pathlib import Path
import yaml

W = Path(__file__).resolve().parent
HEAD = """Create ONE image: a sheet of {n} separate character portraits arranged in a grid of {cols} columns and {rows} rows, \
portrait orientation 2:3, large (1024x1536). All cells the same size, each cell a portrait rectangle slightly taller than \
wide; solid pure white gutters about 16 pixels wide between the cells and around the outer edge. Each cell is one complete, \
separate portrait with its own background.

Style: exactly the style of the attached reference sheets, which are real NPC portraits from Might and Magic VII (1999). \
They are simple pre-rendered 3D renders of that era, NOT photographs and NOT detailed paintings: smooth plastic-like \
skin with no pores, stubble texture or fine wrinkles (only a few broad modelled wrinkles on the old), soft Gouraud-style \
shading with a gentle specular sheen, hair as smooth simple modelled shapes, slightly simplified low-detail features with \
large clear eyes, clothes as simple smooth shapes, a dated CG look. Very close crop like the references: the face is \
large and fills about two thirds of the cell width, top of the head touching or just cut by the top edge, chin at about \
three quarters of the height, only the neck, collar and top of the shoulders below. Face turned slightly to one side, \
eyes visible. Soft warm lighting. Behind each head a simple, soft, out-of-focus painted interior or landscape fitting \
the person. Medieval fantasy clothing. Not photo-real, not cartoon, not anime, not a modern digital painting. No text, \
letters, labels, numbers, borders or frames anywhere in the image. The reference sheets show the style, framing and \
lighting only: do not copy their faces, every portrait is a new person.

Portraits in reading order (left to right, top row first):
"""

def main():
    desc = {d['id']: d for d in yaml.safe_load((W / 'descriptions.yml').read_text())}
    sheets = yaml.safe_load((W / 'sheets.yml').read_text())
    for name in sys.argv[1:]:
        sheet = sheets[name]
        ids = sheet['ids']
        cols, rows = sheet.get('grid', [3, 4])
        lines = [f"{i + 1}. {desc[npc]['description']}." for i, npc in enumerate(ids)]
        (W / 'prompts' / f'{name}.txt').write_text(HEAD.format(n=len(ids), cols=cols, rows=rows) + '\n'.join(lines) + '\n')

main()
