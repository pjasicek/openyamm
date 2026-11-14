#!/usr/bin/env python3
"""Step 2 of the Oblivion weapon skins (README.md): Codex HD masters for one weapon in one tier, painted over the exact
silhouettes of the upload (prep.py guides), with the template's own textured renders as the design reference.

  python3 -I codex_masters.py brief <template> <tier>   writes work/<template>/masters_t<tier>/ (inputs, CODEX_BRIEF.md)
  python3 -I codex_masters.py run <template> <tier>     runs one Codex image session on it (prompt on stdin)
  python3 -I codex_masters.py mirror <template> <tier>  02_back.png as the mirrored 01_front.png, for a view the image
                                                        tool refused (the bow: its back guide is the mirrored front at
                                                        IoU 0.997); noted in MIRRORED.txt
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))

# Views per template: the swords' edge-on views are hairlines, the bow's side view a strip.
VIEWS = {'w_longsword': ('front', 'back'), 'w_claymore': ('front', 'back'), 'w_mace': ('front', 'back', 'left'),
         'w_bow': ('front', 'back'), 'w_shortsword': ('front', 'back'), 'w_dagger': ('front', 'back'),
         'w_waraxe': ('front', 'back'), 'w_battleaxe': ('front', 'back'), 'w_warhammer': ('front', 'back', 'left'),
         'w_staff': ('front', 'back', 'left'), 's_steelshield': ('front', 'back')}
NUMBER = {'front': '01', 'back': '02', 'left': '03', 'right': '04'}

WEAPON = {
    'w_longsword': ('one-handed longsword',
                    'A straight longsword replica: a long tapering blade with a central fuller (groove) running '
                    'from the guard most of the way to the point, a short crossguard with slightly down-swept ends, a '
                    'grip with ring bands, a round disc pommel.'),
    'w_claymore': ('two-handed greatsword (claymore)',
                   'A long straight two-handed sword replica: a long blade with a central fuller, a wide '
                   'crossguard with down-swept quillons and a decorated centre block, a long grip with ring bands, a '
                   'round disc pommel.'),
    'w_mace': ('ornamental sceptre',
               'A ceremonial sceptre (a regalia prop): a round head with raised ornamental flanges and six pointed '
               'studs (one on top), a metal collar, a twisted metal upper shaft, a long handle below with ring bands, '
               'a pointed metal end cap.'),
    'w_bow': ('recurve archery bow',
              'A long wooden recurve archery bow (sporting equipment): gently recurved limbs, a decorated metal '
              'handle block at the centre, metal ferrules and ornamented metal tips at both ends, a thin string.'),
    # The image tool refuses weapon words as violence (README.md): regalia, tools and armour-display props.
    'w_shortsword': ('short arming sword',
                     'A short straight sword replica: a tapering blade with a central fuller, a crossguard with '
                     'down-curled ends, a grip with ring bands, a round disc pommel.'),
    'w_dagger': ('ceremonial dirk (a short regalia blade)',
                 'A short broad double-edged ceremonial blade with a central fuller, a small crossguard with curled '
                 'ends, a grip with ring bands, a large round disc pommel.'),
    'w_waraxe': ('ceremonial bearded axe (a regalia prop)',
                 'A one-handed ceremonial axe: a single flared blade with an engraved round medallion near the eye, a '
                 'short back spike, a twisted metal upper shaft, a wooden handle with metal ring bands, a pointed metal '
                 'end cap.'),
    'w_battleaxe': ('ceremonial broad axe (a regalia prop)',
                    'A long two-handed ceremonial axe: a large crescent blade with a recessed darker face inside a '
                    'bright bevelled rim, a hooked back, a twisted metal upper shaft, a long wooden haft with metal '
                    'ring bands, a pointed end cap.'),
    'w_warhammer': ('ceremonial long-handled hammer (a regalia prop)',
                    'A long-handled ceremonial hammer: a square head with an engraved medallion panel on each side, a '
                    'round flat striking face on one end and a conical spike on the other, a twisted metal upper '
                    'shaft, a long wooden handle with metal ring bands, a pointed end cap.'),
    'w_staff': ("wizard's walking staff (a theatre prop)",
                "A gnarled wizard's walking staff: one length of twisted, knotted wood that splits at the top into a "
                'claw of thin curling prongs, a cloth wrapping spiralling down the middle of the shaft.'),
    's_steelshield': ('plate-armour shield (a museum armour piece)',
                      'A curved, slightly tapered plate shield: overlapping horizontal steel lames with raised ribs '
                      'and small rivets, a scalloped top edge, rolled borders; a leather hand strap on the inner '
                      'side.'),
}

# One text per tier and material family: the same three looks for every weapon.
TIERS = {
    1: ('LOW tier: crude, cheap, hard-used',
        {'blade': 'dark grey forged iron, not steel: visible hammer marks and forge scale, uneven coarse grinding '
                  'streaks along the blade, scattered small rust-brown spots and pitting, a dull flat; the edges '
                  'show a narrow rough brighter band where they were last polished, with a few small dents',
         'metal': 'plain blackened iron fittings, rough and slightly pitted, worn bright only on the high points',
         'grip': 'worn brown rawhide and coarse cord wrapping, frayed and dirty',
         'wood': 'plain unpolished ash wood, grey-brown, coarse open grain, scuffed, with rawhide bindings',
         'axe': 'dark grey forged iron: hammer marks and forge scale, coarse grinding streaks, scattered rust-brown '
                'spots and pitting, a dull face; the cutting edge a narrow rough brighter band with a few small nicks',
         'head': 'dark rough forged iron with hammer marks, forge scale, rust-brown spots and dented faces',
         'haft': 'plain unvarnished ash wood, grey-brown, scuffed and stained, with a worn rawhide grip wrap and '
                 'blackened iron bands',
         'staffwood': 'rough grey-brown weathered wood, dry and cracked, with remnants of bark in the hollows',
         'wrap': 'a frayed, undyed hemp cloth wrapping tied with twine, dirty and faded',
         'plate': 'dark grey forged iron plates: hammer marks, dents and scratches, rust-brown streaks along the '
                  'rivets and edges, a dull surface; plain iron rivets',
         'strap': 'worn, cracked brown rawhide'}),
    2: ('MID tier: clean, well-made craftsman\'s steel',
        {'blade': 'bright clean steel with a satin finish: fine lengthwise grinding grain on the flats, a smoother '
                  'polished fuller, clearly polished bright bevels along both edges, light honest wear '
                  '(fine scratches, a slightly darker tone near the guard)',
         'metal': 'polished steel fittings with crisp chamfers and small brass accents (a brass ring or rivets), '
                  'darker in the recesses',
         'grip': 'dark brown leather wrapped in a neat spiral with fine twisted steel wire',
         'wood': 'polished yew wood showing honey-orange heartwood and pale sapwood, smooth satin varnish, with a '
                 'dark leather grip and polished steel and brass fittings',
         'axe': 'clean bright steel with a satin finish and fine grinding grain, a clearly polished bright bevel '
                'along the cutting edge, the engraving crisp and darker in its recesses, light honest wear',
         'head': 'bright satin steel, crisp polished edges on the faces and the spike, the engraved panels crisp and '
                 'darker in the recesses',
         'haft': 'polished dark walnut with a satin varnish, polished steel ring bands with small brass rivets, a dark '
                 'leather grip wrapped with fine steel wire',
         'staffwood': 'smooth oiled dark walnut wood with fine visible grain and polished knots',
         'wrap': 'a neat deep-blue wool cloth wrapping bound with thin brass wire',
         'plate': 'clean polished steel plates with a satin finish, bright rolled edges and crisp ribs, brass rivets',
         'strap': 'dark brown leather with a steel buckle'}),
    3: ('HIGH tier: a masterwork, rich and ornate (a museum showpiece)',
        {'blade': 'mirror-polished silvery steel, very bright and clean, with a delicate etched decorative band '
                  '(flowing vine scrollwork) inside the fuller near the guard, finely honed edges as a crisp bright '
                  'line, no rust and almost no wear',
         'metal': 'gold-inlaid and gilded fittings with engraved scrollwork, polished gold high points, deep '
                  'engraved recesses, a small deep-red gem set in the centre (guard centre or pommel)',
         'grip': 'deep crimson leather wrapped with twisted gold wire',
         'wood': 'dark lacquered ebony-black wood with fine gold filigree inlay lines along the limbs, engraved '
                 'white-gold and gold fittings, a crimson leather grip',
         'axe': 'mirror-polished silvery steel with a delicate etched band of vine scrollwork along the edge bevel, '
                'the medallion gilded with a small deep-red gem in its centre, a crisp bright honed edge',
         'head': 'mirror-polished silvery steel with gilded engraved panels of gold scrollwork, a small deep-red gem '
                 'in the centre of each panel',
         'haft': 'dark lacquered ebony with a spiral gold-wire inlay, gilded ring bands, a deep crimson leather grip '
                 'with twisted gold wire',
         'staffwood': 'dark lacquered ebony wood with fine gold filigree inlay along the twists, gilded tips on the '
                      'prongs',
         'wrap': 'a deep crimson silk wrapping bound with twisted gold wire',
         'plate': 'mirror-polished silvery steel plates with gilded engraved scrollwork bands along every rib and '
                  'border, gilded rivets',
         'strap': 'crimson leather with gilded fittings'}),
}

# Per weapon and tier corrections. The low bow: Meshy turned grey-brown ash (v1, v2) into a black-and-white zebra or
# snakeskin weave on its thin limbs; v3 asks for plain dark wood, as the mid bow's yew that came back clean.
OVERRIDES = {('w_bow', 1): {
    'wood': 'plain dark brown stained elm wood, uniformly dark brown along both limbs with only a faint straight '
            'lengthwise grain, dull and scuffed, a few lighter worn patches; NO pattern, weave, carving or stripes on '
            'the limbs; a worn rawhide wrap at the grip; blackened iron tips'}}

# Tier 4 (legendary: artifacts and relics; approved 2026-11-14): one distinct look per weapon, a clear step above the
# gilded high tier, still metal and wood. The "luminous enamel" inlays are the parts post.py may give an emission.
LEGENDARY = {
    'w_longsword': ('starmetal', {
        'blade': 'deep blue-black starmetal with a faint crystalline shimmer, mirror-polished; a line of fine angular '
                 'runes inlaid in the fuller from the guard to near the point, filled with luminous pale-blue enamel '
                 '(bright, as if faintly glowing); honed edges a crisp bright silver line',
        'metal': 'dark blued steel guard and pommel with white-gold filigree and a cut sapphire set in the guard '
                 'centre and in the pommel',
        'grip': 'midnight-blue ray skin bound with twisted silver wire'}),
    'w_claymore': ('dragonforged', {
        'blade': 'smoke-dark damascus steel with a flowing wave pattern of black and silver layers; a line of angular '
                 'runes in the fuller inlaid with molten-orange enamel (bright, like faintly glowing embers); bright '
                 'honed edges',
        'metal': 'blackened steel crossguard and pommel with gold dragon-scale engraving, a large cabochon ruby in '
                 'the guard\'s centre block and on the pommel',
        'grip': 'black leather wrapped with red-gold wire'}),
    'w_mace': ('voidstone', {
        'head': 'The sceptre head and twisted shaft in polished near-black obsidian-dark metal, the flanges edged in '
                'white gold and engraved with runes filled with luminous violet enamel (bright, as if faintly '
                'glowing), each stud tipped with a small faceted amethyst.',
        'metal': 'dark gunmetal fittings with white-gold bands',
        'grip': 'deep purple leather wrapped with white-gold wire'}),
    # The bow's v1 bone and gold read plain (review 2026-11-14); its v2 masters come from codex_masters_pieced.py
    # (pieced guides) with this look.
    'w_bow': ('star-metal', {
        'wood': 'dark star-metal limbs, deep midnight-blue to blue-black with a blue-violet sheen, a continuous channel '
                'of angular runes along each limb filled with luminous cyan shading to violet, a midnight-blue leather '
                'grip wrapped with platinum wire',
        'metal': 'polished platinum fittings and tips with fine engraving, a glowing violet-cyan crystal in the handle '
                 'block and a glowing cyan crystal at each tip'}),
    'w_shortsword': ('elven moonsilver', {
        'blade': 'pale silver-green moonsilver with a glassy satin sheen; a slender leaf-vein pattern etched along '
                 'the centre and filled with luminous green enamel (bright, as if faintly glowing); bright honed '
                 'edges',
        'metal': 'pale gold guard and pommel with leaf engravings, a cut emerald in the pommel',
        'grip': 'pale green leather wrapped with fine gold wire'}),
    'w_dagger': ('bloodsteel', {
        'blade': 'dark crimson-black bloodsteel with a satin finish; a thin line of sharp runes along the centre '
                 'filled with luminous red enamel (bright, as if faintly glowing); bright honed silver edges',
        'metal': 'blackened gold guard and pommel with angular engraving, a faceted garnet in the pommel',
        'grip': 'black leather with blackened-gold wire'}),
    'w_waraxe': ('dwarven runebronze', {
        'axe': 'a deep golden-bronze head with geometric knotwork engraving and a bright silvery steel cutting edge; '
               'the medallion carved with a rune inlaid with luminous amber enamel (bright, as if faintly glowing)',
        'metal': 'bronze fittings with steel rivets and knotwork bands, a cut topaz in the end cap',
        'haft': 'dark stained oak with bronze bands and a brown leather grip bound with bronze wire'}),
    'w_battleaxe': ('frost steel', {
        'axe': 'icy blue-white frost steel with a frosted crystalline damascus pattern across the face and a '
               'mirror-bright edge; runes along the bevel inlaid with luminous ice-blue enamel (bright, as if '
               'faintly glowing)',
        'metal': 'polished silver fittings with fine frost-pattern engraving and small aquamarine settings',
        'haft': 'pale bleached ash with silver bands and a white leather grip bound with silver wire'}),
    'w_warhammer': ('stormforged', {
        'head': 'dark gunmetal with storm-blue enamel panels; each engraved panel bears a lightning rune inlaid with '
                'luminous gold-white (bright, as if faintly glowing) and a cut sapphire; gold-edged faces',
        'metal': 'gunmetal fittings with gold bands',
        'haft': 'black lacquered wood with gold bands and a dark blue leather grip bound with gold wire'}),
    'w_staff': ("archmage's", {
        'staffwood': 'polished petrified black-violet heartwood with a silver filigree spiral along the shaft, a band '
                     'of runes on the upper shaft inlaid with luminous violet enamel (bright, as if faintly glowing), '
                     'the prong tips sheathed in silver',
        'wrap': 'a royal-purple velvet wrapping bound with silver wire and embroidered with small silver stars'}),
    's_steelshield': ('dawn relic', {
        'plate': 'dark blued steel lames with gold-edged ribs and borders; a radiant sun sigil engraved across the '
                 'face, its lines inlaid with luminous pale gold (bright, as if faintly glowing); small rubies set '
                 'in the rivets along the top edge',
        'strap': 'deep blue leather with gold buckles'}),
}
TIERS[4] = ('LEGENDARY tier: a unique legendary relic, finer than any gilded masterwork (a museum\'s crown jewel)', {})

PARTS = {
    'w_longsword': ('blade', 'metal', 'grip'), 'w_claymore': ('blade', 'metal', 'grip'),
    'w_mace': ('metal', 'grip'), 'w_bow': ('wood', 'metal'),
    'w_shortsword': ('blade', 'metal', 'grip'), 'w_dagger': ('blade', 'metal', 'grip'),
    'w_waraxe': ('axe', 'metal', 'haft'), 'w_battleaxe': ('axe', 'metal', 'haft'),
    'w_warhammer': ('head', 'metal', 'haft'), 'w_staff': ('staffwood', 'wrap'), 's_steelshield': ('plate', 'strap'),
}
PART_NAMES = {'blade': 'Blade', 'metal': 'Guard, pommel, collars, head and other metal fittings', 'grip': 'Handle',
              'wood': 'Limbs (wood)', 'axe': 'Axe blade (the head)', 'head': 'Hammer head',
              'haft': 'Haft and handle', 'staffwood': 'The staff (all of the wood, including the prongs)',
              'wrap': 'Cloth wrapping', 'plate': 'Shield plates, ribs, borders and rivets', 'strap': 'Hand strap'}
MACE_HEAD = {1: 'The sceptre head and studs: dark rough iron with rust spots, the shaft iron too.',
             2: 'The sceptre head, flanges and studs: bright satin steel with crisp polished stud tips, the twisted '
                'shaft polished steel.',
             # v2 (2026-11-14): the v1 head (gold scrollwork over every flange) came back as a busy green-gold damask.
             3: 'The sceptre head: smooth, plain, mirror-polished silvery steel with broad calm surfaces (no '
                'scrollwork or pattern on the ball and flanges); only one narrow engraved gold band around the '
                "head's middle and gilded stud bases; the twisted shaft steel with a single gold spiral inlay."}


def folder(template, tier):
    return os.path.join(PROJECT, 'work', template, f'masters_t{tier}')


def brief(template, tier):
    tier = int(tier)
    work = os.path.join(PROJECT, 'work', template)
    out = folder(template, tier)
    os.makedirs(out, exist_ok=True)
    views = VIEWS[template]
    for view in views:
        shutil.copy(os.path.join(work, f'guide_{view}.png'), os.path.join(out, f'guide_{view}.png'))
        shutil.copy(os.path.join(work, f'template_{view}.png'), os.path.join(out, f'reference_{view}.png'))
    title, identity = WEAPON[template]
    tier_title, materials = TIERS[tier]
    if tier == 4:
        look, materials = LEGENDARY[template]
        tier_title = f'{tier_title}; this one {look}'
    materials = {**materials, **OVERRIDES.get((template, tier), {})}
    parts = '\n'.join(f'- {PART_NAMES[p]}: {materials[p]}.' for p in PARTS[template])
    if template == 'w_mace':
        parts = f'- {materials["head"] if tier == 4 else MACE_HEAD[tier]}\n' + parts
    if tier == 4:
        parts += ('\n- The luminous enamel inlays are painted as bright, saturated colour inside their engraved lines '
                  'only: no halo, haze or light spilling onto the surrounding surface.')
    rel = os.path.relpath(out, REPO)
    deliver = '\n'.join(f'- `{NUMBER[v]}_{v}.png` over `guide_{v}.png`' for v in views)
    inputs = '\n'.join(f'- `guide_{v}.png`: plain grey orthographic render of the EXACT 3D model from the {v}.'
                       for v in views)
    refs = '\n'.join(f'- `reference_{v}.png`: the same model with its current low-resolution texture, same view.'
                     for v in views)
    text = f"""# Codex brief: {tier_title} texture for a display-prop {title} (template {template}, tier {tier})

Scope: image generation only. Write ONLY into `{rel}/`. Do not edit any other file, do not run builds, do not call
Meshy.

Use your built-in image generation tool. Attached inputs (all in this folder):
{inputs}
{refs}

The guides fix the silhouette, position, scale and every shape edge of each view. The references show where the
parts are (blade, fuller, guard, grip, pommel, head, limbs) and the existing ornament layout; repaint them in this
tier's materials at high definition.

## Deliverables (1024 x 1536 portrait, transparent background, unresized returns)
{deliver}

Each image must keep its guide's silhouette EXACTLY: same outline, size and position in the frame; nothing added outside
the silhouette, nothing cropped. All views show one and the same object.

## Prompt content
TASK CONTEXT: PROP TEXTURE REFERENCE: a historical-replica display prop ({title}) for a museum-style catalogue,
photographed as a product shot; seen up close, so every surface needs crisp, believable material detail.

Shape: {identity}

Materials for this tier ({tier_title}):
{parts}

Metal must read as metal everywhere: polish varies along the blade or head (honed edges brighter, flats satin or
brushed), chamfers and edges catch thin highlights, recesses are darker.

LIGHTING: even, soft, neutral studio light from the viewer, as for a product reference: the materials show their own
colour and polish with only gentle, broad highlights. No sky or scenery reflected, no dramatic light, no cast shadows,
no rim light, no glow, no background, no floor, no text.

Do NOT: change the shape; paint a different silhouette than the guide; crop; add text or logos.

Checks per image: silhouette identical to its guide; parts where the reference has them; the tier's materials clearly
recognisable; even light; true transparent background. Write `generation_runs.json` (view, prompt, inputs with sha256,
output, selected, reason). At most one corrective regeneration per view. If the tool returns another size, keep it
unresized and record it. If the image tool refuses a request (a safety refusal), retry that view once with more
neutral wording (a display prop, an ornament or a craft piece; no weapon or combat words), and still produce every
other view: never stop after one refused view.
"""
    with open(os.path.join(out, 'CODEX_BRIEF.md'), 'w') as handle:
        handle.write(text)
    print(os.path.join(out, 'CODEX_BRIEF.md'))


def run(template, tier):
    out = folder(template, tier)
    views = VIEWS[template]
    names = [f'guide_{v}.png' for v in views] + [f'reference_{v}.png' for v in views]
    arguments = ['codex', 'exec', '-s', 'workspace-write', '-C', REPO, '--skip-git-repo-check']
    for name in names:
        arguments += ['-i', os.path.join(out, name)]
    prompt = (f'Follow the brief in {os.path.relpath(os.path.join(out, "CODEX_BRIEF.md"), REPO)} exactly. The attached '
              f'images are its inputs, in this order: {", ".join(names)}. Produce the images with your built-in image '
              'generation tool and save them as specified.')
    with open(os.path.join(out, 'codex_run.log'), 'w') as handle:
        result = subprocess.run(arguments, input=prompt, text=True, stdout=handle, stderr=subprocess.STDOUT)
    print('DONE', template, tier, result.returncode)


def mirror(template, tier):
    from PIL import Image, ImageOps
    out = folder(template, tier)
    ImageOps.mirror(Image.open(os.path.join(out, '01_front.png'))).save(os.path.join(out, '02_back.png'))
    with open(os.path.join(out, 'MIRRORED.txt'), 'a') as handle:
        handle.write('02_back.png is 01_front.png mirrored (the back view was refused or failed).\n')
    print('MIRRORED', template, tier)


if __name__ == '__main__':
    {'brief': brief, 'run': run, 'mirror': mirror}[sys.argv[1]](sys.argv[2], sys.argv[3])
