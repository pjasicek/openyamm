#!/usr/bin/env python3
"""Step 2 of the held-sword retexture pilot (README.md): Codex HD masters for the Meshy retexture, one session per
sword, painted over the exact silhouettes of the upload (prep.py guides).

  python3 -I codex_masters.py brief <icon>     writes work/<icon>/references_hd/ (icon_x8.png, guides, CODEX_BRIEF.md)
  python3 -I codex_masters.py run <icon>       runs one Codex image session on it (prompt on stdin)
"""
import os
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2')

COMMON = ("Real sword detail, readable at arm's length in a first-person game: polished, bevelled cutting edges "
          "(a narrow bright honed band along each edge, clearly separate from the satin flat of the blade), fine "
          "lengthwise grinding grain on the flats, light honest wear (a few tiny nicks on the edge, faint scratches, "
          "slightly darker steel near the guard), and visible variation of polish along the blade. Crisp chamfers "
          "and forged edges on the guard, worn highlights on its high points, darker recesses. A grip with clear "
          "tactile texture. Metal must read as metal everywhere.")

SWORDS = {
    'item001': ('Iron Longsword (the knight\'s starting sword)',
                'A straight, double-edged iron longsword. The blade is plain forged iron/steel, a cool grey with a '
                'faint warm patina (the icon shows a weathered grey-tan blade with small nicks), with a raised '
                'central ridge running from the guard to the point. Bronze crossguard with down-turned hooked '
                'ends, brown leather-wrapped grip with thin bronze bands, round bronze pommel.'),
    '7item010': ('Steel Broadsword',
                 'A broad, heavy single-edged steel blade (machete-like, the back edge has a clipped, notched '
                 'section near the tip) of bright polished steel with a fuller-like shallow groove along the spine '
                 'side. Steel crossguard with curled ends, dark leather grip with steel bands, steel pommel.'),
    'item005': ("Champion's Sword",
                'A straight, double-edged sword of bright, highly polished steel with a strong central ridge and '
                'a short fuller near the guard. Ornate gold crossguard shaped as swept wings with engraved feather '
                'detail, red leather grip wrapped with gold wire, gold pommel.'),
    '7item012': ('Cutlass',
                 'A curved, single-edged steel cutlass blade, polished steel with a sharp bevelled edge on the '
                 'curved side and a flat spine. Steel guard with a round knuckle bow, a dark grip wrapped with cord '
                 'and steel ferrules, round steel pommel cap.'),
}


def brief(icon):
    title, identity = SWORDS[icon]
    work = os.path.join(PROJECT, 'work', icon)
    folder = os.path.join(work, 'references_hd')
    os.makedirs(folder, exist_ok=True)
    image = Image.open(os.path.join(ICONS, icon + '.png')).convert('RGBA')
    image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
    canvas = Image.new('RGBA', (image.width + 160, image.height + 160), (255, 0, 255, 255))
    canvas.alpha_composite(image, (80, 80))
    canvas.convert('RGB').save(os.path.join(folder, 'icon_x8.png'))
    for view in ('front', 'back', 'left', 'right'):
        shutil.copy(os.path.join(work, f'guide_{view}.png'), os.path.join(folder, f'guide_{view}.png'))
    rel = os.path.relpath(folder, REPO)
    text = f"""# Codex brief: HD texture references for the 3D sword "{title}" (icon {icon})

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds, do not call
Meshy.

Use your built-in image generation tool. Attached inputs (all in this folder):
- `icon_x8.png`: the restored inventory icon, enlarged (magenta is background). It is the authority for the design,
  colours and materials.
- `guide_front.png`, `guide_back.png`, `guide_left.png`, `guide_right.png`: plain grey orthographic renders of the
  EXACT 3D model, standing upright with the point at the top, from the front (blade face), the back (other blade face),
  its left and its right (edge-on: the blade is a thin strip, the guard and grip seen from the side). Each guide fixes
  the silhouette, position, scale and every shape edge of its view.

## Deliverables (1024 x 1536 portrait, transparent background, unresized returns)
- `01_front.png` over `guide_front.png`
- `02_back.png` over `guide_back.png`
- `03_left.png` over `guide_left.png`
- `04_right.png` over `guide_right.png`

Each image must keep its guide's silhouette EXACTLY: same outline, size and position in the frame; nothing added
outside the silhouette, nothing cropped. Paint the sword's real materials onto that shape so that the four views show
one and the same sword.

## Prompt content
TASK CONTEXT: FANTASY-GAME ASSET RESTORATION: a faithful high-definition rendition of the EXISTING Might and Magic
item from the supplied icon, as the texture reference for its 3D model, which a first-person game shows in the hand,
filling a third of the screen. Not a new design.

Identity: {identity}

Detail wanted: {COMMON}

LIGHTING: even, soft, neutral studio light from the viewer, as for a product reference: the metal shows its own
colour and polish (honed edges brighter, flats satin), with only gentle, broad highlights. No sky or scenery
reflected in the blade, no dramatic light, no cast shadows, no rim light, no glow, no background, no floor, no text.

Do NOT: change the design, the colours or the materials of the icon; add gems, runes, engravings or ornaments the icon
does not have (light wear and grain are wanted); paint a different silhouette than the guide; crop.

Checks per image: silhouette identical to its guide; design and colours match the icon; edges, ridge or fuller,
grain and grip texture clearly visible; even light; true transparent background.
Write `generation_runs.json` (view, prompt, inputs with sha256, output, selected, reason). At most one corrective
regeneration per view. If the tool returns another size, keep it unresized and record it.
"""
    with open(os.path.join(folder, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(text)
    print(os.path.join(folder, 'CODEX_BRIEF.md'))


def run(icon):
    folder = os.path.join(PROJECT, 'work', icon, 'references_hd')
    images = [os.path.join(folder, n) for n in ('icon_x8.png', 'guide_front.png', 'guide_back.png', 'guide_left.png',
                                                'guide_right.png')]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for image in images:
        arguments += ['-i', image]
    prompt = (f'Follow the brief in {os.path.relpath(os.path.join(folder, "CODEX_BRIEF.md"), REPO)} exactly. The '
              'attached images are its inputs (named as in the brief, in this order: icon_x8, guide_front, guide_back, '
              'guide_left, guide_right). Produce the images with your built-in image generation tool and save them as '
              'specified.')
    with open(os.path.join(folder, 'codex_run.log'), 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', icon, result.returncode)


if __name__ == '__main__':
    {'brief': brief, 'run': run}[sys.argv[1]](sys.argv[2])
