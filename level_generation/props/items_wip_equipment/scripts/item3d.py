"""3D ground item designs (designs.json): the non-Blender steps of the playbook (GROUND_ITEM_3D_PLAYBOOK.md).

  master <design>          meshy/<design>/references_hd/: the icon enlarged on magenta (icon_x8.png) and the Codex brief
                           for the HD three-quarter master (CODEX_BRIEF.md), from the design's identity text
  st-request <design>      after the master is selected: the binary-alpha copy Meshy receives and
                           meshy/requests/<design>_st_v1.json (Smart Topology, untextured, 5 credits)
  paint-briefs <design>    after `codex_texture.py prep`: codex_tex/<design>/CODEX_BRIEF_{1,2,3}.md (front + top, back,
                           left + right), from the design's material text
Usage: python3 -I item3d.py <command> <design|brief> [...]"""
import json
import os
import sys
import hashlib

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


def select_master(name, reason):
    entry = design(name)
    folder = os.path.join(HERE, 'meshy', name, 'references_hd')
    path = os.path.join(folder, 'generation_runs.json')
    receipt = json.load(open(path))
    source = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2', entry['master_icon'] + '.png')
    output = os.path.join(folder, '00_three_quarter.png')
    image = Image.open(output)
    alpha = image.getchannel('A').getextrema()
    if alpha[0] != 0 or alpha[1] < 250:
        raise ValueError('Master must have transparent background and opaque object pixels')
    receipt.update(selected=True, reason=reason, input_sha256=hashlib.sha256(open(source, 'rb').read()).hexdigest(),
                   output_sha256=hashlib.sha256(open(output, 'rb').read()).hexdigest(),
                   output_size=list(image.size), alpha_extrema=list(alpha))
    with open(path, 'w') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    st_request(name)


def paint_briefs(name):
    entry = design(name)
    folder = os.path.join(HERE, 'codex_tex', name)
    reference = os.path.join(HERE, 'meshy', entry['geometry_design'], 'references_hd', '00_three_quarter.png')
    Image.open(reference).save(os.path.join(folder, 'design_reference.png'))
    icon_x8(entry['master_icon'], os.path.join(folder, 'icon_x8.png'))
    for part, views in PAINT_PARTS.items():
        items = '\n'.join(f'- `paint_{view}.png` over `guide_{view}.png` (the item seen from the {view})'
                          for view in views)
        masks = '\n'.join(f'- `mask_{view}.png` in the exact `guide_{view}.png` framing'
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
{masks}

Each painting must keep the guide's silhouette EXACTLY: the same outline, size and position in the frame, every edge,
band, opening and detail where the guide has them; nothing added outside the silhouette, nothing cropped. Paint the
surface materials of the design reference onto that shape: {entry['materials']}.

LIGHTING: this is a TEXTURE SOURCE (albedo). Even, flat, shadowless light from the viewer; no cast shadows, no
ambient-occlusion darkening, no strong specular highlights or reflections (show metal as its base colour with only a
faint sheen), no rim light, no background, no floor.

MATERIAL MASKS: separate flat class-colour images, with exact guide silhouette and transparent background.
Red (#ff0000) = exposed metal, green (#00ff00) = leather, blue (#0000ff) = cloth/fur,
yellow (#ffff00) = horn/wood, black (#000000) = gemstone. No shading, texture or lighting in masks.
Paint metal fittings separately from leather/cloth/horn, even when their base colours look similar.
Use the image generation tool directly; nested Codex sessions are forbidden for this worker.

Write `generation_runs_{part}.json` (view, prompt, inputs with sha256, output, selected, reason). At most one
corrective regeneration per view. If the tool returns another size, keep it unresized and record it.

Checks per image: silhouette identical to the guide; materials and colours match the design reference; flat even
light with no shadows or hot highlights; transparent background.
"""
        with open(os.path.join(folder, f'CODEX_BRIEF_{part}.md'), 'w') as handle:
            handle.write(brief)
        print(os.path.join(folder, f'CODEX_BRIEF_{part}.md'))


def main():
    command, target = sys.argv[1], sys.argv[2]
    if command == 'select-master':
        select_master(target, sys.argv[3])
    else:
        {'master': master, 'st-request': st_request, 'paint-briefs': paint_briefs}[command](target)


if __name__ == '__main__':
    main()
