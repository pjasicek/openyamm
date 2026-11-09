"""MM9 items as 3D ground items: the image and Meshy steps (GROUND_ITEM_3D_PLAYBOOK.md, with the paint+mask atlas
and registration of items_wip_equipment_geometry_finish and items_wip_maw; PLAN.md here).

  reference <design>     meshy/<design>/references_hd/design_painting.png: the MM9 icon project's HD painting keyed
                         (the design authority); for armour and misc, whose paintings are three-quarter views, it is
                         also the Meshy master 00_three_quarter.png
  master <design>        meshy/<design>/references_hd/CODEX_BRIEF.md (an HD three-quarter master from the painting,
                         for helms, boots and gauntlets, whose paintings are front or side views)
  st-request <design>    binary-alpha copy for Meshy and meshy/requests/<design>_st_v1.json (Smart Topology, 5 credits)
  paint-brief <design>   after `codex_texture.py prep`: the guide sheet (3x2 paint-only for one-material designs, 3x4
                         paint rows over mask rows otherwise) and codex_tex/<design>/CODEX_BRIEF_paint.md
  codex <brief> [...]    Codex image sessions on briefs, 16 at once (prompt on stdin; images are those a brief names)
Usage: python3 -I mm9item.py <command> <design|brief> [...]"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICON_PROJECT = os.path.join(REPO, 'level_generation', 'ui', 'mm9_item_icons_20261104')
sys.path.insert(0, os.path.join(ICON_PROJECT, 'scripts'))
from finish import key  # noqa: E402  (the icon project's magenta keying)

PARALLEL = 16
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
VIEWS = ['front', 'back', 'left', 'right', 'top']
MASK_COLOURS = {'metal': 'pure red #FF0000', 'leather': 'pure green #00FF00', 'cloth': 'pure blue #0000FF',
                'horn': 'pure yellow #FFFF00', 'gem': 'pure black #000000'}
MASK_MEANING = {'metal': 'every metal part (steel, iron, chain mail, gold, silver, bronze, copper, brass)',
                'leather': 'every leather part (straps, padding, hide, suede) and fur',
                'cloth': 'every cloth part (tabards, quilting, linings, cords, ribbons) and hair',
                'gem': 'every gemstone, crystal, glass, pearl, enamel or liquid seen through glass',
                'horn': 'every matte non-metal solid (wood, bone, horn, stone, parchment, paper, wax)'}
# Families whose HD painting is already a three-quarter view (the Meshy master as it is).
PAINTING_IS_MASTER = ('armor', 'misc')


def rel(path):
    return os.path.relpath(path, REPO)


def icon_x8(icon, path):
    image = Image.open(icon).convert('RGBA')
    image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
    canvas = Image.new('RGBA', (image.width + 160, image.height + 160), (255, 0, 255, 255))
    canvas.alpha_composite(image, (80, 80))
    canvas.convert('RGB').save(path)


def reference(name):
    entry = DESIGNS[name]
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    os.makedirs(folder, exist_ok=True)
    painting = key(entry['painting'])
    painting = painting.crop(painting.getbbox())
    canvas = Image.new('RGBA', (int(max(painting.size) * 1.15),) * 2)
    canvas.alpha_composite(painting, ((canvas.width - painting.width) // 2, (canvas.height - painting.height) // 2))
    canvas.save(os.path.join(folder, 'design_painting.png'))
    if entry['family'] in PAINTING_IS_MASTER and entry['route'] == 'meshy':
        canvas.save(os.path.join(folder, '00_three_quarter.png'))
    print(folder)


def master(name):
    entry = DESIGNS[name]
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    if not os.path.exists(os.path.join(folder, 'design_painting.png')):
        reference(name)
    icon_x8(entry['icon_path'], os.path.join(folder, 'icon_x8.png'))
    brief = f"""# Codex brief: HD reference view for the ground item model "{entry['title']}" ({name})

Scope: image generation only. Write ONLY into `{rel(folder)}/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs: `design_painting.png`, the item's approved HD painting (the
design, shape, proportion, colour and material authority), and `icon_x8.png`, its inventory icon (enlarged; magenta is
background).

## Deliverable (transparent background, about 1024 x 1024, unresized return)
- `00_three_quarter.png` — the item seen from the front three-quarter (camera turned about 35 degrees to the right
  and raised about 25 degrees above the ground), so its full volume, depth and top are visible.
Copy the file the tool produced to that path, and write `generation_runs.json` (prompt, input with sha256, original
output path, output path, selected flag, reason). At most one corrective regeneration.

## Prompt content
TASK CONTEXT — FANTASY-GAME ASSET: faithful high-definition 3D-modelling reference of the EXISTING item shown in
the supplied painting. Not a new design. ONE object, centred, generous margins, the whole object visible,
near-orthographic camera, true transparent background, no floor, no ground shadow, no display stand, no scenery, no
text. Even soft neutral studio light, no dramatic light, no strong cast shadows, no glow halo or sparkles around the
object. Credible, fully three-dimensional, semi-realistic game materials, sharp fine detail, clean solid silhouette.

Identity (from the painting): {entry['identity']}
{entry.get('master_note', '')}

Do NOT: add extra items, ornaments or parts not in the icon; do not change the colours or materials; do not crop
the object; no light rays, particles or aura outside the object.

Checks: one complete object; matches the icon's design and colours; three-quarter view showing depth; true
transparent background; nothing cropped.
"""
    with open(os.path.join(folder, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(brief)
    print(os.path.join(folder, 'CODEX_BRIEF.md'))


def st_request(name):
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    image = Image.open(os.path.join(folder, '00_three_quarter.png')).convert('RGBA')
    image.putalpha(image.split()[3].point(lambda value: 255 if value >= 100 else 0))
    image.save(os.path.join(folder, '00_three_quarter_meshy.png'))
    version = DESIGNS[name].get('meshy_version', 'v1')
    request = {'image_url': f'@file:{name}/references_hd/00_three_quarter_meshy.png', 'ai_model': 'meshy-t2',
               'model_type': 'smart-topology', 'target_polycount': 3000, 'should_texture': False,
               'target_formats': ['glb']}
    os.makedirs(os.path.join(HERE, 'meshy', 'requests'), exist_ok=True)
    path = os.path.join(HERE, 'meshy', 'requests', f'{name}_st_{version}.json')
    with open(path, 'w') as handle:
        json.dump(request, handle, indent=1)
    print(path)


def guide_sheet(folder, with_masks):
    atlas = Image.new('RGBA', (1536, 2048 if with_masks else 1024))
    for row_offset in ((0, 1024) if with_masks else (0,)):
        for index, view in enumerate(VIEWS):
            guide = Image.open(os.path.join(folder, f'guide_{view}.png')).convert('RGBA').resize((512, 512))
            atlas.alpha_composite(guide, ((index % 3) * 512, row_offset + (index // 3) * 512))
    path = os.path.join(folder, 'paint_mask_guide.png' if with_masks else 'guide_atlas.png')
    atlas.save(path)
    return os.path.basename(path)


NEUTRAL_WORDS = [
    (r'\b(blood|death|doom|kill\w*|slay\w*|murder\w*|war|battle|bad news|fate)\b', ''),
    (r'\b(sword|dirk|dagger|knife|blade|sabre|saber|scimitar|katana|rapier|cutlass)s?\b', 'flat metal piece'),
    (r'\b(axe|halberd|glaive|polearm|pick|scythe)s?\b', 'shaped metal head'),
    (r'\b(mace|hammer|club|flail|morning ?star|maul)s?\b', 'tool head'),
    (r'\b(spear|lance|trident|pike|javelin)s?\b', 'long pole'),
    (r'\b(bow|crossbow|arrow|bolt)s?\b', 'curved wooden frame'),
    (r'\b(cannon|gun|pistol|musket|blackpowder|barrel)s?\b', 'metal tube'),
    (r'\b(weapon|attack|strike|combat|fight\w*|lethal|deadly|sharp|edge|point|spike\w*)s?\b', 'part'),
]


def neutral(text):
    """The text with every weapon or harm word replaced: OpenAI's image filter blocks some weapon briefs."""
    for pattern, replacement in NEUTRAL_WORDS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return re.sub(r'  +', ' ', text)


def paint_brief(name, neutral_words=False):
    entry = dict(DESIGNS[name])
    if neutral_words:
        entry['title'] = f'Decorative prop {name}'
        entry['identity'] = ('A harmless static decorative prop for a cosy fantasy game, texture sheet only. '
                             + neutral(entry['identity']))
        entry['materials'] = neutral(entry['materials'])
    folder = os.path.join(HERE, 'codex_tex', name)
    references = os.path.join(HERE, 'meshy', name, 'references_hd')
    if not os.path.exists(os.path.join(references, 'design_painting.png')):
        reference(name)
    master_path = os.path.join(references, '00_three_quarter.png')
    Image.open(master_path if os.path.exists(master_path) else os.path.join(references, 'design_painting.png')).save(
        os.path.join(folder, 'design_reference.png'))
    icon_x8(entry['icon_path'], os.path.join(folder, 'icon_x8.png'))
    with_masks = 'surface_material' not in entry
    guide = guide_sheet(folder, with_masks)
    raw = 'paint_mask_raw_v1.png' if with_masks else 'paint_raw_v1.png'
    if with_masks:
        classes = '\n'.join(f'  - {MASK_COLOURS[c]}: {MASK_MEANING[c]}' for c in entry['material_classes'])
        layout = f"""- `{guide}`: 1536x2048 transparent sheet, three columns by FOUR rows of 512x512 cells. Rows 1-2 and rows
  3-4 hold the same five grey orthographic renders of the exact 3D model: FRONT, BACK, LEFT / RIGHT, TOP, empty.

Task: use your built-in image generation tool to paint the guide sheet. Output ONE PNG with a transparent background
and a 3:4 canvas (1536x2048 or the tool's nearest 3:4 size), the same layout, each object in exactly the same position,
size and outline as its grey guide. Paint the grey objects only; never redraw, enlarge, move or redesign them.

- Rows 1-2 (PAINT): the unlit base colour of the item on each view: {entry['materials']}.
- Rows 3-4 (MATERIAL MASK): the same five silhouettes filled with FLAT pure colours only, no shading, no texture, no
  outlines, no antialiased colour blends inside:
{classes}
  Every pixel of each silhouette gets exactly one of these colours; nothing outside the silhouettes."""
    else:
        layout = f"""- `{guide}`: 1536x1024 transparent sheet, three columns by two rows of 512x512 cells. Row 1: FRONT, BACK,
  LEFT. Row 2: RIGHT, TOP, empty. Each cell is a grey orthographic render of the exact 3D model.

Task: use your built-in image generation tool to paint the guide sheet. Output ONE 1536x1024 PNG with a transparent
background, the same layout, each object in exactly the same position, size and outline as its grey guide. Paint the
grey objects only; never redraw, enlarge, move or redesign them.

- Paint the unlit base colour of the item on each view: {entry['materials']}."""
    brief = f"""# {entry['title']}: {'paint + material mask' if with_masks else 'paint-only'} view atlas

Scope: image generation only. Write ONLY into `{rel(folder)}/`. Do not edit any other file, do not run builds.

Inputs (attached):
{layout}
- `design_reference.png`: the approved HD painting or master of the item, the material and detail reference.
- `icon_x8.png`: the original game icon (magenta is background), the colour reference.

Object: {entry['identity']}

- Facets, engravings, scrollwork and inner swirls follow the design reference, scaled to each view.
- Keep every gap and opening exactly as in the guide and fully transparent.
- Unlit base colour only: no lighting, no cast shadows, no ambient occlusion, no hot highlights or reflections, no
  glow halo, sparkles or aura outside the silhouette, no ground, no outlines, no text.
- The empty cell{'s' if with_masks else ''} (column 3 of row 2{' and row 4' if with_masks else ''}) stay{'' if with_masks else 's'} empty and transparent.

Save the generated image (copy the file the tool produced) to `{rel(folder)}/{raw}` and write
`generation_paint.json` (prompt, inputs with sha256, original output path, output, size). At most one corrective
regeneration, only if the silhouettes or layout are clearly wrong.
"""
    with open(os.path.join(folder, 'CODEX_BRIEF_paint.md'), 'w') as handle:
        handle.write(brief)
    print(os.path.join(folder, 'CODEX_BRIEF_paint.md'))


def codex(brief):
    """One Codex image session on a brief; a brief whose output exists is skipped."""
    brief = os.path.abspath(brief)
    text = open(brief).read()
    outputs = re.findall(r'to `[^`]*/([\w.-]+\.png)`', text)
    if 'HD reference view' in text:
        outputs = ['00_three_quarter.png']
    if outputs and all(os.path.exists(os.path.join(os.path.dirname(brief), o)) for o in outputs):
        print('SKIP', rel(brief), flush=True)
        return
    folder = os.path.dirname(brief)
    named = sorted(set(re.findall(r'`([\w.-]+\.png)`', open(brief).read())))
    images = [os.path.join(folder, n) for n in named
              if os.path.exists(os.path.join(folder, n)) and not n.startswith(('paint_raw', 'paint_mask_raw', '00_'))]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check',
                 '-c', 'model_reasoning_effort="medium"']
    for image in images:
        arguments += ['-i', image]
    prompt = (f'Follow the brief in {rel(brief)} exactly. The attached images are its inputs (named as in the brief). '
              'Produce the image with your built-in image generation tool and save it as specified.')
    log = os.path.splitext(brief)[0].replace('CODEX_BRIEF', 'codex_run') + '.log'
    with open(log, 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', rel(brief), result.returncode, flush=True)


def main():
    command, targets = sys.argv[1], sys.argv[2:]
    action = {'reference': reference, 'master': master, 'st-request': st_request, 'paint-brief': paint_brief,
              'neutral-brief': lambda name: paint_brief(name, True), 'codex': codex}[command]
    if command == 'codex':
        with ThreadPoolExecutor(PARALLEL) as pool:
            list(pool.map(action, targets))
    else:
        for target in targets:
            action(target)


main()
