"""3D ground item designs (designs.json): the non-Blender steps of the playbook (GROUND_ITEM_3D_PLAYBOOK.md).

  master <design>          meshy/<design>/references_hd/: the icon enlarged on magenta (icon_x8.png) and the Codex brief
                           for the HD three-quarter master (CODEX_BRIEF.md), from the design's identity text
  st-request <design>      after the master is selected: the binary-alpha copy Meshy receives and
                           meshy/requests/<design>_st_v1.json (Smart Topology, untextured, 5 credits)
  paint-briefs <design>    after `codex_texture.py prep`: codex_tex/<design>/CODEX_BRIEF_{1,2,3}.md (front + top, back,
                           left + right), from the design's material text
  codex <brief> [image...] run one Codex image session on a brief (prompt on stdin: `codex exec -i` takes every
                           following argument as an image); images default to those the brief names in its folder
Usage: python3 -I item3d.py <command> <design|brief> [...]"""
import json
import os
import re
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2')
DESIGNS = os.path.join(HERE, 'designs.json')
PAINT_PARTS = {'1': ['front', 'top'], '2': ['back'], '3': ['left', 'right']}


def design(name):
    return json.load(open(DESIGNS))[name]


def rel(path):
    return os.path.relpath(path, REPO)


def icon_x8(icon, path):
    image = Image.open(os.path.join(ICONS, icon + '.png')).convert('RGBA')
    image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
    canvas = Image.new('RGBA', (image.width + 160, image.height + 160), (255, 0, 255, 255))
    canvas.alpha_composite(image, (80, 80))
    canvas.convert('RGB').save(path)


def master(name):
    entry = design(name)
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    os.makedirs(folder, exist_ok=True)
    icon_x8(entry['master_icon'], os.path.join(folder, 'icon_x8.png'))
    brief = f"""# Codex brief: HD reference view for the ground item model "{entry['title']}" (icon {entry['master_icon']})

Scope: image generation only. Write ONLY into `{rel(folder)}/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached input: `icon_x8.png` — the restored inventory icon of the item
(enlarged; magenta is background). It is the design, shape, proportion, colour and material authority.

## Deliverable (transparent background, 1024 x 1024, unresized return)
- `00_three_quarter.png` — the item seen from the front three-quarter (camera turned about 35 degrees to the right
  and raised about 25 degrees above the ground), so its full volume, depth and top are visible.
Also write `generation_runs.json` (id, prompt, input with sha256, output path, selected flag, reason, superseded runs).
At most one corrective regeneration.

## Prompt content
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic item from the supplied inventory icon, as a reference for 3D modelling. Not a new design. ONE object, centred,
generous margins, the whole object visible, near-orthographic camera, true transparent background, no floor, no
ground shadow, no stand, no head or feet inside it, no scenery, no text. Even soft neutral studio light, no dramatic
light, no strong cast shadows. Credible, fully three-dimensional, semi-realistic game materials, sharp fine detail.

Identity (from the icon): {entry['identity']}

Do NOT: add a mannequin, a head, legs, a person, a display stand, extra items or ornaments not in the icon; do not
change the colours or materials; do not crop the object.

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
    request = {'image_url': f'@file:{name}/references_hd/00_three_quarter_meshy.png', 'ai_model': 'meshy-t2',
               'model_type': 'smart-topology', 'target_polycount': 3000, 'should_texture': False,
               'target_formats': ['glb']}
    os.makedirs(os.path.join(HERE, 'meshy', 'requests'), exist_ok=True)
    path = os.path.join(HERE, 'meshy', 'requests', f'{name}_st_v1.json')
    with open(path, 'w') as handle:
        json.dump(request, handle, indent=1)
    print(path)


def paint_briefs(name):
    entry = design(name)
    folder = os.path.join(HERE, 'codex_tex', name)
    reference = os.path.join(HERE, 'meshy', name, 'references_hd', '00_three_quarter.png')
    Image.open(reference).save(os.path.join(folder, 'design_reference.png'))
    icon_x8(entry['master_icon'], os.path.join(folder, 'icon_x8.png'))
    for part, views in PAINT_PARTS.items():
        items = '\n'.join(f'- `paint_{view}.png` over `guide_{view}.png` (the item seen from the {view})'
                          for view in views)
        brief = f"""# Codex brief: paint the views of the {entry['title']} 3D model (texture source), part {part}

Scope: image generation only. Write ONLY into `{rel(folder)}/`. Do not edit
any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design of the
item, three-quarter view: the design, colour and material authority), `icon_x8.png` (the original game icon) and
one `guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge.

## Deliverables (1024 x 1024, transparent background, unresized returns)
{items}

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
band, opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the
surface materials of the design reference onto that shape: {entry['materials']}.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections (show metal as its base colour with only a
faint sheen), no rim light, no background, no floor.

Write `generation_runs_{part}.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light with no shadows or hot highlights; transparent background.
"""
        with open(os.path.join(folder, f'CODEX_BRIEF_{part}.md'), 'w') as handle:
            handle.write(brief)
        print(os.path.join(folder, f'CODEX_BRIEF_{part}.md'))


def codex(brief, images):
    brief = os.path.abspath(brief)
    folder = os.path.dirname(brief)
    if not images:
        named = sorted(set(re.findall(r'`([\w.-]+\.png)`', open(brief).read())))
        images = [os.path.join(folder, n) for n in named
                  if os.path.exists(os.path.join(folder, n)) and not n.startswith(('paint_', '00_'))]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for image in images:
        arguments += ['-i', image]
    prompt = (f'Follow the brief in {rel(brief)} exactly. The attached images are its inputs (named as in the brief). '
              'Produce the images with your built-in image generation tool and save them as specified.')
    log = os.path.splitext(brief)[0].replace('CODEX_BRIEF', 'codex_run') + '.log'
    with open(log, 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', rel(brief), result.returncode)


def main():
    command, target = sys.argv[1], sys.argv[2]
    if command == 'codex':
        codex(target, sys.argv[3:])
    else:
        {'master': master, 'st-request': st_request, 'paint-briefs': paint_briefs}[command](target)


main()
