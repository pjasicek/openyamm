#!/usr/bin/env python3
"""Step 1 (README.md): one Codex HD design master per weapon kind, from the MM6-MM8 item icons of that kind. The
master is the design the Blender model is built to (proportions, head outline, fittings), at the Oblivion template's
level of detail; the tier masters (codex_masters.py) are painted later over the finished model's guides.

  python3 -I codex_design.py brief <kind>   writes work/<kind>/design/ (icons, CODEX_BRIEF.md)
  python3 -I codex_design.py run <kind>     one Codex image session on it (prompt on stdin)
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2')

# kind: (icons, title, identity, views {file: (size, description)})
KINDS = {
    'spear': (
        ['spear1', 'item042', '7item032', 'spear4', 'spear3'],
        'ceremonial processional pole with a leaf-shaped finial (spear form)',
        'A Might and Magic style processional pole in spear form (a display replica): a long leaf-shaped polished '
        'steel finial with a raised central ridge (diamond section) and bevelled edges, a round socket with two '
        'raised collar rings, a short straight cross-bar (lugs) just below the socket as on the item042 and spear4 '
        'icons, a straight wooden pole with a few thin metal bands and a spiral leather wrap where the hands hold '
        'it, and a pointed metal end cap.',
        {'01_front.png': ('1024x1536', 'the whole pole standing upright, finial at the top, the finial\'s flat '
                                       'facing the viewer, filling the frame height'),
         '02_head.png': ('1024x1536', 'a close-up of the upper part only: the finial, socket, collar rings, '
                                      'cross-bar and the first band of the pole, flat facing the viewer, filling the frame')}),
    'halberd': (
        ['halberd1', 'halberd3', 'item048', 'halberd2'],
        'halberd',
        'A Might and Magic halberd: a broad axe blade on one side with a convex, slightly crescent cutting edge, a '
        'shorter back spike (a curved beak) on the other side, a long top spike with a diamond-section point, long '
        'riveted metal langets running down the shaft below the head, a straight wooden shaft with metal bands, a '
        'leather grip wrap and a metal butt cap.',
        {'01_front.png': ('1024x1536', 'the whole halberd standing upright, head at the top, the axe blade\'s flat '
                                       'facing the viewer (blade to the left, beak to the right), filling the frame '
                                       'height'),
         '02_head.png': ('1024x1536', 'a close-up of the head only: top spike, axe blade, beak, socket and langets, '
                                      'flat facing the viewer, filling the frame')}),
    'trident': (
        ['trident3', 'item054', 'trident1', 'trident2'],
        'trident',
        'A Might and Magic war trident: three barbed steel prongs, the middle one longer and straight with a '
        'diamond-section point, the two side prongs rising from a curved cross-piece and curving slightly outward, '
        'each prong with a small barb, a socket with collar rings, a straight shaft with metal bands, a leather grip '
        'wrap and a metal butt cap.',
        {'01_front.png': ('1024x1536', 'the whole trident standing upright, prongs at the top, the flat of the '
                                       'prongs facing the viewer, filling the frame height'),
         '02_head.png': ('1024x1536', 'a close-up of the head only: three prongs, cross-piece, socket and collar, '
                                      'flat facing the viewer, filling the frame')}),
    'crossbow': (
        ['crsbow1', 'crsbow2', 'item063', 'crsbow3'],
        'antique target crossbow (historical sporting equipment, museum replica)',
        'A museum replica of a historical target-shooting crossbow as used at medieval archery festivals: a long '
        'polished wooden stock (tiller) with a curved butt, a steel prod (the bow part) mounted crosswise at the '
        'front with slightly recurved tips and a metal binding, a taut cord drawn back to a round nut on top of the '
        'stock, a blunt practice bolt with fletching lying in the top groove, a long curved trigger lever under the '
        'stock, a small metal foot stirrup at the front end, metal bands and rivets. The prod lies FLAT, crosswise '
        '(horizontal, at right angles to the stock), as on every real crossbow.',
        {'01_top.png': ('1536x1024', 'seen from directly above (top-down plan view), the stock running left to '
                                     'right (butt left, stirrup right), the prod spread crosswise (vertical in the '
                                     'image) near the right end, the cord drawn back to the nut, the bolt in its '
                                     'groove, filling the frame'),
         '02_three_quarter.png': ('1536x1024', 'a three-quarter view from above and in front-left, the same object, '
                                               'filling the frame')}),
    'wand': (
        ['wand1', 'wand4', 'wand2', 'item155', 'wand5'],
        'magic wand',
        'A Might and Magic magic wand about 35 cm long: a slender tapered rod with a few raised metal rings, a '
        'small pommel at the bottom, and at the top a faceted crystal gem held by four curved metal claws in a '
        'metal cup, as on the wand1 and wand4 icons.',
        {'01_front.png': ('1024x1536', 'the whole wand standing upright, gem at the top, filling the frame height'),
         '02_head.png': ('1024x1024', 'a close-up of the top: the crystal, the claws and the cup')}),
    'blaster': (
        ['raygun1', '7item064', 'raygun2', 'blastsg'],
        'ray pistol (blaster)',
        'A Might and Magic blaster: a retro-futuristic ray pistol of the Ancients, about 30 cm long: a polished '
        'silver body, a long ribbed barrel with copper rings ending in an emitter tip, a glowing green energy cell '
        'visible in a window on the side, swept fins and a curved hook-shaped guard, a curved grip with dark inlays.',
        {'01_side.png': ('1536x1024', 'seen from the side, muzzle pointing to the right, grip down'),
         '02_top.png': ('1536x1024', 'seen from directly above, muzzle pointing to the right')}),
    # Added 2026-11-14 (README.md "Club"): one template for every club, MM6-MM8 values all below the mid band.
    'club': (
        ['item077', 'club1', '7item058', 'club2'],
        'shillelagh (a traditional Irish blackthorn walking stick with a heavy knob; a folk-craft display replica)',
        'A folk-craft shillelagh replica in a Might and Magic style, about 80 cm long: one piece of gnarled hardwood '
        'thickening steadily from a slim handle to a heavy rounded knob at the top (the knob about four times the '
        'handle\'s width), a few natural knots and bark ridges along it, a forged iron band around the knob\'s base '
        'and another near its top, about ten short pyramid-shaped decorative iron studs set into the knob (as on the '
        'item077 icon), a rawhide wrap over the handle and a small rounded knob at the bottom end. One straight axis '
        '(no crook): the knob is an uneven swelling of the same wood, not a separate ball.',
        {'01_front.png': ('1024x1536', 'the whole stick standing upright, knob at the top, filling the frame '
                                       'height'),
         '02_head.png': ('1024x1536', 'a close-up of the upper half: the knob with its iron bands and studs, '
                                      'filling the frame')}),
}


def folder(kind):
    return os.path.join(PROJECT, 'work', kind, 'design')


def brief(kind):
    icons, title, identity, views = KINDS[kind]
    out = folder(kind)
    os.makedirs(out, exist_ok=True)
    for icon in icons:
        shutil.copy(os.path.join(ICONS, f'{icon}.png'), os.path.join(out, f'icon_{icon}.png'))
    rel = os.path.relpath(out, REPO)
    deliver = '\n'.join(f'- `{name}` ({size}): {text}.' for name, (size, text) in views.items())
    text = f"""# Codex brief: HD design master of a {title} for a first-person weapon model

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds, do not call
Meshy.

Use your built-in image generation tool. Attached inputs (all in this folder): the original Might and Magic 6-8 item
icons of this weapon kind, `icon_<name>.png` ({', '.join(icons)}). They are the design source: the new weapon must read
as a Might and Magic weapon of this kind, combining their typical shapes and ornament into one clean design.

## Deliverables (transparent background, unresized returns)
{deliver}

## Prompt content
TASK CONTEXT: PROP DESIGN REFERENCE for a 3D modeller: a historical-fantasy replica display prop ({title}) for a
museum-style catalogue, photographed as a clean orthographic product shot. It will be held close to the camera in a
first-person game, so the design must be clear and solid: crisp bevelled edges, readable fittings, no hair-thin parts.

Design: {identity}

Materials: well-made craftsman's work: clean satin steel with polished bevels, polished wood, dark leather wrap, steel
and small brass fittings (the material tiers are painted later; this image fixes the shape).

LIGHTING: even, soft, neutral studio light from the viewer; gentle broad highlights only. No background, no floor, no
cast shadows, no text, no scenery reflections. Orthographic (no perspective distortion).

Checks per image: the shape matches the design above and the icons' character; parts are symmetric where the design
is symmetric; true transparent background. Write `generation_runs.json` (view, prompt, inputs with sha256, output,
selected, reason). At most one corrective regeneration per view.
"""
    with open(os.path.join(out, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(text)
    print(os.path.join(out, 'CODEX_BRIEF.md'))


def run(kind):
    out = folder(kind)
    icons = KINDS[kind][0]
    names = [f'icon_{icon}.png' for icon in icons]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in names:
        arguments += ['-i', os.path.join(out, name)]
    prompt = (f'Follow the brief in {os.path.relpath(os.path.join(out, "CODEX_BRIEF.md"), REPO)} exactly. The attached '
              f'images are its inputs, in this order: {", ".join(names)}. Produce the images with your built-in image '
              'generation tool and save them as specified.')
    with open(os.path.join(out, 'codex_run.log'), 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', kind, result.returncode)


if __name__ == '__main__':
    {'brief': brief, 'run': run}[sys.argv[1]](sys.argv[2])
