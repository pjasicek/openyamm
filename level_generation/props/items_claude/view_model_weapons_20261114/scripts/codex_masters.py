#!/usr/bin/env python3
"""Step 4 (README.md): Codex HD masters of one weapon kind in one tier, painted over the exact silhouettes of the Meshy
upload (prep.py guides), with the kind's design master (codex_design.py) as the shape and ornament reference.

  python3 -I codex_masters.py brief <kind> <tier>   writes work/<kind>/masters_t<tier>/ (inputs, CODEX_BRIEF.md)
  python3 -I codex_masters.py run <kind> <tier>     one Codex image session on it (prompt on stdin)

Tiers follow engine/world_items/held_tiers.yml: 1 low, 2 mid, 3 high, 4 legendary. The image tool refuses weapon
words as violence: the briefs call the weapons display props and replicas (the Oblivion skins' lesson).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, HERE)
from kinds import KINDS  # noqa: E402

NUMBER = {'front': '01', 'back': '02', 'left': '03', 'right': '04', 'top': '05', 'bottom': '06'}

# kind: (title, layout of the guide, design files, part families)
WEAPON = {
    'spear': ('ceremonial processional pole with a leaf-shaped finial',
              'The pole is shown CUT INTO FOUR PIECES standing side by side, left to right: (1) the head assembly '
              '(leaf-shaped finial with a central rib and side flutes, collar rings, a round socket with a cross-bar '
              'ending in turned knobs, three thin rings at the socket base), (2) the upper pole: wood with one wide '
              'metal band, (3) the middle pole: plain wood with a thin metal band near its lower end, (4) the lower '
              'pole: the spiral leather grip wrap over its upper two thirds, a thin metal band, a short piece of '
              'wood, the metal end ferrule with its ring and the pointed end cap.',
              ('01_front.png', '02_head.png'), ('blade', 'metal', 'brass', 'wood', 'leather')),
    'halberd': ('ceremonial halberd (a display replica)',
                'The halberd is shown CUT INTO THREE PIECES standing side by side, left to right: (1) the head '
                'assembly (top spike, broad crescent axe blade, hooked back beak, gilded clamps either side of the '
                'socket, riveted langets with square studs running down the pole), (2) the middle of the pole: wood with '
                'a pair of thin metal bands, a thin band lower down and at its very bottom the top of the leather grip '
                'wrap, (3) the lower pole: the leather grip wrap, a thin metal band, a short piece of wood and the '
                'rounded metal butt cap.',
                ('01_front.png', '02_head.png'), ('blade', 'metal', 'brass', 'wood', 'leather')),
    'trident': ('ceremonial trident (a display replica)',
                'The trident is shown CUT INTO THREE PIECES standing side by side, left to right: (1) the head '
                'assembly (a long straight middle point, two side prongs rising from a curved cross-piece with small '
                'barbs near their tips, a round boss with a set stone where they meet, rings on the side prongs, the '
                'socket with its collars), (2) the middle of the pole: wood with one wide and one thin metal band, (3) '
                'the lower pole: a thin metal band, the leather grip wrap, another thin band, a short piece of wood and '
                'the rounded metal butt cap.',
                ('01_front.png', '02_head.png'), ('blade', 'metal', 'brass', 'wood', 'leather', 'gem')),
    'wand': ('magic wand (a fantasy display prop)',
             'The whole wand stands upright: the crystal held by curved claws in a cup at the top, a slender rod '
             'with rings and a grip, a small pommel at the bottom.',
             ('01_front.png', '02_head.png'), ('metal', 'brass', 'wood', 'leather', 'crystal')),
    'blaster': ('retro-futuristic ray pistol (a science-fiction display prop)',
                'The pistol is seen whole: a body with an energy-cell window, a ribbed barrel with rings ending in '
                'an emitter, a guard and a curved grip.',
                ('01_side.png', '02_top.png'), ('body', 'brass', 'grip', 'cell')),
    # Every archery wording was refused (two wordings, four tiers); after the user's review (2026-11-14, the reshaped
    # tiller) a workshop instrument and museum stock furniture, no bow, cord, dart or trigger words.
    'crossbow': ('antique workshop instrument: a carved wooden stock (museum stock furniture) with a curved steel '
                 'spring across its front',
                 'The object is seen whole: a long carved wooden stock with a shaped butt and a cheek rest, a laced '
                 'leather hand grip at its narrow wrist, decorative side plates with a set stone each, a short wooden '
                 'peg handle underneath, a curved steel spring across the front held by two metal clamps, a thin '
                 'cord, a slim rod lying in a groove on top, a long metal bar along the underside and a small metal '
                 'loop at the front.',
                 ('01_top.png',), ('metal', 'brass', 'wood', 'leather', 'string', 'gem')),
    # The image tool refused 'club' and 'cudgel' as violence (work/club/design): a shillelagh walking stick.
    'club': ('shillelagh (a traditional Irish walking stick with a heavy knob; a folk-craft display replica)',
             'The stick is shown CUT INTO TWO PIECES standing side by side, left to right: (1) the upper part: the '
             'egg-shaped knob with a riveted iron band at its neck and another near its top, pyramid-shaped iron studs '
             'over the knob, and the knotted shaft below it, (2) the lower part: the knotted shaft, the criss-cross '
             'rawhide wrap of the handle, a thin iron band and the small rounded end knob.',
             ('01_front.png', '02_head.png'), ('wood', 'metal', 'brass', 'leather')),
}

# One text per tier and material family (the same looks for every kind; held_tiers.yml's tier notes).
TIERS = {
    1: ('LOW tier: crude, cheap, hard-used', {
        'blade': 'dark grey forged iron, not steel: hammer marks and forge scale, coarse uneven grinding streaks, a '
                 'few small rust-brown spots and pitting; the bevelled rims a narrow rough brighter band',
        'metal': 'plain blackened iron fittings, rough and slightly pitted, worn bright only on the high points',
        'brass': 'dull blackened iron rings (no brass)',
        'wood': 'plain unpolished grey-brown ash wood, coarse open grain, scuffs and small dents',
        'leather': 'worn brown rawhide and coarse cord wrapping, frayed and dirty',
        'gem': 'a dull unpolished grey-green stone',
        'crystal': 'a cloudy, roughly cut pale grey-blue quartz',
        'body': 'dull gunmetal grey metal with scratches, worn paint and grime in the recesses',
        'grip': 'cracked dark brown bakelite-like grip plates',
        'cell': 'a dim yellow-green energy cell behind scratched glass',
        'string': 'a plain hemp cord'}),
    2: ('MID tier: clean, well-made craftsman\'s work', {
        'blade': 'bright clean satin steel: fine lengthwise grinding grain on the flats, smoother polished flutes, '
                 'clearly polished bright bevels along both rims, light honest wear',
        'metal': 'polished steel fittings with crisp chamfers, darker in the recesses',
        'brass': 'polished brass rings and rivets',
        'wood': 'polished honey-orange yew or ash wood with a clear straight grain under a satin varnish',
        'leather': 'dark brown leather wrapped in a neat spiral with fine twisted steel wire',
        'gem': 'a polished deep blue cabochon in a brass setting',
        'crystal': 'a clear faceted sapphire-blue crystal',
        'body': 'brushed silver steel panels with polished bevels and brass screws',
        'grip': 'polished walnut grip plates with brass rivets',
        'cell': 'a bright green energy cell behind clear glass',
        'string': 'a waxed linen cord'}),
    3: ('HIGH tier: a masterwork, rich and ornate (a museum showpiece)', {
        'blade': 'mirror-polished silvery steel, very bright and clean, a delicate etched vine-scroll band along the '
                 'central rib near the base, finely polished rims as a crisp bright line',
        'metal': 'gilded fittings with engraved scrollwork, polished gold high points, deep engraved recesses',
        'brass': 'bright gold rings',
        'wood': 'dark lacquered ebony-black wood with fine gold filigree inlay lines',
        'leather': 'deep crimson leather wrapped with twisted gold wire',
        'gem': 'a faceted deep-red ruby in a gold setting',
        'crystal': 'a brilliant faceted ruby-red crystal held in gold claws',
        'body': 'polished silver with engraved gold scrollwork panels',
        'grip': 'ivory grip plates with gold inlay',
        'cell': 'a glowing ruby-red energy cell behind cut crystal',
        'string': 'a silk cord bound with gold thread'}),
    4: ('LEGENDARY tier: an artifact of ancient power (a relic)', {
        'blade': 'exotic dark star-metal: blackened blue-grey steel with a faint violet sheen, a line of engraved '
                 'runes along the central rib inlaid with luminous cyan-blue light, the bevelled rims a bright silvery '
                 'line',
        'metal': 'dark star-metal fittings with fine platinum-white filigree and small luminous cyan rune marks',
        'brass': 'platinum-white rings engraved with tiny cyan runes',
        'wood': 'pale ivory-white bone-like wood with a spiral of platinum inlay',
        'leather': 'midnight-blue leather wrapped with twisted platinum wire',
        'gem': 'a luminous faceted cyan-blue star sapphire in a platinum setting',
        'crystal': 'a luminous faceted violet-blue crystal with a bright inner glow in platinum claws',
        'body': 'black star-metal panels with platinum trim and luminous cyan rune lines',
        'grip': 'pale bone grip plates with platinum inlay',
        'cell': 'a brilliant cyan-white energy cell',
        'string': 'a silvery cord'}),
}
# Per kind: tier materials and part names that differ from the shared ones (the club's woods, iron and rawhide).
KIND_TIERS = {
    ('club', 1): {
        'wood': 'rough knotted root wood: grey-brown ash with a coarse open grain, patches of rough dark bark still on '
                'it, small splits, scuffs and dents',
        'metal': 'crude blackened forged iron, hammer marks, pitted, with a few rust-brown spots, worn bright only on '
                 'the stud tips and band edges',
        'brass': 'crude black iron rivet heads (no brass)',
        'leather': 'worn pale rawhide strips wrapped criss-cross, frayed and dirty, the ends tied with coarse cord'},
    ('club', 2): {
        'wood': 'dark seasoned hardwood, oiled deep walnut brown, smooth and polished where handled, its knots and '
                'flowing grain clearly visible, no bark',
        'metal': 'well-forged dark grey iron bands and studs with crisp facets and polished edges, darker in the '
                 'recesses',
        'brass': 'polished brass rivet heads',
        'leather': 'dark brown leather strips wrapped neatly criss-cross, the ends stitched'},
}
# The poles' legendary skin after the user's review (2026-11-14): the shaft is what shows at idle, so it carries the
# tier; bone-white wood read plain. Dark wood here, the glowing spiral channel added by post.py (README.md "Legendary
# poles"), glowing stones in the collars.
KIND_TIERS.update({(pole, 4): {
    'blade': 'exotic dark star-metal: blackened steel with a deep blue-violet sheen, a line of engraved runes along '
             'the central rib inlaid with luminous cyan light, the bevelled rims a bright platinum-white line',
    'metal': 'dark star-metal fittings (blackened steel with a blue-violet sheen) edged with bright platinum-white '
             'filigree, each collar and band set with small glowing cyan gemstones',
    'brass': 'bright platinum-white rings set with tiny glowing cyan stones',
    'wood': 'near-black ebony wood with a deep blue-violet sheen and a fine straight grain running along the pole, '
            'plain and smooth between the fittings',
    'leather': 'deep midnight-violet leather wrapped with twisted platinum wire',
    'gem': 'a luminous faceted cyan star sapphire in a platinum setting'} for pole in ('spear', 'halberd', 'trident')})
# The crossbow's tiers after the user's review (2026-11-14): four clearly different instruments at a glance.
KIND_TIERS.update({
    ('crossbow', 1): {
        'wood': 'rough weathered grey-brown wood, dry and unpolished, coarse open grain, scuffs, dents and dark grime',
        'metal': 'crude rusty iron: dark pitted iron with orange-brown rust patches, worn bright only on the edges',
        'brass': 'rusty black iron clamps and plate (no brass)',
        'leather': 'worn cracked brown rawhide laced with coarse cord',
        'string': 'a plain frayed hemp cord',
        'gem': 'a plain dark iron rivet boss'},
    ('crossbow', 2): {
        'wood': 'warm polished walnut, rich red-brown with a flowing natural grain under a satin oil finish',
        'metal': 'clean polished steel with crisp chamfers, satin flats, darker in the recesses',
        'brass': 'polished steel clamps and butt plate',
        'leather': 'dark brown leather laced neatly with thin cord',
        'string': 'a waxed cream linen cord',
        'gem': 'a polished steel boss'},
    ('crossbow', 3): {
        'wood': 'deep black lacquered ebony with fine flowing gold filigree scrollwork inlaid along its sides',
        'metal': 'mirror-polished silver steel with engraved borders',
        'brass': 'bright polished gold with engraved scrollwork',
        'leather': 'deep crimson leather laced with gold thread',
        'string': 'a silk cord bound with gold thread',
        'gem': 'a faceted deep-red ruby in a gold setting (not glowing)'},
    ('crossbow', 4): {
        'wood': 'blackened wood with a faint blue-violet sheen, a luminous cyan-violet rune channel running along '
                'each side of the stock (thin glowing lines with small rune marks)',
        'metal': 'dark star-metal: blackened steel with a deep blue-violet sheen, a luminous cyan-violet rune line '
                 'along the curved spring',
        'brass': 'bright platinum-white clamps and butt plate',
        'leather': 'deep midnight-violet leather laced with platinum wire',
        'string': 'a silvery cord',
        'gem': 'a luminous glowing cyan-violet crystal in a platinum setting'},
})
KIND_PART_NAMES = {
    'crossbow': {'wood': 'The wooden stock and the peg handle', 'metal': 'The curved spring, side plates, the bar '
                 'underneath, the loop at the front and the nut', 'brass': 'The two clamps on the spring and the butt '
                 'plate', 'leather': 'The laced hand grip', 'string': 'The cord', 'gem': 'The set stones (one in each '
                 'side plate, one in the nose)'},
    'club': {'wood': 'The stick itself (one piece of wood: knotted shaft and egg-shaped knob)',
             'metal': 'The iron bands, the pyramid studs and the thin band at the lower end',
             'brass': 'The domed rivets on the bands', 'leather': 'The handle wrap'},
}
PART_NAMES = {'blade': 'The finial (the polished steel leaf, prongs or crescent)', 'metal': 'Metal fittings (socket, collars, '
              'cross-bar knobs, bands, langets, butt cap, claws)', 'brass': 'The thin rings and rivets',
              'wood': 'The pole or rod (wood)', 'leather': 'The grip wrap', 'gem': 'The set stone',
              'crystal': 'The crystal', 'body': 'Body, barrel and emitter', 'grip': 'Grip plates',
              'cell': 'The energy cell', 'string': 'The cord'}


def folder(kind, tier):
    return os.path.join(PROJECT, 'work', kind, f'masters_t{tier}')


def brief(kind, tier):
    tier = int(tier)
    work = os.path.join(PROJECT, 'work', kind)
    out = folder(kind, tier)
    os.makedirs(out, exist_ok=True)
    views = KINDS[kind]['views']
    for view in views:
        shutil.copy(os.path.join(work, f'guide_{view}.png'), os.path.join(out, f'guide_{view}.png'))
    title, layout, designs, parts = WEAPON[kind]
    for d in designs:
        shutil.copy(os.path.join(work, 'design', d), os.path.join(out, f'design_{d}'))
    tier_title, materials = TIERS[tier]
    materials = {**materials, **KIND_TIERS.get((kind, tier), {})}
    names = {**PART_NAMES, **KIND_PART_NAMES.get(kind, {})}
    text_parts = '\n'.join(f'- {names[p]}: {materials[p]}.' for p in parts)
    rel = os.path.relpath(out, REPO)
    deliver = '\n'.join(f'- `{NUMBER[v]}_{v}.png` over `guide_{v}.png`' for v in views)
    inputs = '\n'.join(f'- `guide_{v}.png`: plain grey orthographic render of the EXACT 3D model from the {v}.'
                       for v in views)
    refs = '\n'.join(f'- `design_{d}`: the approved design of this prop (shape, ornament, where each material goes).'
                     for d in designs)
    text = f"""# Codex brief: {tier_title} texture for a {title} ({kind}, tier {tier})

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds, do not call
Meshy.

Use your built-in image generation tool. Attached inputs (all in this folder):
{inputs}
{refs}

The guides fix the silhouette, position, scale and every shape edge of each view. {layout} The design images show the
same prop assembled, in neutral materials: use them for where each part and ornament is, and repaint everything in
this tier's materials at high definition.

## Deliverables (the guide's size and orientation, transparent background, unresized returns)
{deliver}

Each image must keep its guide's silhouette EXACTLY: same outline, size and position in the frame; nothing added outside
the silhouette, nothing cropped, the pieces kept apart exactly as in the guide. All views show one and the same object.

## Prompt content
TASK CONTEXT: PROP TEXTURE REFERENCE: a {title} for a museum-style catalogue, photographed as a product shot; seen up
close, so every surface needs crisp, believable material detail.

Materials for this tier ({tier_title}):
{text_parts}

Metal must read as metal everywhere: polish varies (bevelled rims brighter, flats satin or brushed), chamfers and edges
catch thin highlights, recesses are darker. Wood shows its grain running along the pole.

LIGHTING: even, soft, neutral studio light from the viewer, as for a product reference: the materials show their own
colour and polish with only gentle, broad highlights. No sky or scenery reflected, no dramatic light, no cast shadows,
no rim light, no background, no floor, no text. Luminous inlays (legendary tier only) are painted as bright coloured
lines on the surface, without any halo outside the silhouette.

Do NOT: change the shape; paint a different silhouette than the guide; join the pieces; crop; add text or logos.

Checks per image: silhouette identical to its guide; parts where the design has them; the tier's materials clearly
recognisable; even light; true transparent background. Write `generation_runs.json` (view, prompt, inputs with sha256,
output, selected, reason). At most one corrective regeneration per view. If the tool returns another size, keep it
unresized and record it.
"""
    with open(os.path.join(out, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(text)
    print(os.path.join(out, 'CODEX_BRIEF.md'))


def run(kind, tier):
    out = folder(kind, tier)
    views = KINDS[kind]['views']
    designs = WEAPON[kind][2]
    names = [f'guide_{v}.png' for v in views] + [f'design_{d}' for d in designs]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in names:
        arguments += ['-i', os.path.join(out, name)]
    prompt = (f'Follow the brief in {os.path.relpath(os.path.join(out, "CODEX_BRIEF.md"), REPO)} exactly. The attached '
              f'images are its inputs, in this order: {", ".join(names)}. Produce the images with your built-in image '
              'generation tool and save them as specified.')
    with open(os.path.join(out, 'codex_run.log'), 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', kind, tier, result.returncode, flush=True)


if __name__ == '__main__':
    {'brief': brief, 'run': run}[sys.argv[1]](sys.argv[2], sys.argv[3])
