"""Prepare configured MM7 native families from descriptor-resolved native artwork."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
from PIL import Image
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / 'sprites'))
from inventory import frame_images

CONFIGS = {
    'mm7_m254': dict(label='Golem A', creature='golem', base_palette=255,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm254sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original Egyptian pharaoh golem: lean muscular metallic gold and bronze '
        'humanoid statue, small stern gold human face, smooth gold exposed chest, abdomen, arms and legs, '
        'warm pale gold highlights and very deep brown-black metal shadows. Flat-topped close-fitting '
        'nemes headdress with narrow gold rim, two short ivory side horns, and hanging fabric lobes '
        'striped dark near-black forest green and muted pale mint-green. Small matching striped false '
        'beard. Broad rounded black shoulder collar with two rows of small gold studs, black wrist '
        'cuffs with gold trim and narrow black ankle cuffs. Short rectangular striped green loincloth '
        'panels hang from the gold waist belt at front and back; preserve alternating horizontal '
        'near-black green and muted mint stripes, folds and exact native panel lengths. Bare gold '
        'human feet and bare gold hands. Preserve the narrow head, native muscular proportions, '
        'horn size, exact empty-hand poses and bent knee motion. Only the two cloth stripe colors '
        'change in native palette variants; gold metal body, ivory horns and black collar and cuffs '
        'stay unchanged. No weapon, shield, cape, hair, pedestal, glow, added ornament or redesign.'),
    'mm7_m250': dict(label='AGog A', creature='gog', base_palette=613,
        palette_paths={str(p):f'assets_dev/worlds/mm8/textures/PAL{p}.act' for p in [613,614,615]},
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm250sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original green reptilian gog monster: lean upright biped, small angular '
        'reptile head with short projecting muzzle, narrow yellow eyes, pale pointed teeth and small '
        'chin spike. Two long ivory-gray horns sweep outward and upward from the sides of the crown, '
        'with a thin pointed central crest. Large pointed green ear fins, textured emerald-green '
        'scales, muted mint highlights and deep near-black green shadows. Muscular shoulders, long '
        'bent arms, large open clawed hands with pale horn-colored nails, lean long legs and three '
        'large splayed clawed toes. Thin long green tail with pointed dark spade tip curls behind '
        'the legs; preserve its exact native curve and the rear ankle spur. Dark overlapping curved '
        'back plates form a narrow ridge with pale horn spikes along the upper back and shoulders. '
        'Small pale silver-green scaly chest highlight and dark segmented belly, no clothing or '
        'armor. Preserve the native small head, long slender limb proportions, narrow waist, claw '
        'poses, ivory horns and very dark tonal weight. In casting poses copy only the exact native '
        'fire or sparks and their original positions. Green hide changes offline to blue and red; '
        'horns, claws, teeth and eye details remain protected. No weapons, wings, added accessories, '
        'invented effects, extra limbs or redesign.'),
    'mm7_m246': dict(label='Goblin A', creature='goblin', base_palette=248,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm246sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult male green-skinned goblin warrior: lean muscular upright body, '
        'long bare green arms, small stern angular face, pointed green ears, narrow yellow eyes and jutting '
        'lower teeth. Olive-green skin with yellow-green highlights and deep forest shadows. Tall narrow '
        'ornate brass helmet with a swept-back brown-gold segmented crest, brass brow rim and small '
        'side spikes; thin reddish brown hair extends below the helmet at the back. Sleeveless close-fitting '
        'muted blue-teal vest with deep V neckline and fine gold edge trim, dark diagonal shoulder strap. '
        'One heavy spiked brass pauldron on his left shoulder and ornate brass segmented armor down '
        'his left arm; right forearm has a dark blue cloth bracer with gold trim. Bare green hands hold '
        'the native single long slightly curved broad silver blade diagonally across his waist, right '
        'hand at the small gold hilt. Blade has a rusty red-brown center line and bright silver edge; '
        'preserve exact length, curvature, grip and angle in every pose. Dark navy-blue fitted trousers '
        'with brown leather bands at knees and native gold studded side details. Brown knee-high '
        'leather boots with pointed brass spiked shin guards visible from the front. Brass waist belt, '
        'thin gold hanging side straps and dark rear harness exactly as native. Keep skin, hair, brass, '
        'steel and brown boots unchanged; only blue-teal vest and dark navy trousers/bracer recolor '
        'separately to their native variants. No shield, cape, extra weapon, glow or redesign. Preserve '
        'the native slender proportions, dark tonal weight and asymmetric armor.'),
    'mm7_m242': dict(label='Ghost A', creature='ghost', base_palette=244,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm242sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original floating skeletal ghost, in its native dark brown robe palette. '
        'A small narrow yellowed ivory skull with deep black eye sockets, dark nasal cavity, small '
        'exposed teeth and no glowing eyes. Thin pale yellow-green aged bones form the neck, exposed '
        'upper rib cage, forearms and very long fine fingers; match each native finger curl and hand '
        'pose, with empty hands. The skull sits inside a close-fitting dark brown hood with a soft '
        'rounded crown and a small swept-back point visible in profile. Broad sloping shoulders, '
        'a short torn shoulder cape and long loose ragged brown sleeves surround the slim skeletal '
        'body. The robe is worn coarse dark umber cloth with muted brown-gray highlights, deep '
        'near-black vertical folds, mottled threadbare texture, long thin torn strips at the sleeve '
        'and lower hem, and irregular angular pointed edges. The robe tapers beneath the floating '
        'body; no visible feet, boots or leg bones, no floor shadow, smoke or mist. Preserve all '
        'native robe tears and the pointed profile silhouette. In standing poses both bent skeletal '
        'arms are held near the waist across the front. Attack raises the empty long-fingered hands; '
        'falling poses crumple the robe and separate only the native skeletal hand pieces. Preserve '
        'the small skull, narrow profile, robe width, native hand anatomy and deeply shaded tonal '
        'weight. Cloth recolors offline to gray-white and black; skull, ribs and hand bones stay '
        'yellowed ivory. No weapon, scythe, chain, belt, jewelry, extra bones, added aura or redesign.'),
    'mm7_m238': dict(label='Genie A', creature='genie', base_palette=239,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        core_magenta_tolerance=8, protect_warm_contours=True,
        batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm238wa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult female blue genie: slim upright humanoid upper body with '
        'smooth medium cobalt-blue skin, pale cool blue highlights and deep navy shadows, narrow angular '
        'face, small pale eyes, straight nose and stern closed mouth. Dark cobalt hair swept tightly into '
        'a high upright curved ponytail, divided by thin gold rings down its back-hanging length, with a '
        'small gold tip. Thin gold circlet with a small central orange-gold forehead jewel and small pointed '
        'gold side ornaments. Small gold earrings. Rich emerald-green high collar, short fitted sleeveless '
        'bust garment with thin bright gold lower edging, and matching wide green wrist cuffs. Bare blue '
        'arms, shoulders, midriff and back match native coverage. In idle poses the arms are crossed firmly '
        'at chest height. Below the waist there are no legs: the body blends into one long tapering '
        'blue-white swirling mist vortex, with sparse delicate cyan speckles at its ragged outer boundary, '
        'ending at a narrow pointed tip. Preserve the exact native swirl shape and very fine soft edges; '
        'do not make a solid skirt, snake tail, water splash, broad aura or extra particles. In casting '
        'poses copy only the precise native white-gold star sparks and their positions around the hands. '
        'In disappearance poses copy the native pale blue-white smoke puffs and tiny final gold oil lamp '
        'with blue lid. Preserve slender proportions, small head, native blue skin, green cloth, gold '
        'trim and dark tonal weight. Only green garment, collar and wrist cuffs change palette. No '
        'weapons, extra jewelry, added clothing, enlarged bust, glow halo or environment.'),
    'mm7_m234': dict(label='Gargoyle A', creature='gargoyle', base_palette=235,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm234sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original stone gargoyle monster: compact lean muscular biped with '
        'cool slate-gray and blue-violet stony hide, pale gray mottled highlights across the face, '
        'upper chest, shoulders and front thighs, and deep navy-purple shadows. Narrow elongated '
        'goat-like reptilian muzzle with pointed chin, stern brow, two tiny bright red eyes, pointed '
        'side ears and two thick dark-gray horns curling backward in tight arcs beside the crown. '
        'Long bent arms with thin bony clawed fingers, muscular haunches, bent knees and narrow '
        'ankles ending in long splayed clawed toes, not hooves. A very thin long dark-gray tail '
        'extends from the lower back and ends in a small flattened spade; match its curve in each '
        'native view. Two separate bat wings grow from the shoulder blades, dark charcoal-gray '
        'skeletal struts with little hooked top joints and rich dark leaf-green thin membranes, '
        'mottled vein-like stony texture and deeply scalloped lower margins with long thin wing '
        'finger tips. Preserve the native folded or spread wing outline, individual finger struts '
        'and body occlusions in every frame. It is a carved living stone beast, with no clothing, '
        'armor, accessories, weapon, hair or added anatomy. Preserve native head size, slender '
        'waist, large thighs, long hands and wing proportions. Only the green wing membranes are '
        'recolorable; stone body, horns, claws, tail and small red eyes retain their native colors. '
        'No added glow, particles, rubble, pedestal or environment.'),
    'mm7_m226': dict(label='Fighter Leather A', creature='leather_fighter', base_palette=52,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm226sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult male leather-armored fighter: tall slim athletic build, '
        'pale skin, stern narrow angular clean-shaven face, dark brown-black slicked hair in a long '
        'low ponytail tied with a green band. Fitted deep leaf-green long-sleeved leather jacket '
        'with upright green collar, silver-gray central clasp and dark diagonal leather chest strap. '
        'Broad dark brown leather shoulder yoke with narrow bright silver piping around its curved '
        'lower edge and small silver studs along the shoulder ridge. Native silver studs and dark '
        'crisscross laces down the outer green sleeves. Dark brown wrist bracers, bare hands. Wide '
        'dark leather waist belt with silver fittings and buckle. Ochre-brown fitted leather trousers '
        'with dark side lacing and a small green laced panel on his left front thigh. Ochre leather '
        'sheath and straps at the right hip, matching the source. Knee-high black leather boots with '
        'small brass buckles and silver-gray laced shin fronts, dark toes. One broad curved silver '
        'falchion in his right hand, with two small triangular hooks/notches on the inner blade near '
        'the pointed tip, short brass-and-dark hilt. Match each native blade angle, handedness and '
        'foreshortening. Preserve the narrow dark diagonal back equipment silhouette exactly. '
        'Keep green jacket, collar, hair tie and small thigh panel distinct from unchanged brown '
        'pants, dark leather shoulders, boots, hair, skin and steel. No shield, cape, helmet, '
        'extra weapon, glow or added ornament. Preserve native slender proportions and dark tonal weight.'),
    'mm7_m222': dict(label='Fighter Chain A', creature='chain_fighter', base_palette=223,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm222sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult female chain-armored fighter: tall slim athletic build, '
        'pale skin, stern narrow face, straight medium brown shoulder-length hair. Dark steel rounded '
        'helmet with a small brown upright crest and brass forehead rim. Dark silver-blue chainmail '
        'short-sleeved cropped chest armor over deep green cloth at the V neckline, upper sleeves '
        'and waist; preserve the native small bare midriff and chainmail briefs. Brass-gold rounded '
        'shoulder plates, brown leather long forearm bracers and gloves. Two long ornate gold linked '
        'draped panels hang down the front thighs from the belt, with native chain loops across the '
        'hips and back. Dark navy-black thigh-high boots with brass thigh bands and segmented silver '
        'shin plates separated by dark straps, small silver toe caps. Bare upper rear thighs exactly '
        'as in the reference, no additional exposure. A single curved bright silver scimitar with '
        'brass hilt in her right hand; preserve the narrow curved blade and exact native angle and '
        'foreshortening in each pose. Brown and dark blue diagonal scabbard with brass fittings '
        'across her back. Preserve all straps and material placement. Keep the green cloth distinct '
        'from silver chainmail, gold armor, brown leather and skin for selective native palette '
        'variants. No shield, cape, extra sword, large plume, glow or added ornament.'),
    'mm7_m218': dict(label='Elf Spearman A', creature='elf_spearman', base_palette=220,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm218sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult male woodland elf spearman: tall slender lightly muscular '
        'build, long slim legs, pale gray-pink skin, narrow stern angular face, pointed ears and dark '
        'brown-black hair swept back to the nape. Two thin branching green leafy sprigs rise from '
        'either side of the head, forming the native small asymmetric foliage crown. Bright green '
        'leafy vines wind diagonally around the bare chest, shoulders, arms and legs; preserve each '
        'native leaf cluster and yellow-green highlights. A short dark blue-violet loincloth of '
        'narrow pointed overlapping fabric tabs hangs from a thin brown waist belt, with green '
        'vines crossing the waist above it. Brown leather forearm bracers with green vine accents. '
        'Bare feet. He carries the exact native long thin dark ochre-brown wooden spear, with small '
        'pale silver pointed tip and subtle green-brown accents; copy its length, direction and '
        'hand grip from every native frame. Preserve the native diagonal shaft visible behind '
        'the back and its exact occlusion. No bowstring, bow, shield, cape, armor, extra weapons, '
        'added jewelry or glow. Preserve native sparse foliage coverage, long limbs, dark hair, '
        'pale skin, cool deep shadows and slender silhouette. Keep blue-violet loincloth clearly '
        'separate from green vine foliage for deterministic offline palette variants.'),
    'mm7_m214': dict(label='Elf Archer A', creature='elf_archer', base_palette=216,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm214sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original adult female elf archer: tall slender athletic build, long slim '
        'legs, pale pink-gray skin, stern narrow face and pointed ears. Short straight silver-white '
        'hair lies close to the head, parted at front and reaching the nape. Rich dark leaf-green '
        'sleeveless fitted leather vest with narrow ivory-white piping around all edges, open in a '
        'long narrow central V, fastened by two slim horizontal brown leather buckle straps across '
        'the waist. A small bare midriff below the vest. Matching dark green close-fitting trousers '
        'end above the ankles, with native brown crisscross lacing along the outer lower calves, '
        'ivory piping at the waist, and small dark leather thigh straps and pouch. Bare feet with '
        'clearly defined toes, no boots. Brown leather forearm bracer on the bow arm. Left hand '
        'holds a thin dark brown recurved bow with fine pale taut string, narrow gold bands and '
        'pointed ends. Right hand is empty when standing; use exact native draw and arrow poses '
        'during shooting. A long narrow brown leather quiver lies diagonally across the back, '
        'with raised gold-brown winding ornament, small red studs and pale gray-white arrow '
        'fletchings above the shoulder. Preserve exact bow/string geometry, quiver placement, '
        'silver hair, white piping, native green garments, slender proportions and deep shadows. '
        'No cape, armor, extra weapons, added accessories, glow or costume redesign. Keep material '
        'boundaries clear for deterministic offline variants.'),
    'mm7_m190': dict(label='Dwarf A', creature='dwarf_warrior', base_palette=191,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm190sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original short broad adult male dwarf warrior: muscular stocky body, '
        'short sturdy legs, tan ruddy skin, broad stern face with large nose, and a very long straight '
        'ochre-brown beard divided into narrow pointed locks hanging to the belt. Matching long brown '
        'hair behind the head. Dark steel domed helmet with thin brass rim, a short central ivory '
        'spike and two tall upward-curving ivory side horns. Dark polished blue-gray plate breastplate '
        'and broad rounded shoulder armor, short fine silver chainmail sleeves and chainmail skirt '
        'over green cloth; preserve native ragged green rectangular hem tabs and small green shoulder '
        'collar. Thick brown waist belt with brass buckle; short brown leg coverings, exposed tan '
        'knees, dark steel greaves with narrow brass upper rims, dark pointed boots. Heavy dark '
        'metal forearm guards with brass rims and small studs. Right hand holds the native short '
        'double-bladed silver battle axe with curved crescent cutting edges, brown shaft, brass '
        'collars and curled brass grip ornament. Left hand is empty and loosely clenched. Preserve '
        'the exact axe orientation, occlusion, horn profile, chainmail pattern, beard length, original '
        'body proportions and dark tonal weight. No shield, cape, extra weapons, added insignia, '
        'jewelry, glow or costume redesign. Only native green cloth changes to blue and muted red '
        'through offline variants; protect brown beard/hair, skin, chainmail, steel, ivory and brass.'),
    'mm7_m182': dict(label='ADragon A', creature='dragon', base_palette=183,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm182sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact original flying dragon: slender long-necked dark forest-green scaled body, '
        'small elongated angular reptilian head with narrow toothy muzzle, fine ivory teeth, tiny bright '
        'eyes, and the native swept-back ivory horns and gold-green cheek spines. A narrow segmented '
        'golden-yellow ventral plate strip runs from throat down the belly. Two short forearms extend '
        'forward with small pale hooked claws; two larger bent hind legs hang tucked below the torso. '
        'A long tapering green tail sweeps backward with small gold-green dorsal spines and thin gold '
        'forked fins near its tip. Two enormous angular bat-like wings rise from the upper back, with '
        'long dark green pointed spars and broad triangular pale silvery green membranes, densely '
        'mottled olive-gold and gray, shaded almost black on their undersides. Preserve each native '
        'wing projection, folded overlap, tapered point and dark underside; do not invent feathers. '
        'Keep the native fine dorsal spines, long thin neck, small head, compact torso, tucked legs, '
        'long tail and dark shaded scales. No clothing, armor, accessories, riders, added horns, '
        'flames, smoke, aura or redesign. Native blue and red variants will be derived offline; '
        'preserve clear boundaries between green scales, silvery membranes, gold belly and pale horns.'),
    'mm7_m178': dict(label='Devil A', creature='devil', base_palette=44,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm178sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The exact native wingless long-armed devil creature: lean muscular ochre-brown '
        'pebbled hide, narrow waist, bent digitigrade legs and enormous low-hanging clawed hands with '
        'long separated bony fingers and ivory-gray hooked talons. Broad dark slate-violet plated '
        'chest and abdomen, matching dark slate tops of feet and pale short toe claws. Small broad '
        'reptilian head with a toothy horizontal mouth, pale fine teeth, pointed ears and brilliant '
        'yellow eyes with tiny pale centers. Preserve the exact native short head horns and long '
        'ivory-gray spikes rising behind the head and shoulders; several shorter spikes follow '
        'outer forearms, lower legs and the upper curve of the long thin tail. Preserve the native '
        'tail length, curled orientation and small spear-shaped tip, rough brown hide, dark chest, '
        'long forearms and disproportionately large hands. No wings, weapons, clothing, armor, '
        'extra horns or ornamental redesign. Keep the creature fully nonhuman and follow every '
        'native pose, silhouette and claw placement. Native green-teal and red hide variants will '
        'be derived offline, protecting gray chest plates, ivory spikes, claws, teeth and yellow eyes.'),
    'mm7_m174': dict(label='Cleric Sun A', creature='sun_cleric', base_palette=40,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm174sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original tall adult male sun cleric in his exact ceremonial costume: a polished '
        'gold face mask with narrow dark eye openings and solemn sculpted mouth; thin uneven wavy gold '
        'sun rays project radially above and beside the head, preserving each native ray. Gray close-fitting '
        'head covering with dark horizontal straps is visible behind the mask. A stiff high scarlet collar '
        'flares beside the neck. A short broad gold-orange shoulder mantle hangs to the elbows and waist, '
        'with dense narrow flowing wavy gold ridges, divided at front and back by a narrow vertical red '
        'center opening. These are sculpted or embroidered wavy surfaces, not feathered wings. Long slim '
        'scarlet floor-length robe with alternating thin ochre-gold vertical stripes and heavy shaded '
        'folds; feet hidden. A narrow gold waist belt has a square turquoise-green central buckle. A long '
        'pointed dark teal-green front hanging stole has narrow gold edging and the exact native small '
        'gold square/dot ornaments. Bare tan forearms and empty tan hands, smooth pale gold wrist cuffs. '
        'Keep the native bright gold and scarlet colors, deep shadows, narrow body, long robe, exact '
        'sun-ray silhouette, cloth folds and hand gestures. No weapons, staff, shield, added ornaments, '
        'new symbols, halo, aura or glow. Only retain golden particles in native action/death cells that '
        'contain them; no particles in standing or walking. Palette variants affect only the teal '
        'front stole and matching buckle; protect all gold, scarlet cloth, skin and gray head covering.'),
    'mm7_m170': dict(label='Cleric Moon A', creature='moon_cleric', base_palette=37,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm170sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original tall slender moon cleric: gaunt pale gray adult male face, narrow dark '
        'eyes and long gray fingers with dark joints, black shoulder-length hair visible under a small '
        'ornate gold crown with a domed center and short pointed side peaks. A heavy black neck collar '
        'has narrow radial gold bars and a gold pendant. Long rich dark leaf-green robe with loose '
        'sleeves, draped folds across the chest, thin gold hem and side trim, and a thin gold waist cord '
        'tied in front with two hanging ends. Feet remain hidden by the floor-length robe. Behind the '
        'shoulders is the distinctive high crescent-shaped engraved gold ceremonial collar, its two '
        'tips rising well above the head; long near-black olive-green fabric panels hang vertically '
        'from the tips to the waist, edged above by thin gold cords and small turquoise triangular '
        'tassels. These are hanging fabric panels, not feathered wings. Preserve exact native collar '
        'geometry, panel folds, hand gestures, slender body, gray complexion and dark tonal weight. '
        'Hands are empty; retain only the native small golden spell particles in action cells that '
        'contain them. No staff, weapon, shield, new symbols, added aura or costume redesign. Native '
        'robe and hanging-panel palette variants will be derived offline; protect gold ornament, '
        'turquoise tassels, hair, gray face and hands, and golden spell particles.'),
    'mm7_m154': dict(label='Archer A', creature='archer', base_palette=155,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm154sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult male archer: stern dark tan-brown clean-shaven human face beneath '
        'a small domed dark steel helmet with a narrow brass rim, short central spike and two small '
        'upcurved ivory side horns. Silver-gray chainmail coif covers the neck and back of the head; '
        'dark gray fine chainmail sleeves cover the arms beneath a plain short green-teal tabard. '
        'Preserve the exact native large white heraldic bird emblem across the chest, its outspread '
        'wings and descending tail, partially crossed by a brown diagonal quiver strap. Bright muted '
        'brass-gold gorget, small dark steel shoulder plates with brass edging and visible studs, '
        'plain brown waist belt with round brass buckle. Ochre-brown fitted trousers and tall plain '
        'brown leather boots; preserve original native cuff seams and coverage. The right hand holds '
        'the curved dark brown wooden bow with a fine pale bowstring, at the exact native angle. '
        'The left hand has an ochre leather glove and is empty except in native arrow-handling poses. '
        'A brown leather arrow quiver lies diagonally across the back with several thin pale shafts '
        'and white-gray feather fletchings projecting above the shoulder. Preserve native proportions, '
        'dark tonal weight, tabard green, brown leather and simple practical materials. No sword, '
        'shield, cape, extra ornaments, glow or costume redesign. Native cloth palette variants will '
        'be derived offline; keep the white emblem, armor, skin, leather, arrows and bow protected.'),
    'mm7_m150': dict(label='Angel A', creature='angel', base_palette=151,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm150sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original armored male angel warrior: stern tan human face, dark shoulder-length '
        'hair beneath an ornate gold-brass helmet with the native raised curled crest and small side '
        'ornaments. Muscular bare tan upper arms, fitted dark polished blue-gray steel torso armor with '
        'gold-brass scroll-shaped rims, dark metal forearm guards, dark fitted leg coverings and tall '
        'steel shin armor with gold-brass borders. Short dark green cloth skirt panels alternate with '
        'brown leather hanging tabs and small gold chain details. The right hand holds a long thin '
        'silver wavy flamberge sword with gold crossguard and dark grip; preserve every bend in the '
        'native blade. The left arm carries the native small elongated dark bronze kite shield with '
        'brass studded rim. Two large feathered wings extend from the upper back, pale silvery lavender '
        'upper feathers and deep navy-violet undersides, layered long flight feathers and bright pale '
        'upper leading edges. Preserve exact wing spread, folds, occlusion, feather direction and '
        'native asymmetry in every pose. Preserve the original dark tonal weight, long legs, tan skin, '
        'green skirt, dark armor and restrained metallic highlights. No halo, glow, invented jewelry, '
        'cape, extra weapons, symbols or costume redesign. Native skirt palette variants will be '
        'derived offline; keep wings, skin, armor, leather, gold and cloth material boundaries clear.'),
    'mm7_m398': dict(label='Skeleton Warrior A', creature='skeleton_warrior', base_palette=63,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm398sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original armored skeletal warrior: bare aged ochre-ivory skull with hollow dark '
        'eye sockets and exposed teeth, a small rounded dark steel helmet with a narrow brass band and '
        'short top spike. Thin exposed rib and limb bones, dark battered steel breastplate with muted '
        'gold-brass border, dark metal forearm gauntlets and shin greaves with brass rims, and tattered '
        'faded blue-violet short trousers. Preserve the native rusty red streaks and ragged damage on '
        'armor and cloth. The right hand holds the original short straight silver sword with small '
        'crossguard and rusty red blade marking; left hand is empty. Preserve the thin arrows lodged '
        'through the torso and projecting behind the shoulders, their pale feather fletching and exact '
        'native placement in each view. Long slender legs, narrow body, worn tarnished surfaces and '
        'heavy dark native tonal weight. No living skin, eyes, extra weapons, shield, cape, jewelry, '
        'glow or invented ornaments. Keep native armor, bone, cloth and metal material boundaries '
        'clear for offline native palette variants; preserve the exact native damage without adding any.'),
    'mm7_m402': dict(label='Spider A', creature='spider', base_palette=66,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm402sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original low broad fantasy spider: eight long angular jointed near-black charcoal '
        'legs with narrow gray upper-surface highlights, deep crimson-red distal segments, small black '
        'downward serrations on those red segments, and tiny pale ivory hooked tips. Preserve each native '
        'leg position and projection, including raised forward legs. Small black rough-textured head and '
        'thorax with clustered bright yellow eyes, short red mouth details and dark pointed mandibles. '
        'A large smooth rounded glossy very dark emerald-green abdomen sits behind the head, with the '
        'native broad pale silver-white upper highlight and deep teal underside shadows. Preserve the '
        'compact body and long thin limbs, heavy near-black tonal weight, original material colors and '
        'all occluded leg projections. No human features, clothing, armor, accessories, web, glow, '
        'cast shadow, extra legs or invented markings. Only native abdomen palette variants will be '
        'derived offline; preserve distinct shell, black legs, crimson lower legs, ivory tips and eyes.'),
    'mm7_m186': dict(label='Dragonfly A', creature='dragonfly', base_palette=187,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm186wa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original serpentine fantasy dragonfly: a long thin S-curved segmented brown-gray '
        'armored insect body hanging vertically in flight, with pale beige belly plates edged dark reddish '
        'brown, bright green narrow spines along the back of the upper body, and a small hooked insect '
        'head with large round orange-red compound eyes. Dark pointed snout and small pale silver-white '
        'mandibles, fine ochre whisker-like mouth bristles. The tail ends in paired long narrow tan-gold '
        'pointed prongs and small pale silver hooked side spurs. Thin paired translucent-looking pale '
        'gray wings with dark red-brown veins attach near the upper curved body and sweep horizontally '
        'in the native flight pose; preserve the native wing count and exact projected width and angle. '
        'Wings may appear edge-on or hidden in profile. Keep the original narrow silhouette, dark '
        'segment shadows, light plate highlights and small head. No legs, arms, human face, bat wings, '
        'clothing, ornaments, glow, cast shadow or invented appendages. Native palette variants will '
        'be derived offline; keep spine, shell, wing, eye and jaw material boundaries clear.'),
    'mm7_m166': dict(label='Beholder A', creature='beholder', base_palette=167,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','a','n'],
        identity_frames=[f'm166wa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original floating beholder: an irregular dark brown leathery ridged head with a '
        'large central vivid green eye under heavy folded brown eyelids. Four short thick curved stalks '
        'around the upper head end in small green eyes with pale ivory rims. A narrow open mouth beneath '
        'the central eye has small ivory teeth and a reddish interior, with thin ochre-gold hanging strands '
        'beneath the jaw. Several long slender dark gray tentacles descend and spread from the underside, '
        'ending in tapered vivid green tips. Preserve the exact native tentacle count, paths and lengths '
        'in each view, the heavy dark brown head, small stalk eyes and dark tonal weight. No legs, hands, '
        'wings, horns, clothing, armor, invented jewelry or extra appendages. Green tentacle tips change '
        'through native palettes; eyes, brown head, dark shafts, teeth and ochre strands stay protected. '
        'Preserve every thin feature with clear material boundaries.'),
    'mm7_m352': dict(label='Peasant Human1 MaleA A', creature='human_male_peasant_1', base_palette=353,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','n'],
        identity_frames=[f'm352sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult human male peasant: fair tan skin, stern ordinary face, straight '
        'near-black shoulder-length hair combed back, near-black moustache and short full beard. Plain '
        'dark forest-green long tunic with round close neckline, loose elbow-length sleeves, small pale '
        'brass studs around the sleeve cuffs, straight rectangular cut tabs around the thigh-length hem. '
        'A narrow plain brown leather belt with small brass buckle; gray beige fitted trousers and low '
        'plain brown leather ankle shoes. Both hands empty and loosely clenched. Preserve the native '
        'slender proportions, long legs, restrained woven cloth and dark green tonal weight. No hat, '
        'cape, armor, jewelry, weapons or invented costume embellishments. Native cloth and hair/beard '
        'palette variants will be derived offline; preserve clear material boundaries.'),
    'mm7_m342': dict(label='Peasant Human1 FemaleA A', creature='human_female_peasant_1', base_palette=343,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','n'],
        identity_frames=[f'm342sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult human female peasant: fair skin, ordinary serious face, long thick wavy '
        'dark brown hair swept behind her shoulders down to mid-back, small plain gold earrings. Dark forest '
        'green fitted bodice with fine tan-gold front and back cross lacing, short green upper sleeves over '
        'white linen puffed elbow-length sleeves, broad white gathered square neckline. Long flowing green '
        'overskirt open down the lower front over a white linen underskirt, white hem and black low shoes. '
        'A dark brown leather waist belt with small brass buckle holds a narrow sheathed dagger at the hip. '
        'Both hands are empty. Preserve native proportions, clothing coverage, brown hair, green cloth, white '
        'linen and dark tonal weight. No armor, crown, hat, cape, staff, extra ornaments or costume redesign. '
        'Native palette variants will be derived offline; keep all material boundaries clear.'),
    'mm7_m322': dict(label='Peasant Elf FemaleA A', creature='elf_female_peasant', base_palette=323,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view', actions=['w','n'],
        identity_frames=[f'm322sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult female elf peasant: tall slender build, fair skin and pointed ears, '
        'long straight reddish chestnut hair swept behind her shoulders. Dark brown sleeveless fitted leather '
        'vest with native V neckline, two close rows of small brass buttons and front lacing, brown wrist '
        'wraps, dark forest-green long fitted trousers with narrow open side panels crossed by dark leather '
        'laces, and small brown ankle boots. One hand holds a long plain slightly crooked dark brown wooden '
        'walking staff exactly as in the native pose; the other hand is empty. Preserve her ordinary serious '
        'face, native proportions, dark tonal weight and original clothing coverage. Preserve separate '
        'green cloth, reddish hair, skin, leather, brass and wood materials. No ornaments, armor, hat, cape, '
        'extra weapons, glow or costume redesign. Native palette variants will be derived offline.'),
    'mm7_m332': dict(label='Peasant Elf MaleA A', creature='elf_male_peasant', base_palette=59,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, protect_cool_purple=True, batch_mode='per_action_view', actions=['w','n'],
        identity_frames=[f'm332sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult male elf peasant, lean muscular build with fair skin and pointed ears, '
        'short combed-back pale yellow-blond hair tied into a long narrow low ponytail. Plain dark brown '
        'sleeveless leather vest, open V neckline, two close vertical rows of small brass buttons and dark '
        'brown leather straps around upper arms and wrists. Muted dark burgundy-purple fitted trousers, '
        'brown ankle boots, narrow brown belt and a small sheathed dagger with pale gold fittings at the hip. '
        'Both hands are empty and loosely clenched. Preserve the ordinary stern native face, long slim legs, '
        'original proportions, material boundaries and dark tonal weight. No beard, cape, armor, hat, '
        'large weapons, extra jewelry or costume redesign. Native palette variants will be derived offline.'),
    'mm7_m210': dict(label='Elemental Water A', creature='water_elemental', base_palette=501,
        palette_paths={str(p):f'assets_dev/worlds/mm8/textures/pal{p}.act' for p in [501,502,503]},
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        protect_warm_contours=True, batch_mode='per_action_view',
        identity_frames=[f'm210sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original aquatic serpent water elemental: upright slender teal-blue scaly torso, '
        'small fishlike head with bulging gold eyes, blunt projecting fish mouth and a narrow pointed dorsal '
        'crest; finlike ear flaps, long slender arms with dark brown clawed hands, pale silver-blue scaled '
        'chest and continuous broad pale belly plate. The lower body is a thick curled serpentine fish tail '
        'resting in a low loop, ending in a broad upright fan fin with pale pink tips and dark teal rays. '
        'Preserve the exact native aquatic anatomy, small head, cool dark blue shadow weight and reflective '
        'pale belly scales. No human face, hair, clothing, jewelry, weapons or extra limbs. Keep teal scales, '
        'silver belly, brown hands, pink fin tips and yellow eyes separated for native palette recoloring.'),
    'mm7_m206': dict(label='Elemental Light A', creature='light_elemental', base_palette=528,
        palette_paths={'528':'assets_dev/worlds/mm8/textures/PAL528.act'},
        connected_pose_calibration=False, per_batch_window=False, neutralize_green_contours=False,
        core_magenta_tolerance=8, protect_warm_contours=True, batch_mode='single_view_chunks',
        identity_frames=['m206wa0','m206wg0','m206ws0'],
        description='The original tiny floating light elemental: a small flattened oval dark blue-gray '
        'glassy sphere with a pale gold horizontal glowing center, surrounded by irregular clusters of '
        'fine sharp pale ivory and gold star-shaped sparkles. Preserve its small central sphere, exact '
        'particle positions, empty gaps, flickering white-gold light, subtle cool rim and restrained '
        'native glow. Attack frames develop a larger orange-gold circular flare and luminous center. '
        'Death frames scatter into separate dim warm gray-brown motes and a few fading gold sparks. '
        'No humanoid face, eyes, limbs, wings, ornaments, opaque cloud, giant sun or extra broad bloom. '
        'Keep the diffuse light soft and translucent-looking, with crisp tiny sparkle cores and native '
        'relative brightness. Preserve every disconnected particle and each frame-specific silhouette.'),
    'mm7_m202': dict(label='Elemental Fire A', creature='fire_elemental', base_palette=496,
        palette_paths={'496':'assets_dev/worlds/mm8/textures/pal496.act'},
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        core_magenta_tolerance=8, protect_warm_contours=True, batch_mode='per_action_view',
        identity_frames=[f'm202f{letter}0' for letter in 'abcdef'],
        identity_view='six successive front-facing idle flame poses, in row-major order',
        description='The original humanoid fire elemental: smooth deep crimson red athletic torso and limbs, '
        'small bald oval red head with two pale glowing yellow eyes, plain clenched hands and bare flame feet. '
        'Bright flat orange and pale warm yellow flames lick around and across the body, with long narrow '
        'tongues above the head. Preserve the exact flame silhouettes, negative spaces, native flame coverage '
        'and dark red body shading of each pose. The body is a featureless magical figure, with no clothes, '
        'armor, accessories, weapons, lava cracks or redesign. Keep flame edges delicate and slightly soft '
        'with clear separate tongues, not white-hot bloom, smoke, sparks or a broad glowing halo. Preserve '
        'original orange/red/yellow colors and tonal weight.'),
    'mm7_m302': dict(label='Peasant Dwarf MaleA A', creature='dwarf_male_peasant', base_palette=58,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        batch_mode='per_action_view', actions=['w','n'], identity_frames=[f'm302sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult dwarf male peasant: short broad stocky build, long straight dark brown '
        'beard split into tapered strands, plain green drooping cloth cap, green long sleeves and green waist '
        'trim, dark brown leather sleeveless vest with broad pale ivory fleece edging, brown leather wrist '
        'cuffs, small brown belt, gray-beige trousers and dark brown knee boots with pale fleece cuffs. A thick '
        'plain rough brown wooden club hangs from his right hand. Preserve the native ordinary rugged face, '
        'large nose, compact short legs, sloping cap and dark tonal weight. No extra armor, jewelry, braids, '
        'weapons, exaggerated muscles or redesigned costume. Green cloth and brown beard will be recolored '
        'offline; keep their boundaries clear and preserve the original colors.'),
    'mm7_m198': dict(label='Elemental Earth A', creature='earth_elemental', base_palette=504,
        palette_paths={'504':'assets_dev/worlds/mm8/textures/pal504.act'},
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=False,
        core_magenta_tolerance=8, protect_warm_contours=False, batch_mode='per_action_view',
        identity_frames=[f'm198sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original stocky humanoid earth elemental made entirely of dark brown irregular fractured '
        'rock plates. Small blunt rocky head, broad bulky shoulders and torso, heavy bent arms with huge clenched '
        'stone fists, thick short legs and broad flat rock feet. Deep nearly black cracks separate warm dull '
        'ochre-brown stone facets with small restrained upper highlights. Preserve the compact native blocky '
        'silhouette, plain face and very dark earthy tonal weight. No glowing cracks, moss, crystals, armor, '
        'clothes, spikes, weapons, ornaments or redesigned anatomy.'),
    'mm7_m475': dict(label='zBlasterGuy A', creature='blaster_actor', base_palette=527, protect_cool_purple=True, protect_warm_contours=False,
        connected_pose_calibration=True, per_batch_window=True, neutralize_green_contours=True,
        batch_mode='per_action_view', identity_frames=[f'm475sa{i}' for i in range(5)],
        identity_view='front, front-right oblique, right profile, rear-right oblique, back in row-major order',
        description='The original adult human male blaster wielder, with medium straight brown hair, light tan '
        'skin and a short brown beard, black open-neck shirt with wide bright ivory V lapels, muted violet '
        'waistcoat panels and pale silver-lavender shoulder caps, dark brown studded belt, fitted black trousers, '
        'black knee boots and a long near-black cape with an exaggerated high pointed collar. A compact dark '
        'metal futuristic pistol is held low in his right hand. Preserve the native lean proportions, stern '
        'ordinary face, black tonal weight and small original weapon; no helmet, sword, extra armor or redesign.'),
    'mm7_m158': dict(label='Bat A', creature='bat', base_palette=159, connected_pose_calibration=True, green_material_grade=[.82,1.1,1.32], per_batch_window=True, neutralize_green_contours=False, batch_mode='per_action_view',
        identity_frames=['m158wa0','m158wa2','m158wa4','m158we0','m158we2','m158we4'],
        description='The original flying monster bat, with a small dark gray-brown furry rodent body and muzzle, '
        'two very large pointed ears with pale pink insides, tiny orange eyes, small pale fangs and pink bony '
        'wing fingers. Its enormous leathery wing membranes are deep forest green with brighter muted green '
        'upper planes and nearly black green undersides. Preserve the wide angular wing silhouette, thin bony '
        'ribs, tiny feet and native hunched flying posture. No feathers, horns, humanoid anatomy, ornaments or '
        'extra limbs. Preserve native dark colors and tonal weight; ONLY membranes will later change palette.'),
    'mm7_m479': dict(label='Treant A', creature='treant',
        description='The original rooted leafless evil tree: a broad conical dark earthy brown bark trunk flaring '
        'into a ragged root skirt, long narrow central face with two small vivid green eyes and a low broad mouth '
        'of pale uneven teeth. A jagged central spike and twisted bare branching crown, asymmetrical winding limbs '
        'and tiny twigs. Preserve dark native tonal weight, muted warm bark and subtle cool branch shadows. '
        'No humanoid legs, foliage, arms with hands, invented ornaments or redesigned face.',
        custom_batches=True, core_magenta_tolerance=8, protect_warm_contours=False, bark_spill_frames={'m479dd0':.74,'m479de0':.76,'m479df0':.81}),
    'mm7_7m500': dict(label='zcat a', creature='ambient_cat',
        description='An ordinary slender dark charcoal-black short-haired cat, faint smoky gray-brown fur markings, '
        'green eyes, pointed triangular ears, long slim legs and a long downward-curving tail. Preserve its narrow '
        'feline face, erect alert posture and very dark original tonal weight; no white markings, collar or accessories.'),
    'mm7_7m504': dict(label='zchicken a', creature='ambient_chicken',
        description='An ordinary slim white hen, pale cool blue-gray feather shadows, small red comb and wattle, '
        'small pale horn-colored beak, tiny dark eyes, slender pinkish bare legs and splayed toes, short upright '
        'white tail. Keep the native long upright neck and compact body. No giant rooster comb, colored plumage '
        'or invented accessories. Preserve white highlights and cool shadow weight.'),
    'mm7_m509': dict(label='zdog a', creature='ambient_dog',
        description='An ordinary lean shepherd-like dog with erect pointed ears, long narrow muzzle, dark eyes, '
        'slim straight legs, medium low-held tail and dark olive-gray-brown coarse coat with nearly black torso '
        'shadows. Keep the native alert upright posture and very dark muted coloration. No collar, markings, '
        'accessories, wolf exaggeration or cartoon redesign.')
}


def run(project, config=None):
    config = CONFIGS[project] if config is None else config
    root = HERE.parent / project
    inv = json.loads((HERE.parent / 'remaining_inventory.json').read_text())
    family = next(f for f in inv['families'] if f['world'] == 'mm7' and f['label'] == config['label'])
    palette = config.get('base_palette', family['palettes'][0])
    assert palette in family['palettes']
    groups, paths = {}, {}
    for path in [REPO/'assets_dev/engine/rendering/sprite_frame_data_common.yml',
                 *(REPO / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml')]:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
            paths[group['sprite_name'].lower()] = path
    actions = ['standing', 'walk', 'attack', 'shoot', 'hit', 'death', 'corpse', 'fidget']
    bindings, descriptors = {}, []
    for line in (REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt').read_text().splitlines():
        row = line.split('\t')
        if row[0] in {str(d['id']) for d in family['descriptors']}:
            descriptors.append(row)
            bindings[row[0]] = dict(zip(actions, [n.lower() for n in row[11:19]]))
    selected = {n: groups[n] for binding in bindings.values() for n in binding.values()}
    palette_paths = {str(p): REPO / config.get('palette_paths',{}).get(str(p),f'assets_dev/worlds/mm7/textures/pal{p:03d}.act') for p in family['palettes']}
    palette_path = palette_paths[str(palette)]
    colors = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
    sources, natives = {}, {}
    for directory in ['native', 'references', 'prompts/submitted', 'raw', 'review']:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for relative in family['existing_images']:
        path = REPO / relative
        bmp = Image.open(path)
        assert bmp.mode in ('P','L'), 'Native frame must contain original 8-bit palette indices.'
        indices = np.array(bmp)
        native = Image.fromarray(np.dstack((colors[indices], (indices != 0).astype(np.uint8)*255)))
        name = path.stem.lower()
        native.save(root / f'native/{name}.png')
        natives[name] = native
        sources[name] = dict(path=relative, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            size=list(native.size), visible_bounds=native.getbbox(), transparency_index=0,
            referenced=name in family['images'])
    boxes = [im.getbbox() for im in natives.values()]
    canvases = sorted({im.size for im in natives.values()})
    assert len(canvases) == 1, 'Variable native canvases require explicit shared-canvas offsets.'
    window = [min(b[0] for b in boxes)-12, min(b[1] for b in boxes)-12,
              max(b[2] for b in boxes)+12, max(b[3] for b in boxes)+12]
    family_window = window.copy()
    stem = re.match(r'^[67]?m\d{3}', family['standing_images'][0]).group()
    if config.get('batch_mode') == 'single_view_chunks':
        batches = dict(standing=dict(frames=config['identity_frames'], columns=3,
            view='one native single-image camera; distinct idle particle arrangements'))
        remaining = set(sources)-set(config['identity_frames'])
        for action in ['w','a','d']:
            names = sorted(n for n in remaining if n.startswith(stem+action))
            for i in range(0,len(names),6):
                batches[f'{action}_{i//6}'] = dict(frames=names[i:i+6],columns=3,
                    view='native single-image camera; preserve each exact sphere and disconnected particle arrangement')
    elif config.get('batch_mode') == 'per_action_view':
        batches = dict(standing=dict(frames=config['identity_frames'], columns=3,
            view=config.get('identity_view','native front, right profile, rear; folded wings in row 1, spread wings in row 2')))
        remaining = set(sources)-set(config['identity_frames'])
        views = ['FRONT','FRONT-RIGHT OBLIQUE','RIGHT PROFILE','REAR-RIGHT OBLIQUE','BACK']
        for action in config.get('actions',['w','a','n']):
            for view in range(5):
                names = sorted(n for n in remaining if re.fullmatch(re.escape(stem)+action+r'[a-z]'+str(view),n))
                assert names
                parts=1 if config.get('sampling_target') else (len(names)+7)//8
                for part, indices in enumerate(np.array_split(np.arange(len(names)),parts)):
                    selected_names=[names[i] for i in indices]
                    key=f'{action}_{view}' + (f'_{part}' if parts>1 else '')
                    batches[key] = dict(frames=selected_names,columns=4 if len(selected_names)>6 else 3,
                        view=views[view]+' in EVERY cell; follow each native limb, body and head pose')
        fidgets = sorted(n for n in remaining if n.startswith(stem+'f'))
        if fidgets:
            batches['fidget'] = dict(frames=fidgets, columns=2 if len(fidgets)<=4 else 3,
                view='native frontal fidget sequence, following each pose exactly')
        batches['death_corpse'] = dict(frames=sorted(n for n in remaining if n.startswith((stem+'d',stem+'x'))),
            columns=3,view='native death and prone corpse orientations exactly')
    elif config.get('custom_batches'):

        batches = dict(standing=dict(frames=['m479sa0', 'm479al0'], columns=2,
            view='same native frontal camera: closed-mouth rest, then twisted open-mouth attack'))
        remaining = sorted(n for n in sources if n.startswith(stem+'a') and n != 'm479al0')
        for i in range(0, len(remaining), 6):
            batches[f'attack_{i//6}'] = dict(frames=remaining[i:i+6], columns=3,
                view='native frontal camera; follow each exact branch twist and mouth expression')
        batches['hit'] = dict(frames=sorted(n for n in sources if n.startswith(stem+'n')), columns=4,
            view='native frontal camera with exact reaction and mouth poses')
        batches['death_corpse'] = dict(frames=sorted(n for n in sources if n.startswith((stem+'d',stem+'x'))),
            columns=4, view='native frontal camera with breaking tree and stump poses; preserve all detached fragments')
    else:
        batches = dict(standing=dict(frames=family['standing_images'], columns=3,
                                   view='front, front-right oblique, right profile, rear-right oblique, back in row-major order'))
        views = ['FRONT', 'FRONT-RIGHT OBLIQUE', 'RIGHT PROFILE', 'REAR-RIGHT OBLIQUE', 'BACK']
        for view in range(5):
            names = sorted(n for n in sources if re.fullmatch(re.escape(stem)+r'w[a-z]'+str(view), n))
            assert len(names) <= 8
            batches[f'walk_{view}'] = dict(frames=names, columns=4, view=views[view]+' in EVERY cell')
        batches['death_corpse'] = dict(frames=sorted(n for n in sources if re.fullmatch(re.escape(stem)+r'[dx][a-z]0', n)),
                                      columns=3, view='native collapse and prone orientations in exact source order')
    batches.update(config.get('extra_batches', {}))
    for key, names in config.get('extra_batch_frames', {}).items():
        batches[key]['frames'].extend(names)
    assert sorted(n for b in batches.values() for n in b['frames']) == sorted(sources)
    if config.get('sampling_target'):
        sys.path.insert(0, str(HERE.parent))
        from sheet_checks import plan
        packed = {}
        for key, batch in batches.items():
            bounds = [natives[n].getbbox() for n in batch['frames']]
            common = [min(b[0] for b in bounds)-12, min(b[1] for b in bounds)-12,
                      max(b[2] for b in bounds)+12, max(b[3] for b in bounds)+12]
            pending = batch['frames'][:]
            part = 0
            while pending:
                budget = plan(len(pending), common[2]-common[0], common[3]-common[1],
                              target=config['sampling_target'])
                names, pending = pending[:budget['poses']], pending[budget['poses']:]
                name = key if not pending and not part else f'{key}_{part}'
                packed[name] = dict(batch, frames=names, columns=budget['columns'],
                                    common_window=common, budget=budget)
                part += 1
        batches = packed
    for key, batch in batches.items():
        if batch.get('common_window'):
            window = batch['common_window']
        elif config.get('per_batch_window'):
            batch_boxes = [natives[n].getbbox() for n in batch['frames']]
            window = [min(b[0] for b in batch_boxes)-12, min(b[1] for b in batch_boxes)-12,
                      max(b[2] for b in batch_boxes)+12, max(b[3] for b in batch_boxes)+12]
        cols = batch['columns']
        rows = (len(batch['frames'])+cols-1)//cols
        # Portrait-ish cells give quadrupeds room at a useful aspect ratio without individual fitting.
        width, height = window[2]-window[0], window[3]-window[1]
        if cols*width/(rows*height) > 2.8:
            cols = 3
            rows = (len(batch['frames'])+cols-1)//cols
        cell = [width*4, height*4]
        sheet = Image.new('RGB', (cell[0]*cols, cell[1]*rows), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = natives[name].crop(window).resize(cell, Image.Resampling.NEAREST)
            sheet.paste(im, (i%cols*cell[0], i//cols*cell[1]), im)
        sheet.save(root / f'references/{key}.png')
        batch.update(columns=cols, rows=rows, cell_size=cell, native_window=window, reference_scale=4)
        prompt = f'''Use case: style-transfer. Faithfully restore the supplied Might and Magic VII native {config['creature']} sprite sheet into detailed coherent fantasy game artwork.
Input 1 is exact POSE, VIEW and LAYOUT authority: {cols} columns by {rows} rows; {len(batch['frames'])} occupied cells in row-major order. Batch {key}. Camera: {batch['view']}. Leave unused cells empty.
Identity: {config['description']}
Preserve each native head angle, material placement, branch/limb position, base contact, proportions and silhouette. Clarify fine material surface detail with restrained soft upper-left baked lighting, preserving the native colors and tonal weight. No generic standing replacements for moving poses, no per-cell recentering, stretching or independent zoom. Keep common anatomical scale and source-relative cell placement. Do not retain enlarged pixel stair steps.
All anatomy and thin features must stay inside their cells with clear gutters. Background: uniform pure magenta RGB(255,0,255); no cast shadow, gradient, checkerboard, text, labels, grid lines, colored bounce, reflection or halos. Aim for approximately 2048 pixels wide with useful per-pose detail.
'''
        if not key.startswith('standing'):
            prompt += 'Input 2 is the accepted enhanced identity/material reference ONLY. Input 1 controls every pose and view. Do not copy the identity reference layout or camera angles into the animation.\n'
        if key == 'death_corpse':
            prompt += 'Follow the native collapse rotations and resting prone body mass; do not enlarge low poses to fill their cells. No added injuries or blood.\n'
        if config.get('true_alpha'):
            prompt = prompt.replace('Background: uniform pure magenta RGB(255,0,255);',
                'Background: genuine transparent PNG alpha, including empty cells;')
            prompt += ('Reconstruct fine natural material detail and smooth contours at higher resolution. '
                       'A merely enlarged pixelated sprite, preserved pixel blocks, blur or sharpening halos '
                       'is unacceptable. Modest faithful anatomical interpretation is allowed. '
                       'The reference matte is only for readability; output must have real transparency.\n')
        (root / f'prompts/{key}.txt').write_text(prompt)
        if config.get('sampling_target'):
            (root / f'prompts/submitted/{key}_v1.txt').write_text(prompt)
    provenance = lambda p: dict(path=str(p.relative_to(REPO)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    source = dict(sources=sources, groups=selected, descriptor_rows=descriptors, descriptor_bindings=bindings,
        base_palette=palette, palettes=family['palettes'], palette_sources={str(p): provenance(palette_paths[str(p)]) for p in family['palettes']},
        group_sources=[provenance(p) for p in sorted({paths[n] for n in selected})], generation_window=family_window,
        logical_canvases=canvases, unreferenced=family['unreferenced_family_images'],
        palette_note=f'Base palette {palette}; native palettes {family["palettes"]}. Author enhanced-art masks when distinct.')
    (root / 'sources.json').write_text(json.dumps(source, indent=2)+'\n')
    (root / 'batches.json').write_text(json.dumps(batches, indent=2)+'\n')
    (root / 'config.json').write_text(json.dumps(config, indent=2)+'\n')
    generation = root / 'generation.json'
    if not generation.exists():
        generation.write_text(json.dumps(dict(tool='image_gen.imagegen (built-in)', batches={}), indent=2)+'\n')
    print(f'{project}: {len(sources)} native frames, {len(batches)} batches, palette {palette}, window {window}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--config', type=Path, help='Explicit configuration for a new family.')
    args = parser.parse_args()
    run(args.project, json.loads(args.config.read_text()) if args.config else None)
