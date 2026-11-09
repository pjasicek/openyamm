"""Hesper pickups (designs.json; a copy of level_generation/props/hesper_decorations/scripts/deco3d.py whose concept
paths are repository-relative): the non-Blender steps of the ground-item route
(level_generation/props/items_claude/GROUND_ITEM_3D_PLAYBOOK.md), with an approved concept crop as the design source
instead of an inventory icon.

  master <design>          meshy/<design>/references_hd/CODEX_BRIEF.md: the brief for the HD three-quarter master,
                           from the design's identity and its concept crop (concept_crop.png)
  st-request <design>      after the master is selected: the binary-alpha copy Meshy receives and
                           meshy/requests/<design>_st_v1.json (Smart Topology, untextured, 5 credits)
  paint-briefs <design>    after `codex_texture.py prep`: codex_tex/<design>/CODEX_BRIEF_{1,2,3}.md
  codex <brief> [image...] run one Codex image session on a brief (the prompt goes on stdin)
Usage: python3 -I deco3d.py <command> <design|brief> [...]"""
import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DESIGNS = os.path.join(HERE, 'designs.json')
PAINT_PARTS = {'1': ['front', 'top'], '2': ['back'], '3': ['left', 'right']}


def design(name):
    return json.load(open(DESIGNS))[name]


def rel(path):
    return os.path.relpath(path, REPO)


def source_text(name, entry, folder):
    """How the brief names its design source: the concept crop, or (for a design with no concept) its style
    references, copied into the folder as ref_<n>.png."""
    if entry.get('concept'):
        return ('Attached input: `concept_crop.png`, the approved concept painting of this decoration (from the Hesper '
                'pickups sheet). It is the design, shape, proportion, colour and material authority.',
                'No ground mound or floor: the object stands or lies on nothing, as in the concept.',
                'matches the concept\'s design and colours', 'not in the concept',
                'a high-definition reference of the EXISTING concept design, for 3D modelling. Not a new design.')
    os.makedirs(folder, exist_ok=True)
    names = []
    for n, ref in enumerate(entry['refs'], 1):
        shutil.copy(os.path.join(REPO, ref), os.path.join(folder, f'ref_{n}.png'))
        names.append(f'`ref_{n}.png` ({os.path.basename(ref)})')
    return ('This decoration has no concept painting: it is designed from the identity below. Attached style '
            'references: ' + ', '.join(names) + '. They set the world\'s materials, palette and painting style (the '
            'white ceramic and gold of the Ancients, the patched salvage of the Hesperians); do not copy their content.',
            'No ground mound: the object stands or lies on nothing.', 'matches the identity and the references\' style',
            'not named in the identity', 'a high-definition design reference for 3D modelling of the object in the identity '
            'below, in the style of the references.')


def master(name):
    entry = design(name)
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    if entry.get('concept'):
        os.makedirs(folder, exist_ok=True)
        concept = Image.open(os.path.join(REPO, entry['concept']))
        concept.crop(tuple(entry['crop'])).save(os.path.join(folder, 'concept_crop.png'))
    source, ground, check, extra, task = source_text(name, entry, folder)
    brief = f"""# Codex brief: HD reference view for the decoration model "{entry['title']}"

Scope: image generation only. Write ONLY into `{rel(folder)}/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. {source}

## Deliverable (transparent background, unresized return)
- `00_three_quarter.png`: the decoration seen from the front three-quarter (camera turned about 35 degrees to the
  right and raised about 25 degrees above the ground), so its full volume, depth and top are visible.
Also write `generation_runs.json` (id, prompt, input with sha256, output path, selected flag, reason, superseded
runs). At most one corrective regeneration.

## Prompt content
TASK: {task} ONE object,
centred, generous margins, the whole object visible, near-orthographic camera, true transparent background, no floor
plane, no ground shadow, no scenery, no text. {ground} Even soft neutral studio light, no dramatic light, no strong cast shadows. Credible, fully
three-dimensional, semi-realistic game materials, sharp fine detail.

Identity: {entry['identity']}

Do NOT: add people, creatures, extra objects or ornaments {extra}; do not change the colours or materials;
do not crop the object.

Checks: one complete object; {check}; three-quarter view showing depth; true
transparent background; nothing cropped.
"""
    with open(os.path.join(folder, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(brief)
    print(os.path.join(folder, 'CODEX_BRIEF.md'))


def st_request(name):
    entry = design(name)
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    image = Image.open(os.path.join(folder, '00_three_quarter.png')).convert('RGBA')
    image.putalpha(image.split()[3].point(lambda value: 255 if value >= 100 else 0))
    image.save(os.path.join(folder, '00_three_quarter_meshy.png'))
    request = {'image_url': f'@file:{name}/references_hd/00_three_quarter_meshy.png', 'ai_model': 'meshy-t2',
               'model_type': 'smart-topology', 'target_polycount': max(3000, entry['tris']), 'should_texture': False,
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
    if entry.get('concept'):
        Image.open(os.path.join(HERE, 'meshy', name, 'references_hd', 'concept_crop.png')).save(
            os.path.join(folder, 'concept_crop.png'))
    concept = '`concept_crop.png` (the original concept) and ' if entry.get('concept') else ''
    for part, views in PAINT_PARTS.items():
        items = '\n'.join(f'- `paint_{view}.png` over `guide_{view}.png` (the decoration seen from the {view})'
                          for view in views)
        brief = f"""# Codex brief: paint the views of the {entry['title']} 3D model (texture source), part {part}

Scope: image generation only. Write ONLY into `{rel(folder)}/`. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Inputs in this folder: `design_reference.png` (the approved HD design,
three-quarter view: the design, colour and material authority), {concept}one
`guide_<view>.png` per deliverable: a plain grey orthographic render of the EXACT 3D model from that side,
transparent background. The guide fixes the silhouette, position, scale and every shape edge.

## Deliverables (1024 x 1024, transparent background, unresized returns)
{items}

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the surface
materials of the design reference onto that shape: {entry['materials']}.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections, no rim light, no background, no floor.
Glowing parts (orange sacs, seams) are painted at their glowing colour, not as light cast on their surroundings.

Write `generation_runs_{part}.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light; transparent background.
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
