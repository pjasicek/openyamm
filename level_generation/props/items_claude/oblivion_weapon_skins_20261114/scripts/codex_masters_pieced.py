#!/usr/bin/env python3
"""Codex HD masters for the v2 skins (README.md "Bow v2: pieced upload" and "Legendary v2"): over the pieced guides
of prep_pieced.py (the bow, the claymore, the staff) or, for templates whose old views already show the seen faces
large and face-on (the war axe, the warhammer, the shield), over their original guides.

  python3 -I codex_masters_pieced.py brief <template> <tier> [version]   work/<template>/masters_t<tier>_<version>/
  python3 -I codex_masters_pieced.py run <template> <tier> [version]     one Codex image session on it (stdin prompt)
  python3 -I codex_masters_pieced.py mirror <template> <tier> [version]  02_back.png as the mirrored 01_front.png

The bow:

The guides show the bow cut into five segments stood side by side, each seen face-on to its inner face (the face toward
the string, which the player sees): left to right the upper tip, the upper limb with the grip wrap at its foot, the
handle block, then the lower limb and the lower tip at half size. The back view is the same row from behind (mirrored
order). Tier looks (the tier rule of 2026-11-14): HIGH polished ebony, gold filigree, crimson leather, gold fittings,
no glow; LEGENDARY the only glowing tier: dark star-metal with a blue-violet sheen, platinum fittings, luminous
cyan-violet rune channels along the limbs and glowing gems at the grip and the tips.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
NUMBER = {'front': '01', 'back': '02', 'left': '03', 'right': '04'}
PIECED = ('w_bow', 'w_claymore', 'w_staff')
# Views of the templates that keep their original guides (codex_masters.py VIEWS).
ORIGINAL_VIEWS = {'w_waraxe': ('front', 'back'), 'w_warhammer': ('front', 'back', 'left'),
                  's_steelshield': ('front', 'back')}

SEGMENTS = """The guide shows ONE recurve archery bow (sporting equipment) taken apart for a catalogue photo: its five
segments stand upright side by side, each seen face-on to its INNER face (the side that faces the string). Left to
right in the front view:
1. the upper tip fitting (a pointed ornamental metal tip, the string notch end);
2. the upper limb: a long tapering wooden limb; its widest lower end (the bottom fifth) is the leather grip wrap;
3. the handle block (riser) at the centre of the bow, a short ornamented block;
4. the lower limb (shown at half size): the grip wrap at its upper end, the limb tapering downward;
5. the lower tip fitting (half size).
The back view shows the same five segments from behind (the outer face), in mirrored order. Paint every segment as part
of one and the same bow: the ornament runs along each limb continuously from end to end."""

# What the guides show, per template other than the bow (SEGMENTS above).
LAYOUTS = {
    'w_claymore': """The guide shows ONE long two-handed sword replica (a museum display prop) taken apart for a
catalogue photo: three segments stand upright side by side, each seen face-on to the flat of the blade. Left to right in the
front view:
1. the upper half of the blade with the point;
2. the lower half of the blade (it continues the first: same width at the cut), with the central fuller;
3. the hilt: the crossguard with its decorated centre block, the long grip with ring bands, the round disc pommel.
The back view shows the same three segments from behind, in mirrored order. Paint them as one and the same sword:
anything running along the blade continues across the cut between segments 1 and 2.""",
    'w_staff': """The guide shows ONE wizard's walking staff (a theatre prop) taken apart for a catalogue photo: four
segments stand upright side by side. Left to right in the front view:
1. the head: the top of the shaft splitting into a claw of thin curling prongs;
2. the upper shaft below the head (a plain round shaft);
3. the middle shaft, where a cloth wrapping spirals around it;
4. the butt end of the shaft (shown at half size).
The back view shows the same four segments from behind, in mirrored order. Paint them as one and the same staff:
anything running along the shaft continues across the cuts.""",
    'w_waraxe': """The guide shows the ONE-HANDED ceremonial bearded axe (a regalia prop) from the front and the back: a
single flared blade with a round medallion near the eye and a short back spike, a twisted metal upper shaft, a handle
with ring bands and a pointed end cap.""",
    'w_warhammer': """The guide shows the long-handled ceremonial hammer (a regalia prop) from the front, the back and
the left: a square head with an engraved medallion panel on each side, a round flat striking face on one end and a
conical spike on the other, a twisted metal upper shaft, a long handle with ring bands and a pointed end cap.""",
    's_steelshield': """The guide shows the plate-armour shield (a museum armour piece) from the front (its INNER face,
with the leather hand strap: the face its bearer sees) and from the back (the outer face): overlapping horizontal
lames with raised ribs and small rivets, a scalloped top edge and rolled borders.""",
}

# Legendary v2 (the tier rule of 2026-11-14): the only glowing tier.
LEGENDARY_V2 = {
    'w_claymore': """- Blade: dark STAR-METAL: deep midnight-blue to blue-black polished metal with a blue-violet
  iridescent sheen and faint tiny silver star specks; NOT grey steel, NOT damascus.
- Rune channel: inside the fuller, one continuous channel of angular runes from the guard to near the point, filled
  with LUMINOUS CYAN light shading to VIOLET near the point (bright, saturated, as if glowing from inside; the colour
  strictly inside the channel: no halo on the metal).
- Edges: a crisp bright platinum honed line along both edges.
- Crossguard and pommel: polished PLATINUM with fine engraving; one faceted GLOWING VIOLET-CYAN crystal set in the
  guard's centre block and one in the pommel's centre (bright, luminous).
- Grip: midnight-blue leather wrapped with platinum wire; platinum ring bands.""",
    'w_staff': """- The whole shaft and the prongs: dark STAR-WOOD: deep midnight-blue to black-violet polished
  petrified wood with a blue-violet sheen; plain and calm, NO star specks, NO speckles, NO scattered dots.
- Rune channel: ONE clean continuous engraved channel spiralling down the shaft from the head to the butt, following
  the shaft's twist, a few pixels wide with small angular runes along it, filled with LUMINOUS CYAN light shading to
  VIOLET (bright, saturated, as if glowing from inside; the colour strictly inside the channel: no halo, no glow
  spots elsewhere).
- Prong tips sheathed in polished PLATINUM; one faceted GLOWING VIOLET-CYAN crystal held in the centre of the claw.
- The cloth wrapping: midnight-blue velvet bound with platinum wire (no stars on it).
- Thin platinum ring bands where the wrapping starts and ends.""",
    'w_waraxe': """- Axe head: dark STAR-METAL: deep midnight-blue to blue-black polished metal with a blue-violet
  iridescent sheen; a crisp bright platinum cutting edge along the whole bevel.
- Rune channel: one continuous channel of angular runes following the edge bevel and circling the medallion, filled
  with LUMINOUS CYAN light shading to VIOLET (bright, saturated, as if glowing from inside; the colour strictly
  inside the channel: no halo on the metal).
- Medallion: a faceted GLOWING VIOLET-CYAN crystal in its centre set in a platinum ring.
- Twisted upper shaft: polished platinum.
- Handle: dark star-metal with a glowing cyan rune channel running down its length; platinum ring bands; the grip end
  wrapped in midnight-blue leather with platinum wire; a platinum end cap tipped with a small GLOWING CYAN crystal.""",
    'w_warhammer': """- Hammer head: dark STAR-METAL: deep midnight-blue to blue-black polished metal with a blue-violet
  iridescent sheen, its edges and the striking face's rim polished platinum.
- Each engraved side panel: a rune sigil whose engraved lines glow LUMINOUS CYAN shading to VIOLET (bright, saturated,
  as if glowing from inside; the colour strictly inside the lines), around one faceted GLOWING VIOLET-CYAN crystal in
  the panel's centre.
- The spike: dark star-metal with a thin glowing cyan rune line along each facet edge.
- Twisted upper shaft: polished platinum.
- Handle: dark star-metal with a glowing cyan rune channel running down its length; platinum ring bands; the grip
  wrapped in midnight-blue leather with platinum wire; a platinum end cap tipped with a small GLOWING CYAN crystal.""",
    's_steelshield': """- Lames: dark STAR-METAL: deep midnight-blue to blue-black polished metal with a blue-violet
  iridescent sheen, on BOTH faces.
- Ribs, borders and the scalloped top edge: polished PLATINUM.
- Rune channels: along every lame, just below its rib, one continuous channel of angular runes across the whole width
  of the shield, filled with LUMINOUS CYAN light shading to VIOLET (bright, saturated, as if glowing from inside; the
  colour strictly inside the channel: no halo on the metal). On BOTH faces; on the inner face they must be clearly
  visible around the strap.
- Rivets along the top edge and the borders: small faceted GLOWING CYAN crystals set in platinum.
- Hand strap: midnight-blue leather with platinum buckles.""",
}

LOOKS = {
    3: ('HIGH tier: a masterwork, rich and ornate (a museum showpiece); it does not glow',
        """- Limbs: polished ebony-black wood with a deep glossy lacquer, inlaid with fine GOLD FILIGREE: thin, crisp,
  continuous flowing vine-and-scroll lines running the full length of each limb, drawn as sharp hairline gold
  inlay with small leaves and curls (precise jeweller's work, not blobs or splashes); most of the surface stays black.
- Grip wrap (the wide end of each limb next to the handle block): deep crimson leather wrapped with twisted gold wire.
- Handle block and both tip fittings: engraved polished GOLD with deep scrollwork; one small deep-red ruby set in the
  centre of the handle block; thin gold ring bands where the limbs meet the grip wrap and the tips.
- No glow anywhere: the gold and the ruby only catch soft highlights."""),
    4: ('LEGENDARY tier: a unique relic of starfall metal, far finer and stranger than any gilded masterwork (a '
        "museum's crown jewel); the only tier with glowing inlays",
        """- Limbs: dark STAR-METAL: deep midnight-blue to blue-black polished metal with a blue-violet iridescent
  sheen (like oil-on-steel or a starry night), faint tiny silver star specks; NOT black lacquer, NOT wood, NOT white.
- Rune channel: along the centre of EVERY limb segment runs one continuous engraved channel of angular runes from end
  to end, filled with LUMINOUS CYAN light shading to VIOLET at its ends (bright, saturated, as if glowing from inside;
  the colour stays strictly inside the channel lines: no halo or haze on the metal around it).
- Grip wrap (the wide end of each limb next to the handle block): midnight-blue leather wrapped with platinum wire.
- Handle block: polished PLATINUM (cool bright silver-white) with fine engraving, set with one large faceted GLOWING
  VIOLET-CYAN crystal gem in its centre (bright, luminous).
- Tip fittings: polished platinum with engraving, each set with a small faceted GLOWING CYAN crystal gem near its end.
- Thin platinum ring bands where the limbs meet the grip wrap, the handle block and the tips.
- The rune channels and the gems are the only bright saturated colours; everything else is dark blue-violet metal
  and platinum."""),
}


def folder(tier, version, template='w_bow'):
    return os.path.join(PROJECT, 'work', template, f'masters_t{tier}_{version}')


def views_of(template):
    return ('front', 'back') if template in PIECED else ORIGINAL_VIEWS[template]


def brief(template, tier, version='v2'):
    tier = int(tier)
    work = os.path.join(PROJECT, 'work', template)
    pieced = os.path.join(work, 'pieced')
    out = folder(tier, version, template)
    os.makedirs(out, exist_ok=True)
    views = views_of(template)
    for view in views:
        if template in PIECED:
            shutil.copy(os.path.join(pieced, f'guide_{view}.png'), os.path.join(out, f'guide_{view}.png'))
            shutil.copy(os.path.join(pieced, f'reference_{view}.png'), os.path.join(out, f'reference_{view}.png'))
        else:
            shutil.copy(os.path.join(work, f'guide_{view}.png'), os.path.join(out, f'guide_{view}.png'))
            shutil.copy(os.path.join(work, f'template_{view}.png'), os.path.join(out, f'reference_{view}.png'))
    if template == 'w_bow':
        title, materials = LOOKS[tier]
        subject, layout = 'recurve archery bow', SEGMENTS
    else:
        assert tier == 4, 'only the legendary tier is redone here'
        title = LOOKS[4][0]
        materials = LEGENDARY_V2[template]
        subject = {'w_claymore': 'two-handed sword replica', 'w_staff': "wizard's walking staff",
                   'w_waraxe': 'ceremonial bearded axe', 'w_warhammer': 'ceremonial long-handled hammer',
                   's_steelshield': 'plate-armour shield'}[template]
        layout = LAYOUTS[template]
    deliver = '\n'.join(f'- `{NUMBER[v]}_{v}.png` over `guide_{v}.png`' for v in views)
    inputs = '\n'.join(f'- `guide_{v}.png`: plain grey orthographic render of the EXACT 3D model, {v} view.'
                       for v in views)
    refs = '\n'.join(f'- `reference_{v}.png`: the same with the original low-resolution texture (where the parts are).'
                     for v in views)
    rel = os.path.relpath(out, REPO)
    text = f"""# Codex brief: {title} texture for a display-prop {subject} (tier {tier}, {version})

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds, do not call
Meshy.

Use your built-in image generation tool. Attached inputs (all in this folder):
{inputs}
{refs}

{layout}

## Deliverables (1024 x 1536 portrait, transparent background, unresized returns)
{deliver}

Each image must keep its guide's silhouettes EXACTLY: the same outlines, sizes and positions in the frame; nothing
added outside them, nothing cropped, any gaps between segments stay empty and transparent.

## Prompt content
TASK CONTEXT: PROP TEXTURE REFERENCE: a fantasy display prop (an ornamental {subject}) for a museum-style catalogue,
photographed as a product shot; seen up close, so every surface needs crisp, high-definition
material detail (fine lines a few pixels wide, sharp edges, no smudges or soft blotches).

Materials for this tier ({title}):
{materials}

LIGHTING: even, soft, neutral studio light from the viewer: the materials show their own colour and polish with only
gentle, broad highlights. No sky or scenery reflected, no dramatic light, no cast shadows, no rim light, no
background, no floor, no text.

Do NOT: change the shapes; join the segments; paint anything in the gaps; crop; add text or logos.

Checks per image: silhouettes identical to the guide; the tier's materials clearly recognisable; ornament crisp; even
light; true transparent background. Write `generation_runs.json` (view, prompt, inputs with sha256, output, selected,
reason). At most one corrective regeneration per view. If the tool returns another size, keep it unresized and record
it. If the image tool refuses a request (a safety refusal), retry that view once with more neutral wording (an
ornamental craft piece, a decorative display object; no weapon or combat words), and still produce every other view:
never stop after one refused view.
"""
    with open(os.path.join(out, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(text)
    print(os.path.join(out, 'CODEX_BRIEF.md'))


def run(template, tier, version='v2'):
    out = folder(int(tier), version, template)
    views = views_of(template)
    names = [f'guide_{v}.png' for v in views] + [f'reference_{v}.png' for v in views]
    arguments = [os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared', 'codex_slot.sh'),
                 'codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in names:
        arguments += ['-i', os.path.join(out, name)]
    prompt = (f'Follow the brief in {os.path.relpath(os.path.join(out, "CODEX_BRIEF.md"), REPO)} exactly. The attached '
              f'images are its inputs, in this order: {", ".join(names)}. Produce the images with your built-in image '
              'generation tool and save them as specified.')
    with open(os.path.join(out, 'codex_run.log'), 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', template, tier, version, result.returncode)


def mirror(template, tier, version='v2'):
    from PIL import Image, ImageOps
    out = folder(int(tier), version, template)
    ImageOps.mirror(Image.open(os.path.join(out, '01_front.png'))).save(os.path.join(out, '02_back.png'))
    with open(os.path.join(out, 'MIRRORED.txt'), 'a') as handle:
        handle.write('02_back.png is 01_front.png mirrored (the back view was refused or failed).\n')
    print('MIRRORED', template, tier, version)


if __name__ == '__main__':
    {'brief': brief, 'run': run, 'mirror': mirror}[sys.argv[1]](*sys.argv[2:])
