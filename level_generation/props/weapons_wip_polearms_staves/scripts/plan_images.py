"""Persist the remaining per-design imagegen briefs; execution uses the session's built-in image tool."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
MATERIALS = {
    '6trident5': 'Purple wraps with bright gold crossing braid, silver cuffs and gold ring fittings.',
    '7item032': 'Warm plain ash wood lower shaft, long dark steel upper socket, small silver bottom ferrule.',
    '7item033': 'Warm speckled tan wooden pole with small silver end ferrule and long engraved steel upper socket.',
    '7item034': 'Jet black wood with yellow gold ring collars and two dark grips crossed by gold braid; silver butt ferrule.',
    '7item035': 'Silver metal pole with chased yellow gold collars and lower gold spiral grip; dark orange tiny butt spike.',
    '7item037': 'Warm brown wooden haft with several close brown leather winding bands, small gold/brass collars and rounded butt.',
    '7item038': 'Tan perforated leather grip bands, exposed brown wood with small gold studs, dark steel cuffs.',
    '7item039': 'Plain brown wooden pole, worn dark steel upper socket and small dull steel butt cap.',
    '7item040': 'Slender grey-green STEEL shaft with little bright red ENAMEL bands and silver cuffs at the ends.',
    '7item041': 'Golden metal pole with diagonal gold ornamental grooves, dark narrow separator collars, yellow gold end fittings.',
    '7item225': 'Silver pole with gold end fittings, dark leather grips with gold crossed braiding and small dark separator bands.',
    '7item227': 'Gold metal upper pole, blue leather lower grip crossed with gold diagonal braid, blue gem collar and gold butt cap.',
    'halberd1': 'Red lacquered wood with silver strap along upper part, small gold studs, red grip bands and silver cuffs.',
    'halberd2': 'Brown wooden shaft with narrow brown leather wrap bands and gold ring collars, tiny blue enamel separators.',
    'halberd3': 'Brown wood with chased gold leaf inlay and silver studded upper straps; copper/gold butt fittings.',
    'item041': 'Dark knotted wooden fighting stick, tan cord bindings at top and bottom, rough wood grain; no painted metal shaft.',
    'item042': 'Rich amber wood with sparse small steel studs and silver butt ferrule; silver upper shaft segment.',
    'item043': 'Pale ivory-green stone inlay rod with green trailing vine pattern, dark gold narrow ring fittings.',
    'item044': 'Red lacquer with ornate gold vine filigree, green enamel separator rings and a gold butt cap.',
    'item045': 'Dark blue wrap with pale turquoise diamond lacing, dark brown grips with tiny gold diamonds, gold collars.',
    'item046': 'Plain warm wooden haft and lower olive-brown spiral leather grip, dark iron collar, rounded wooden butt.',
    'item047': 'Plain dark brown wooden shaft with tiny iron studs and brown spiral leather lower grip, dark iron ring collar.',
    'item048': 'Warm orange-brown wooden shaft with a dark brown spiral wrapped lower grip and dark iron ferrule.',
    'item049': 'Warm orange-brown wood, lower brown leather grip with horizontal segmented wraps, dark iron grip ring and brass butt.',
    'item050': 'Orange-brown wooden pole with broad brown lower leather horizontal wraps, dark iron collar and rounded butt.',
    'item051': 'Warm grained wood, lower salmon red leather grip with dark diamond lattice and silver/gold separator collars.',
    'item052': 'Rough tan wooden pole with dark brown cord binding at top and bottom; grain lengthwise, no metal except tiny fittings.',
    'item053': 'Ochre/brown wood and brown leather wrapping, a few silver cuffs and yellow gold short cross-binding marks.',
    'item054': 'Green leather wraps with vivid yellow gold crossed lacing, brown wood exposed at centre, silver cuffs and gold rings.',
    'item055': 'Royal blue wraps crossed with turquoise/gold diagonal lacing, narrow silver cuffs, gold rings and short brown wood sections.',
    'item243': 'Warm orange wood with small green diamond inlays outlined in gold, silver lower socket, ornate silver/gold collars.',
    'item244': 'Gold metal top grip, pale ivory woven leather with gold diamond net, red enamel separator bands, green inset and gold butt.',
    'spear1': 'Plain reddish brown wood with tan leather winding bands and small red enamel separators; silver short butt cap.',
    'spear2': 'Ornately chased warm golden-brown shaft, short dark brown lower grip, narrow copper/gold separators and green nonmetal butt gem.',
    'spear3': 'Olive green leather with narrow gold cross-lacing and broad green/gold diagonal spiral inlays at bottom, silver ring cuffs.',
    'spear4': 'Dark grey engraved steel upper segment and vivid RED tightly wrapped leather lower shaft, gold rings and silver ferrule.',
    'spear5': 'Pale silver rod with gold engraved lines, narrow orange/gold wire-wrap bands and silver separator collars.',
    'trident1': 'Teal blue lacquer with pale thin lightning veins, tan cord wrapping, turquoise enamel rings and gold narrow collars.',
    'trident2': 'Vivid red lacquer with fine gold vine filigree, narrow gold collars and small purple nonmetal butt gem.',
    'trident3': 'Deep purple wraps, gold crossed braid and spirals, silver cuffs and gold rings; silver butt ferrule.',
    '7item061': 'Plain naturally knotted brown wood with fine vertical bark fibres; entirely nonmetal.',
    '7item062': 'Brown wooden shaft with fine flowing gold filigree, gold metal collars and rounded gold butt.',
    '7item063': 'Muted old yellow brass pole segments with dark leather upper/lower grips dotted with fine gold studs, silver end cap.',
    '7item233': 'Plain yellow gold metal pole, lower dark grip crossed with gold braid, gold ring fittings and rounded gold butt.',
    'item079': 'Dark weathered wood, tan cord wraps around centre and at each end, sparse silver studs and silver end caps.',
    'item080': 'Warm tan carved wood with fine scroll marks and reddish-brown leather collar/grip bands, no metal on the main wooden pole.',
    'item081': 'Two red leather grip zones with tiny gold dots, dark blue lower/central shaft with fine turquoise inlay, gold collars and gold butt.',
    'item250': 'Dark blue shaft with warm gold wavy double-line inlay, brown wooden upper shaft and gold ring collars.',
    'staff1': 'Warm brown carved wooden shaft with delicate gold vine marks and short tan/brown leather wrap bands, gold upper socket and dark blue butt.',
    'staff2': 'Vivid red lacquer with fine orange-gold flowing grain, narrow steel/silver strap rings and small gold separator rings.',
}
MASTERS = {
    '7item063': 'A pale green crystal skull staff finial with an actual carved human skull inside the translucent green oval surface. Short narrow yellow gold neck collar only. Preserve the small stern skull, not a plain round ball; no full shaft.',
    '7item233': 'Ethric staff finial only: a small silver human skull in a gold pointed lozenge frame with two gold feather/leaf wings sweeping up around it, tiny blue top gem and narrow gold neck ferrule. Preserve the complete feather wreath and skull; no full pole.',
    'item050': 'Labyrinth Grapple polearm HEAD ONLY: long vertical silver spear in the middle, straight twin narrow silver prongs on the left with small saw teeth, crooked curled gold/ivory tentacle on the right, and tightly intertwined sculptural pale tentacles at the base. Include only the short attachment socket, not the long wooden shaft. Preserve the asymmetric design and open spaces between its prongs.',
    'item250': 'Staff of the Swamp TOP ASSEMBLY ONLY: red-orange/gold sun-like crossed circular magical crest, little dark leather/wood hanging flaps and chimes, small brown lattice-covered spherical rattle hanging to the left, narrow central golden neck and short brown attachment peg. Preserve the exact exotic arrangement in the source. No full long shaft or added decorations.',
    'item082': 'Complete Serpent Staff: thin straight dark gold segmented rod wrapped from bottom to top by ONE long green snake in a descending helical coil, with a large flared cobra hood at the top, yellow scaled throat, snake face looking toward viewer and short hooked tail at bottom. Preserve open spaces between snake coils and pole, real cylindrical rod and round snake body. Entire long staff, no extra snakes.',
    'item083': 'Complete Bone Staff: a long articulated ivory vertebral spine tapering toward the top, small lateral bony processes along its entire length, broad flared pale base, and a small elaborate bony head with two dark oval eye-like recesses and six thin curved rib processes projecting to each side. Preserve the source skeletal staff design precisely; not a human skeleton or animal creature. Entire long object.',
    'item242': 'Complete Spiritslayer polearm: narrow straight silver spear point at top with one curved silver hook sweeping right and short gold guard with green oval gem, long dark red-brown central haft with repeated sharp silver skeletal/barbed spine flanges all the way down, small ivory human skull above the bottom narrow silver spike. Preserve every large source component, the long slender shaft and ivory skull; entire long weapon.',
}


def main():
    designs = json.loads((HERE / 'designs.json').read_text())
    jobs = []
    for icon, description in MASTERS.items():
        folder = HERE / 'meshy' / ('pole_' + icon) / 'references_hd'
        whole = icon in ('item082', 'item083', 'item242')
        prompt = ('Use case precise-object-edit. Faithful HD 3D modelling reference of the supplied source item. '
                  + description + ' One front-biased three-quarter view with slight yaw, credible physical volume, '
                  'preserve the exact silhouette, proportions, materials, palette and distinctive fittings. '
                  'Soft neutral studio light, no strong reflections or shadows, true transparent empty background, '
                  'no floor, base, text or invented ornament. Full object visible with margin. '
                  + ('Portrait composition for the long slender object.' if whole else 'Square composition, finial fills the frame.'))
        jobs.append({'id': 'master_' + icon, 'kind': 'master', 'icon': icon, 'prompt': prompt,
                     'inputs': [str(folder / 'icon_detail.png')], 'output': str(folder / '00_three_quarter.png'),
                     'transparent': True})
    for name, design in designs.items():
        icon = design['master_icon']
        if icon in ('7item031', '7item036', 'staff3') or design['route'] == 'meshy_full':
            continue
        if design['geometry_group'] != icon:
            continue
        assert icon in MATERIALS, icon
        folder = HERE / 'textures' / icon
        prompt = ('Use case precise-object-edit. Create a game-model cylindrical shaft UV texture from Image 1 layout '
                  'and Image 2 design reference. One square texture split EXACTLY 50/50 vertically: LEFT half diffuse '
                  'albedo, RIGHT half matching BINARY METALLIC MASK, white for metal and black for wood, leather, '
                  'bone, cord, gems and coloured enamel. Never draw a weapon or cylinder: these are full rectangular '
                  'unwrapped texture surfaces. The head is excluded. Preserve exact horizontal band positions and '
                  'relative heights from Image 1, reconstructing fine ornamental detail from Image 2 across the '
                  'complete width. ' + MATERIALS[icon] + ' Wood grain must run VERTICALLY lengthwise. The left/right '
                  'edges of the albedo half join seamlessly. Flat matte diffuse pigment only: REMOVE original painted '
                  'lighting, no highlights, reflections, shading, shadows, AO, gradients, shine, glow, borders, '
                  'labels or text. Do not brighten or darken the rectangle edges. The right mask matches the left '
                  'art pixel for pixel, with red/blue/green enamel black, not metal. Fill the square edge to edge, '
                  '1024x1024, exact equal vertical halves, opaque texture-data background.')
        jobs.append({'id': 'uv_' + icon, 'kind': 'uv', 'icon': icon, 'prompt': prompt,
                     'inputs': [str(folder / 'shaft_uv_template.png'), str(ROOT / 'assets_dev/engine/icons_x2' / (icon + '.png'))],
                     'output': str(folder / 'shaft_uv_painted.png'), 'transparent': False})
    path = HERE / 'generation_jobs.json'
    path.write_text(json.dumps(jobs, indent=2) + '\n')
    assert len({j['id'] for j in jobs}) == len(jobs)
    print(len(jobs), 'remaining image jobs, including', len(MASTERS), 'sculptural masters')


if __name__ == '__main__':
    main()
