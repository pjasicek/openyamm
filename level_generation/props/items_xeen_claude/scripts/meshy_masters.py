"""Lane S: HD masters for the seven sculptural quest items that need Meshy Smart Topology (route `meshy` in
classification.json). Per design it writes meshy/<design>/references_hd/design_painting.png (the Xeen icon project's
HD painting keyed and trimmed: the design authority) and CODEX_BRIEF.md (one three-quarter master, the Meshy input,
the 3D ground item playbook's step 3). Then `python3 -I scripts/xitem.py codex meshy/<d>/references_hd/CODEX_BRIEF.md`.
Step 4 (after the masters are reviewed): `request` writes meshy/requests/<design>_st_v1.json, an untextured Smart
Topology job (5 credits) from the master with its alpha made binary (00_three_quarter_meshy.png).
Usage: python3 -I scripts/meshy_masters.py [<design> ...]            (no designs: all seven)
       python3 -I scripts/meshy_masters.py request [<design> ...]"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICONS = os.path.join(REPO, 'level_generation', 'ui', 'xeen_item_icons')
sys.path.insert(0, os.path.join(ICONS, 'scripts'))
from finish import key  # noqa: E402

DOLL = ('a small hand-sewn PLUSH RAG DOLL about 30 cm tall, made of felt and cloth: an oversized round head, a soft '
        'stuffed body with visible running stitches along every seam, stubby rounded arms and legs, round mitten '
        'hands without fingers, embroidered face. It STANDS upright on its own two feet, the feet slightly apart, '
        'flat on one level ground plane; both arms hang a little away from the body so a clear gap of air separates '
        'each arm from the torso')
DESIGNS = {
    'x12349': ('Golden Pegasus Statuette',
               'a small solid GOLD statuette about 25 cm tall: a winged horse (Pegasus) REARING on its hind legs, '
               'forelegs raised and bent, long flowing mane and tail, two large feathered wings raised and spread '
               'back from the shoulders, standing on a low rectangular gold plinth with bevelled edges. Polished '
               'warm gold with darker gold in the recesses, finely sculpted feathers and mane'),
    'x12351': ('Golden Griffin Statuette',
               'a small solid GOLD statuette about 25 cm tall: a griffin SITTING upright like a guardian lion, eagle '
               'head with a hooked beak turned slightly to its right, feathered chest, two large wings folded up '
               'and back along its sides, lion forelegs straight down with taloned feet, lion haunches and tail '
               'curled round the hind feet, on a low rectangular gold plinth with bevelled edges. Polished warm '
               'gold with darker gold in the recesses, finely sculpted feathers'),
    'x12367': ('Might Doll',
               DOLL + '. It is a circus STRONGMAN: brown curly hair, a big black handlebar moustache, rosy cheeks, '
               'a red-and-cream horizontally striped one-piece leotard with shoulder straps, dark lace-up boots; '
               'in both hands, held horizontally in front of the belly, a felt BARBELL: a short yellow-and-red '
               'striped bar with a round navy-blue weight at each end, each weight with a white star'),
    'x12368': ('Speed Doll',
               DOLL + '. Shaggy ginger yarn hair, a smiling embroidered face, a sleeveless GREEN felt tunic with a '
               'thin brown belt, bare cream felt arms and legs, short brown felt boots, each boot with a small '
               'white feathered WING on its outer side (like Hermes)'),
    'x12369': ('Endurance Doll',
               DOLL + '. A grey quilted felt knight: a round grey felt HELMET with a visor of bars over the face '
               'opening (the embroidered smiling face and brown hair visible inside), a grey quilted felt '
               'tunic-armour with stitched plates and darker grey trim, brown felt trousers and boots'),
    'x12370': ('Accuracy Doll',
               DOLL + '. An archer: a brown felt HOOD over brown hair, X-stitched button eyes, a green felt tunic '
               'with a brown belt and buckle, brown boots; a small wooden BOW held in its left hand, upright, '
               'clear of the body, and a brown quiver with three arrows on its back (arrow fletchings above the '
               'right shoulder)'),
    'x12371': ('Lord Xeen Doll',
               DOLL + '. A villain: a frowning embroidered face with heavy dark brows, a black felt crowned HELMET '
               'with tall pointed spikes, black felt armour with spiky shoulder pauldrons, darker stitched plates '
               'and grey stitching, black boots, a long dark RED felt cape lined in black hanging to the ankles '
               'behind it'),
}

BRIEF = """# Codex brief: HD master of the {title} (Xeen quest item, 3D ground model)

Scope: image generation only. Write ONLY into `{folder}/`. Do not edit any other file, do not run builds, do not call
Meshy. Use your built-in image generation tool.

This is a quest item of an MM6-8-style first-person RPG (OpenYAMM's World of Xeen). It will be rebuilt as a small 3D
model lying on the ground. Your image is the single reference a photogrammetry-like image-to-3D service reconstructs
the SHAPE from, so the whole object, its volume and its parts must read clearly.

## Input (attached)

- `design_painting.png`: the approved HD painting of the item (its inventory icon art), on a transparent
  background. This is the design, proportion and colour authority. Keep every part, colour and detail it shows.

## Deliverable

`00_three_quarter.png`: ONE square image (1024x1024 or the tool's square size, unresized), true transparent
background, the whole object inside the frame with at least 60 px of margin on every side, no floor, no ground
shadow, no text.

View: front three-quarter, the object turned about 35 degrees to image RIGHT (we see its front and its LEFT side),
the camera a little above, about 15 degrees down, near-orthographic (little perspective). Even soft neutral studio
light: no dramatic lighting, no rim light, no strong shadows, no reflections of a room.

Object: {identity}.

Do NOT: add a base, stand, plinth or object the painting does not show; change the colours or the costume; crop any
part; merge parts that the painting shows apart (keep clear gaps of air where the description asks); draw a
background, floor, shadow or text.

## Checks before you select it

Same object as the painting (parts, colours, proportions); three-quarter view turned to image right, seen a little
from above; the whole object with margins; transparent background; square. At most one corrective regeneration.

## Records

Save the selected image (copy the file the tool produced, unresized) to `{folder}/00_three_quarter.png` and write
`{folder}/generation_master.json` (prompt, inputs with sha256, original output path, output, size).
"""


def request(design):
    folder = os.path.join(HERE, 'meshy', design, 'references_hd')
    image = Image.open(os.path.join(folder, '00_three_quarter.png')).convert('RGBA')
    image.putalpha(image.split()[3].point(lambda value: 255 if value >= 100 else 0))
    image.save(os.path.join(folder, '00_three_quarter_meshy.png'))
    body = {'image_url': f'@file:{design}/references_hd/00_three_quarter_meshy.png', 'ai_model': 'meshy-t2',
            'model_type': 'smart-topology', 'target_polycount': 3000, 'should_texture': False,
            'target_formats': ['glb']}
    os.makedirs(os.path.join(HERE, 'meshy', 'requests'), exist_ok=True)
    path = os.path.join(HERE, 'meshy', 'requests', f'{design}_st_v1.json')
    with open(path, 'w') as handle:
        json.dump(body, handle, indent=1)
    print(os.path.relpath(path, REPO))


def main():
    if sys.argv[1:2] == ['request']:
        for design in sys.argv[2:] or list(DESIGNS):
            request(design)
        return
    targets = sys.argv[1:] or list(DESIGNS)
    for design in targets:
        title, identity = DESIGNS[design]
        folder = os.path.join(HERE, 'meshy', design, 'references_hd')
        os.makedirs(folder, exist_ok=True)
        painting = key(os.path.join(ICONS, 'items', f'xeen_item_{design[1:]}', 'paint_a.png'))
        painting = painting.crop(painting.getbbox())
        canvas = Image.new('RGBA', (int(max(painting.size) * 1.15),) * 2)
        canvas.alpha_composite(painting, ((canvas.width - painting.width) // 2,
                                          (canvas.height - painting.height) // 2))
        canvas.save(os.path.join(folder, 'design_painting.png'))
        rel = os.path.relpath(folder, REPO)
        with open(os.path.join(folder, 'CODEX_BRIEF.md'), 'w') as handle:
            handle.write(BRIEF.format(title=title, folder=rel, identity=identity))
        print(rel)


main()
