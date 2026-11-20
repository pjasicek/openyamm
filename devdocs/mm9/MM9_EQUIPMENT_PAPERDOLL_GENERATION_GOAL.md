# MM9 Equipment Paperdoll Placeholder Generation Goal

## Status

Phases 0-4 are complete. The generic pipeline owns generation, fitting, review, provenance, promotion, and
verification; the active MM9 complex-picture table covers all 68 mapped items. Arming Doublet and
Broderick's Hauberk were migrated without changing their promoted hashes, and Coif completed the first full
category-profile pilot. Regal Belt completed the normal belt pilot, and Hubris completed the unique-medallion belt
pilot. Sabaton completed the normal tall-plated boots pilot, and Fuzzy Slippers completed the ankle-only two-foot
geometry pilot. Death Cap completed the hornless and spikeless unique skull-mask pilot. Prize Plate completed the
short-torso unique-tier armor pilot across both arm poses. Padded Leather completed the first Phase 2 standard armor
family after its overlong legwear-like target was corrected from `thigh_length` to `hip_length`. Hardened Leather then
completed the standard `short_torso` vest profile with distinct weapon and empty-hand fits on all five doll types.
Beldonian Hard Leather completed the same geometry with a preserved asymmetric shoulder-flap design. Scaled Leather
then completed the MM7 Officer's Leather geometry with large ochre scale rows; its two female sources required an
explicit global magenta-hue key and transparent-RGB clear before their equipped composites were artifact-free.
Imperial Scale completed the Caravaner's Leather `hip_length` geometry with copper scales, pale shoulder guards, and
restrained red accents. Its alternate minotaur source required a targeted lower-leg continuity repair, and the fitter
now removes both disconnected bright-magenta islands and border-connected dark-magenta vignettes before resampling so
hidden chroma-key RGB cannot bleed into fitted edges. Brigandine then completed the Regnan Leather `hip_length`
geometry with black-brown panels, dense rivets, short sleeves, and a segmented skirt. Its generated full-body proposals
required audited anatomy-excluding source crops for four variants so generated hooves, wraps, and footwear could not
enter disconnected lower armor components. Combat Brigandine then completed the Alvarian Leather `thigh_length`
geometry with brown articulated-square panels, long sleeves, and a split coat. The same four non-human/dwarf proposals
required anatomy-excluding crops before their lower components were clean. Brigan der Combit then completed the same
Alvarian Leather `thigh_length` geometry as a quieter tier-5 coat with muted brown quilting, a vertical front opening,
and minimal trim. Seven full-body proposals required anatomy-excluding crops, including tighter upper crops for both
troll poses so head colors could not enter the collar. Aklean Bouila then completed the MM7 Royal Leather
`hip_length` geometry with green panels, pale-gold riveted chest and hem panels, and small pauldrons. Its initial
male-empty-hand and female proposals included generated anatomy or unrelated clothing; targeted anatomy-removal AI
fix-ups preserved their fitted shoulders, sleeves, torso, and segmented hem before the audited alpha was reapplied.
Butted Chain then completed the MM7 Fine Chain Mail geometry as a coarse bronze-gray sleeveless mail shirt with ragged
divided lower tabs. Equipped review rejected its initial `thigh_length` mapping because the female variants became
unrelated chain leggings; the authoritative profile was corrected to `hip_length`, and six anatomy-bearing proposals
received targeted equipment-only AI fix-ups before deterministic refitting and equipped review. Rivited Chain then
completed the MM8 Minotaur Chainmail `thigh_length` geometry as
bright riveted silver mail with a sleeveless torso and long divided hem. Five full-body proposals received targeted
anatomy-removal AI fix-ups; all ten fitted results preserved the source-derived mail construction, distinct arm poses,
and uncovered footwear in equipped review. Iron Chain then completed the same fitted geometry as darker iron mail with
short sleeves, a broad divided skirt, and restrained leather edging. Six full-body proposals received targeted
anatomy-removal AI fix-ups; both equipped arm poses across all five doll types retained clean sleeve openings, readable
links, the split hem, and uncovered footwear. Steel Chain then completed the same `thigh_length` geometry with clean,
bright silver links, short sleeves, and a divided lower mail section. All ten initial equipment-only proposals passed
deterministic refitting and equipped review without corrective generation; the brighter steel remained distinct from
Iron Chain while respecting both arm poses and all foot exclusions. Chain Haubergeon then completed the MM7
Resplendent Chain Mail `short_torso` geometry as a plain gray mail shirt with small reinforced shoulder panels. All ten
equipment-only proposals removed the reference's blue-white tabard, gold belt, crest, and long skirt while preserving
pose-specific sleeve alignment and clean short hems in equipped review. Chain Hauberk then completed the MM8 Siertal
Chainmail `thigh_length` geometry with cool gray-violet mail, long sleeves, a simple split lower section, and restrained
dull-steel shoulder guards. Equipped review rejected an initial all-mail shoulder treatment as soft pointed fins; all
ten sources received a focused shoulder-material correction, and the minotaur weapon pose also received an earlier
anatomy-removal fix-up. The corrected family preserved the mapped geometry without the reference's gems, belt, spikes,
or black cuirass panels. Chedian Chain then completed the MM7 Resplendent Chain Mail `thigh_length` geometry as bright
silver mail with a royal-blue and yellow V-shaped chest cloth, matching cuffs, and a trimmed divided hem. The female
weapon and empty-hand proposals and the minotaur weapon proposal received targeted anatomy-removal fix-ups before
deterministic refitting; equipped review confirmed clean sleeve openings, uncovered feet, readable heraldic cloth, and
correct alignment in both arm poses. Chain Harness then completed the MM8 Erudine Chainmail `short_torso` geometry as
compact dark-gray mail with restrained dark leather edging and straps. All ten initial equipment-only proposals passed
deterministic refitting and equipped review without corrective generation; they removed Erudine's gold mail, ornate
plate, belt, and skirt while preserving each fitted shoulder and arm pose, hollow openings, and uncovered lower body.
Lachmon Hauberk then completed the MM7 Golden Chain Mail `thigh_length` geometry as plain muted sage-green mail with
full sleeves, divided lower armor, and minimal dark edging. The female weapon proposal received an anatomy-removal
fix-up to replace invented mail feet with open ankle cuffs, and the female empty-hand proposal received a color-only
fix-up to remove a red chroma fringe. Equipped review confirmed aligned sleeves and lower panels while leaving every
doll's footwear, feet, fur, and hooves exposed. Trigvanian Mail then completed the same MM7 Golden Chain Mail
`thigh_length` geometry as bright green-silver chain with dark piping and the MM9 source's paired circular spiral
ornaments. Its first minotaur weapon-pose proposal included the complete doll; a targeted equipment-only fix-up
removed the head, hands, fur, legs, and hooves before fitting. Equipped review confirmed coherent circular ornament
placement, distinct weapon and empty-hand sleeves, and exposed footwear, fur, and hooves on every doll. Ronenguard
Plate then completed the MM8 Minotaur Plate `short_torso` geometry as a plain worn iron cuirass with narrow
dull-silver edging. All ten initial equipment-only proposals passed deterministic fitting and equipped review without
corrective generation; the mapped short torso removed the reference skirt while preserving the proven per-doll
shoulder, neckline, and waist fit in both arm poses. Field Plate then completed the same MM8 Minotaur Plate
`short_torso` geometry as smooth dark-steel field cuirasses with restrained silver edging and stronger anatomical
ridging. All ten equipment-only proposals passed deterministic fitting and equipped review without corrective
generation; both arm poses remain coherent, every lower body remains uncovered, and enlarged edge review found no
checkerboard, magenta spill, or white halo. Full Plate then completed the MM7 Plate Armor `full_harness` geometry as
blue-gray articulated plate with rounded pauldrons and segmented lower plates. Targeted source fix-ups removed
invented female armored feet and excess troll/dwarf forearm plates before fitting. Equipped review confirmed both arm
poses, coherent full-harness construction, separated leg armor, and exposed feet, footwear, fur, and hooves on every
doll. Paladin's Plate then completed the MM7 Splendid Plate Armor `full_harness` geometry as bright silver plate with
cobalt accents, restrained gold edging, rounded pauldrons, and a readable circular holy medallion. The minotaur weapon
proposal received a compact-harness fix-up before fitting; all variants then passed exact-alpha and equipped review,
including the female open ankle cuffs and the short troll, minotaur, and dwarf lower panels. Current acceptance is
Heavy Plate then completed the same MM7 Splendid Plate Armor `full_harness` geometry as dark blue-black gunmetal
plate with broad rounded shoulders, smooth breastplates, and restrained segmented faulds. Targeted source fix-ups
removed excess minotaur, troll, and dwarf forearm armor and stripped generated dwarf trousers, wraps, and boots before
fitting. Both armed and empty-hand contact sheets then confirmed compact non-human proportions, distinct arm poses,
and exposed hands, forearms, footwear, fur, and hooves. Thjoradric Plate then completed the same fitted family as warm
reddish-copper heavy armor with layered shoulders, ribbed articulated arms, restrained highlights, and vertically
segmented skirts. Its ten first-pass sources fit the audited masks without corrective generation; equipped and 8x
review confirmed distinct arm poses, clean chroma-keyed edges, open female ankle cuffs, and compact minotaur, troll,
and dwarf armor above exposed anatomy. Imperial Harness then completed the MM7 Noble Plate Armor `full_harness`
geometry as dark charcoal imperial plate under a readable gold grid framework. One targeted fix-up removed generated
female feet before fitting. Armed, empty-hand, and enlarged review then confirmed the grid followed each fitted pose
instead of being tiled, with open ankle cuffs and exposed non-human hands, legs, footwear, and hooves. Dark Plate then
completed the same MM7 Noble Plate Armor `full_harness` geometry as near-black articulated plate with narrow
bronze-gold ridges, pointed breastplates, and aggressive angular pauldrons. One targeted source fix-up removed an
unintended red shoulder mark before fitting. Armed, empty-hand, and enlarged review confirmed the ornament followed
each doll's fitted pose, with distinct arm states, open female feet, and exposed non-human hands, legs, footwear, fur,
and hooves. Igdrasine then completed the MM7 Officer's Leather `hip_length` geometry as a sleeveless forest-green and
cobalt tabard with antique-gold piping and a readable golden world-tree emblem. The mapping intentionally replaced
Hareck's Leather because its inherited shoulder spikes contradicted the MM9 garment; Officer's Leather provides the
correct sleeveless fitted silhouette despite its lower legacy tier. Two backdrop-only fix-ups restored exact magenta
before fitting. Staged-offset armed, empty-hand, and enlarged review confirmed the emblem followed every torso while
leaving all arms, lower bodies, footwear, fur, and hooves exposed. Current acceptance is 336/488 variants across 37/68
atomically complete families. Poltergeist then completed the MM7 Elven Chainmail `short_torso` geometry as solid pale
spectral fine chain with restrained sage-blue iridescence, dark-steel edging, and three riveted reinforcement bands.
All ten source-derived proposals passed strict magenta despill and exact-alpha fitting without anatomical fix-up.
Armed, empty-hand, and enlarged review confirmed compact torso coverage, distinct arm openings, coherent fitted bands,
and exposed hands, legs, footwear, fur, and hooves on every doll. Current acceptance is 346/488 variants across 38/68
atomically complete families. Swordsbane then completed the MM8 Supreme Plate `full_harness` geometry as warm bronze
and aged-ivory plate with burgundy joint cloth and a circular red chest setting. Equipped review caught that the legacy
mask was forcing Supreme Plate's unrelated shoulder spikes and detached foot fragments back into the generated art;
the pipeline now applies the mapping-declared `smooth_upper_protrusions` silhouette adjustment before fitting, with
unit coverage proving it only removes legacy alpha. Refit armed, empty-hand, and enlarged review confirmed smooth
rounded shoulders, exposed human feet and minotaur hooves, coherent articulated armor, and compact troll/dwarf lower
panels. Current acceptance is 356/488 variants across 39/68 atomically complete families.
Death Cuirass then completed MM7 Officer's Leather `short_torso` geometry as a sleeveless matte-black cuirass with
subtle embossed arabesques, flowing antique-gold chest tracery, and narrow gold piping. Preflight rejected the original
same-tier Hareck's Leather mapping because its spiked shoulder construction contradicted the MM9 inventory icon; the
lower-tier Officer's Leather mapping owns the correct sleeveless fitted silhouette. All ten proposals passed exact-alpha
fitting without corrective generation, and armed, empty-hand, and enlarged review confirmed clean neck and arm
openings, compact hems, and exposed arms, lower bodies, footwear, fur, and hooves. Current acceptance is 366/488
variants across 40/68 atomically complete families.
Quilted Armor then completed MM7 Crude Leather Armor `short_torso` geometry as a warm golden-tan diamond-quilted
shirt with pale rope ties and dark-brown edging. Preflight corrected the stale gray-blue transfer description after
the promoted inventory icon and original PCX proved the binding tan design. One targeted source fix-up removed
invented quilted leggings from the female empty-hand proposal; all ten deterministic fits then passed exact-alpha,
armed, empty-hand, and enlarged review with compact hems and exposed lower bodies. Current acceptance is 376/488
variants across 41/68 atomically complete families.
Plain Helm then completed the MM8 Helm `open_nasal_helm` geometry as a practical brown segmented dome with dull-steel
ribs, rim, and centered nasal guard. A targeted equipment-only fix-up removed the generated dwarf face, hair, beard,
skin, and neck before fitting. All four supported non-minotaur variants then passed exact-alpha, equipped, and enlarged
review with open faces, readable nasal guards, correct head angles, and no baked-in anatomy. Current acceptance is
380/488 variants across 42/68 atomically complete families.
Barbute Helm then completed the MM8 Full Helm `closed_face_helm` geometry as a smooth, weathered dull-steel bowl with
dark T-shaped openings, narrow nose bridges, and restrained cheek guards. Equipped preflight caught the legacy Full
Helm's unrelated crown spikes; the mapping now applies `smooth_upper_protrusions` before fitting. The revised four
non-minotaur variants passed exact-alpha, equipped, and enlarged review with coherent closed-face coverage and no
baked-in anatomy or fantasy ornament. Current acceptance is 384/488 variants across 43/68 atomically complete families.
Loaf Helm then completed a new `closed_conical_helm` profile derived from the MM7 Elven Helm fitted family. Preflight
caught that the source's large face opening contradicted the MM9 item's closed perforated guard, so the profile now
closes only the largest enclosed transparent face component while preserving every original exterior alpha pixel.
The four source-derived variants reproduce the MM9 icon's tall blue-gray steel cone, narrow eye slit, vertical rib,
and perforated lower guard. Exact-alpha, equipped, and enlarged review confirmed correct head alignment on male,
female, troll, and dwarf dolls with no baked anatomy, chainmail, magenta spill, or bright fringe. Current acceptance is
388/488 variants across 44/68 atomically complete families.
Bascinet then completed the MM8 Full Helm `closed_face_helm` geometry as a smooth bright-silver visor helm with a
projecting brow, narrow eye slit, and perforated lower guard. Preflight removed the reference's unrelated crown spikes
through `smooth_upper_protrusions`. Equipped review then rejected first-pass sources whose separate inventory-style
gorgets were compressed into broad collar filler; one targeted construction fix-up per suffix replaced them with
compact head-sized helmets while retaining the MM9 visor identity. The four corrected variants passed exact-alpha,
equipped, and enlarged review with clean head placement and no baked anatomy, detached neck armor, magenta spill, or
bright fringe. Current acceptance is 392/488 variants across 45/68 atomically complete families.
Sallet then completed the MM7 Conscript's Helm `open_round_helm` geometry as a plain worn gray-silver bowl with a low
rim, fully open face, and modest rear tail. Preflight applied `smooth_upper_protrusions` to remove the source family's
unrelated crown spike while retaining its fitted open-bottom silhouette. One female proposal required a background-only
AI correction from black to uniform magenta before fitting; the helmet pixels remained unchanged. All four variants
then passed exact-alpha, equipped, and enlarged review with correct open-face coverage, clean rims, no baked anatomy,
and no chroma-key fringe. Current acceptance is 396/488 variants across 46/68 atomically complete families.
Dragon Helm then completed the MM8 Full Helm `closed_face_helm` geometry as a dark blue-black scaled helm with cool
steel crown highlights, a readable antique-gold dragon-cross face frame, and narrow gold lower edging. Preflight added
`smooth_upper_protrusions` because the MM9 source does not contain the reference family's crown spikes. The dwarf
proposal required a background-only black-to-magenta correction that preserved the helmet pixels. All four variants
then passed exact-alpha, equipped, and enlarged review with coherent gold framing, compact fitted coverage, no baked
anatomy, and no chroma-key fringe. Current acceptance is 400/488 variants across 47/68 atomically complete families.
Imperial Helm then completed the same MM8 Full Helm `closed_face_helm` geometry as a bright silver great helm with a
bold antique-gold eye bar and vertical cross frame, perforated lower face, and cobalt-blue side stripe. Preflight added
`smooth_upper_protrusions` because its flat, practical crown does not contain the reference family's spikes. All four
first-pass equipment-only proposals passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged
review with centered head placement, clear eye slits, readable cross framing, no baked anatomy, and no bright fringe.
Current acceptance is 404/488 variants across 48/68 atomically complete families.
Jarl's Helm then completed a corrected MM7 Phynaxian Helm `open_cheek_helm` geometry as a bright segmented silver dome
with a dark riveted brow, large open face, and circular cheek, jaw, and ear guards. Preflight rejected the stale Full
Helm mapping because it sealed the face and could not express the MM9 source's open circular side structure. The
replacement applies `smooth_upper_protrusions` to remove Phynaxian horns while preserving its fitted cheek rails. One
female proposal received a targeted equipment-only fix-up to remove the generated doll before refitting. All four
variants then passed exact-alpha, equipped, and enlarged review with usable face openings, coherent side guards, no
baked anatomy, and no bright fringe. Current acceptance is 408/488 variants across 49/68 atomically complete families.
Witchbane then completed the MM8 Drogg's Helm `unique_face_mask` geometry as an aged ivory skull front over a dark
charcoal hood with a compact steel-blue lower neck guard. The profile removes the reference spike and horns and closes
its fitted silhouette without carrying over Drogg ornament. All four equipment-only proposals passed strict magenta
despill, exact-alpha fitting, equipped review, and enlarged review with readable skull cavities, coherent head angles,
clean neck placement, no baked anatomy, and no bright fringe. Current acceptance is 412/488 variants across 50/68
atomically complete families.
Brongnoker then completed the MM8 Helm `open_nasal_helm` geometry as a restrained unique-quality version of the MM9
source's practical brown segmented helmet. Dark weathered leather panels, clean dull-silver ribs and brow rim, small
rivets, and a centered nasal guard remain readable without invented gems, crest, horns, plume, cheek mask, or visor.
The female proposal received a targeted equipment-only fix-up to remove generated face, hair, skin, and neck before
refitting. All four variants then passed exact-alpha, equipped, and enlarged review with open faces, aligned nasal
guards, no baked anatomy, and no bright fringe. Current acceptance is 416/488 variants across 51/68 atomically
complete families.
Prize Skullcap then completed a corrected MM7 Elven Helm `conical_helm` geometry as a compact polished white-silver
cone with subtle vertical fluting, a clean lower rim, and sparse dark-red studs. Preflight found that `conical_helm`
was previously only descriptive and left the reference chain hood, face ring, and nasal geometry in every target. The
pipeline now derives a solid fitted upper cone from the reference's face-opening boundary and deterministically removes
all lower hood geometry, with focused unit coverage. All four equipment-only proposals passed strict magenta despill,
exact-alpha fitting, equipped review, and enlarged review with clear faces, aligned rims, no chainmail or nasal guard,
and no bright fringe. Current acceptance is 420/488 variants across 52/68 atomically complete families.
Broderick's Helm then completed the MM8 Full Helm `closed_face_helm` geometry as a flat-topped bright-silver great helm
with cobalt-blue eye and side framing, a narrow black slit, perforated lower face, and a very small antique-gold cross
detail. Preflight added `smooth_upper_protrusions` because the MM9 source contains none of the reference crown spikes.
All four equipment-only proposals passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged
review with compact set-consistent coverage, readable blue framing, no spikes or baked anatomy, and no bright fringe.
Current acceptance is 424/488 variants across 53/68 atomically complete families.
Fre's Helm then completed a new `hornless_round_helm` profile derived from the MM7 Mogred Helm fitted family.
Preflight caught that the legacy target retained the reference horns even though both MM9 source images are hornless.
The profile now removes the top ornament and side horns, constrains the upper dome through a symmetric fitted envelope,
and preserves the lower open-face placement without changing already accepted helmet masks. All four equipment-only
proposals passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged review with readable green
domes, black brow bands, gold eye and nasal framing, open faces, no baked anatomy, and no bright fringe. Current
acceptance is 428/488 variants across 54/68 atomically complete families.
Fur Cap then completed the first constructive `soft_cap` profile using the MM7 Fancy Hat fitted family. Preflight
rejected the stale Scholar's Cap mapping because it retained a triangular crown, white feather, and metal ornament
that contradict the MM9 source. Fancy Hat supplies the correct low round crown, while the profile preserves every
legacy cap pixel, extends only the female and troll canvases where necessary, and adds a narrow attached viewer-left
tail below the cap. All four equipment-only proposals passed strict magenta despill, exact-alpha fitting, equipped
review, and enlarged review with rough tan fur, readable dark-brown/tan stripes, clear faces, no jewel or feather, no
baked anatomy, and no bright fringe. Current acceptance is 432/488 variants across 55/68 atomically complete families,
and the helmet category is complete at 64/64 variants.
Leather Boots then completed a new `low_ankle_boots` profile using the same MM7 Leather Boots fitted family. Preflight
rejected the stale MM8 Walking Boots mapping because its calf-height shafts contradicted the MM9 source's low leather
shoes. The corrected profile preserves the audited left- and right-foot regions while removing all shaft coverage.
All four equipment-only proposals passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged
review with warm brown leather, folded openings, simple brass straps, independent foot direction, grounded soles, no
baked legs or trousers, and no bright fringe. Current acceptance is 436/488 variants across 56/68 atomically complete
families, with boots at 12/44 variants.
Hardened Boots then completed the MM8 Hardened Leather Boots `ordinary_boots` geometry as plain dark-brown stiff
leather with rolled open cuffs, reinforced feet, and restrained ankle buckles. The first female proposal included the
doll's blue legwear above both openings; one targeted equipment-only fix-up removed it before deterministic fitting.
All four variants then passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged review with
independent foot direction, grounded soles, no baked anatomy, and no bright fringe. Current acceptance is 440/488
variants across 57/68 atomically complete families, with boots at 16/44 variants.
Chain Boots then completed the corrected MM7 Leather Boots `low_ankle_boots` geometry as silver chain covering over
dark leather with plain brown open cuffs. Preflight rejected the stale MM8 Regnan Boots mapping because its tall
gold-laced shin guards contradicted both MM9 source images. The corrected mapping reuses the audited low-foot geometry
while transferring only the mail material and cuff identity. All four first-pass proposals passed strict magenta
despill, exact-alpha fitting, equipped review, and enlarged review with readable links, independent foot direction,
grounded soles, no baked anatomy, and no bright fringe. Current acceptance is 444/488 variants across 58/68 atomically
complete families, with boots at 20/44 variants.
Ronenguard Boots then completed the MM7 Steel Plated Boots `plated_boots` geometry as practical brown leather shafts
with simple open cuffs and spaced dull-gray steel reinforcement bands over the ankle and foot. The existing mapping
matched both MM9 source images and required no silhouette correction. All four first-pass proposals passed strict
magenta despill, exact-alpha fitting, equipped review, and enlarged review with restrained rivets, independent foot
direction, grounded soles, no baked anatomy, and no bright fringe. Current acceptance is 448/488 variants across
59/68 atomically complete families, with boots at 24/44 variants.
Steel Boots then completed the same MM7 Steel Plated Boots `plated_boots` geometry as compact bright worn-steel foot,
ankle, and lower-shaft plates with narrow dark articulation seams and brown inner cuffs. All four first-pass proposals
passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged review with steel-dominant coverage,
independent foot direction, grounded soles, no baked anatomy, and no bright fringe. Current acceptance is 452/488
variants across 60/68 atomically complete families, with boots at 28/44 variants.
Prote der Fatta then completed the MM7 Paladin Boots `ornate_plated_boots` geometry as white-silver articulated foot
plates, black inset shaft panels, narrow antique-gold edging, and restrained scroll ornament. All four proposals passed
exact-alpha fitting, equipped review, and enlarged review with open cuffs, independent foot direction, grounded soles,
no baked anatomy, and no bright fringe. The first three sources used the strict magenta-key path; the dwarf source
returned clean native transparency and used the equivalent alpha-key path. Current acceptance is 456/488 variants
across 61/68 atomically complete families, with boots at 32/44 variants.
Walking Boots then completed the MM7 Seven League Boots `unique_leather_boots` geometry as plain warm red-brown
high-laced leather boots with dark soles, open cuffs, and small dull-brass eyelets. The transfer deliberately removed
all artifact jewelry while retaining the proven fitted pose. All four proposals passed strict magenta despill,
exact-alpha fitting, equipped review, and enlarged review. Current acceptance is 460/488 variants across 62/68
atomically complete families, with boots at 36/44 variants.
Death Boots then completed the MM7 Knight's Boots `tall_plated_boots` geometry as severe blackened-steel shafts with
cold silver articulated feet, sharp charcoal seams, narrow blue-black edge reflections, and restrained dark rivets.
All four proposals passed strict magenta despill, exact-alpha fitting, equipped review, and enlarged review with no
gold heraldry, baked anatomy, or bright fringe. Current acceptance is 464/488 variants across 63/68 atomically
complete families, with boots at 40/44 variants.
Fre's Chain Boots then completed the MM7 Paladin Boots `ornate_mail_boots` geometry as dense gold-bronze fitted mail,
deep-green cuff and sole edging, and simple dull-silver toe caps. All four proposals passed strict magenta despill,
exact-alpha fitting, equipped review, and enlarged review with consistent chain direction, independent feet, open
cuffs, no anatomy, and no edge contamination. Current acceptance is 468/488 variants across 64/68 atomically complete
families, with boots complete at 44/44 variants.
Peasant Belt then completed the MM7 Leather Belt `narrow_belt` geometry as a thin worn tan-leather strap with a tiny
plain buckle. All five proposals passed strict magenta despill, exact-alpha fitting, waist-alignment review, and
enlarged review without anatomy, unrelated equipment, or edge contamination. Current acceptance is 473/488 variants
across 65/68 atomically complete families, with belts at 15/30 variants.
Fancy Belt then completed the MM7 Fine Belt `narrow_belt` geometry as narrow red-brown leather with restrained silver
studs and a small center ornament. All five proposals passed exact-alpha fitting, waist-alignment review, and enlarged
review; four sources used the strict magenta-key path and the troll source used equivalent native-alpha extraction.
Current acceptance is 478/488 variants across 66/68 atomically complete families, with belts at 20/30 variants.
Soldier's Belt then completed the MM7 Strong Belt `medium_belt` geometry as segmented medium-brown leather with square
cold-steel reinforcement fittings and a plain sturdy buckle. All five proposals passed strict magenta despill,
exact-alpha fitting, waist-alignment review, and enlarged review without baked anatomy or unrelated decoration.
Current acceptance is 483/488 variants across 67/68 atomically complete families, with belts at 25/30 variants.
Dragon Belt then completed the MM7 Gilded Belt `jeweled_belt` geometry as an aged-gold interlaced band with a green
center jewel and restrained dark-red side stones. All five proposals passed strict magenta despill, exact-alpha
fitting, waist-alignment review, and enlarged review with the fitted legacy construction retained. Current acceptance
is 488/488 variants across all 68 atomically complete families, with belts complete at 30/30 variants.

The final audit verified all 68 families and 488 active variants, all aggregate preview reports completed without
issues, and native-scale, nearest-neighbor, per-category, both-pose armor, and full-set catalogues were visually
reviewed. A freshly restarted MM9 client then rendered representative Arming Doublet, Coif, Leather Boots, and
Peasant Belt equipment on male, female, minotaur, troll, and dwarf dolls. The five accepted runtime screenshots are
preserved under `tools/mm9_import_discovery/generated_equipment_art/reviews/in_game/`. The 47 focused tests,
`generate_mm9_equipment_variants.py --verify-only`, and the clean OpenYAMM build all pass.

The MM7/MM8 base mapping is complete and validated for 68 MM9 items. Existing Arming Doublet and Broderick's Hauberk
placeholder families are migration candidates from the earlier experiment; preserve them, but do not count them as
complete under this goal until they pass the combined manifest, mapping, provenance, and equipped-composite gates.

This document supersedes `MM9_ARMOR_PAPERDOLL_GENERATION_GOAL.md` for the combined armor, helmet, boot, and belt
placeholder run. The armor-only document and `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md` remain detailed references for
armor anatomy, fitting, chroma keying, and AI review.

## Objective

Generate a coherent MM6-MM8-style fitted paperdoll placeholder family for every imported MM9 armor, helmet, boot, and
belt. Each family starts from the selected fitted MM7/MM8 item variants and modestly transfers the recognizable MM9
palette, material, ornament, and construction from the exact MM9 inventory image and original PCX.

These are intentionally good source-derived placeholders, not claims of final hand-painted production art. They must
fit every supported doll correctly, look aesthetically consistent in game, and remain recognizably based on the MM9
item. They must not look like inventory icons stretched across a paperdoll mask.

All output remains owned by the MM9 world package. Do not alter, recolor, overwrite, or relocate the selected base
assets under `assets_dev/engine/icons/`.

## Scope And Exact Counts

| Category | Items | Suffixes per item | Total variants |
| --- | ---: | ---: | ---: |
| Armor | 35 | 10 | 350 |
| Helmet | 16 | 4 | 64 |
| Boots | 11 | 4 | 44 |
| Belt | 6 | 5 | 30 |
| **Total** | **68** | — | **488** |

This goal does not include shields, weapons, bows, cloaks, gauntlets, jewelry, inventory-icon generation, statistics,
equip permissions, or item effects.

## Binding Authorities

Use these sources in this order:

1. `tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml` owns the target list, legacy base selection,
   normalized tier, geometry profile, selection reason, and MM9 design-transfer facts.
2. `MM9_EQUIPMENT_LEGACY_BASE_MAPPINGS.md` is the human-readable review table.
3. `assets_dev/worlds/mm9/data_tables/items.txt` owns the promoted MM9 item id, category, icon name, original PCX path,
   and current item metadata.
4. The exact promoted MM9 inventory PNG and exact original 64x64 MM9 PCX own identity, palette, material, and ornament.
5. `assets_dev/engine/data_tables/items.txt`, `complex_item_pictures.txt`, and the selected MM7/MM8 fitted assets own
   starting pose, placement, perspective, per-doll proportions, and alpha geometry.
6. The actual OpenYAMM paperdolls and runtime render path own final placement and layer-order truth.
7. `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md` owns the stricter armor-specific prompt, semantic fitting, chroma-key,
   equipped-review, and repair rules where this document does not override them.

Use `/home/pjasicek/github/OpenMM9` and `/home/pjasicek/github/GodotMM9` only to resolve MM9 format or presentation
questions. Do not copy code or artwork from reference projects.

## Output Naming And Supported Dolls

All accepted files use:

```text
assets_dev/worlds/mm9/icons/mm9_item_<global-item-id><suffix>.png
```

### Armor

Armor has a separate right-hand-weapon and empty-right-hand pose:

| Doll type | Weapon pose | Empty-right-hand pose |
| ---: | --- | --- |
| 0 | `v1` | `v1a` |
| 1 | `v2` | `v2a` |
| 2 | `v3` | `v3a` |
| 3 | `v4` | `v4a` |
| 4 | `v5` | `v5a` |

### Helmets And Boots

Minotaur doll type 2 cannot equip helmets or boots. Generate only:

| Doll type | Suffix |
| ---: | --- |
| 0 | `v1` |
| 1 | `v2` |
| 3 | `v4` |
| 4 | `v5` |

Do not invent `v3` helmet or boot art and do not count it as missing.

### Belts

Belts support all five equippable doll types: `v1`, `v2`, `v3`, `v4`, and `v5`.

Type 5 is the non-equippable dragon paperdoll and receives no generated equipment in this goal.

## Required Tooling Architecture Before Bulk Generation

The existing implementation is armor-specific. Generalize it before starting a batch; do not create a second
forwarding layer which leaves two owners for the same accepted output.

1. Replace the armor-only generated-art authority with one equipment authority:

   ```text
   tools/mm9_import_discovery/mm9_equipment_generated_art.yml
   tools/mm9_import_discovery/generated_equipment_art/
   tools/mm9_import_discovery/generated_equipment_art/sources/
   tools/mm9_import_discovery/generated_equipment_art/reviews/
   ```

2. Migrate the existing Arming Doublet and Broderick placeholder families and their evidence explicitly. Retire the
   old acceptance ownership only after the generic generator reproduces the same promoted hashes.
3. Generalize the authoritative generator, fitter, and review-packet tool rather than wrapping the old armor tools:

   ```text
   generate_mm9_equipment_variants.py
   fit_mm9_ai_equipment_variant.py
   prepare_mm9_equipment_ai_review.py
   ```

4. Keep category-specific geometry logic in clear functions or data profiles inside those tools. Armor foot masks do
   not apply to boots; helmet face/head constraints do not apply to belts.
5. Make the generator consume `mm9_equipment_legacy_base_mappings.yml` directly. Do not require manual synchronization
   with the stale armor-only mapping after migration.
6. Preserve one manifest owner, one active-output path, and one regeneration route. Remove or explicitly retire old
   duplicate ownership after migration tests pass.
7. Add `--verify-only`, single-item selection, category selection, and non-promoting staging modes. A verification run
   must never rewrite accepted art.

The existing table-driven `render_paperdoll_equipment_preview.py` should remain the shared rendered-review path. Extend
it only where required; do not duplicate its runtime suffix, offset, or layer-selection logic.

## Offset And Table Integration Prerequisite

`assets_dev/worlds/mm9/data_tables/complex_item_pictures.txt` currently owns only the 35 armor rows. Before promoting
helmets, boots, or belts:

1. Extend the authoritative import/generation overlay to cover all 68 mapped items.
2. Derive each per-doll point from the selected reference item's active engine `complex_item_pictures.txt` row.
3. Apply a geometry-profile-specific correction only when the actual cropped output requires it.
4. Emit category sections for armor, helmets, boots, and belts into the MM9 world table.
5. Validate that each generated item id resolves to exactly one merged complex-picture entry.
6. Render every supported suffix and fail if the runtime uses `(0,0)`, the inventory icon, or an unsuffixed fallback.

The generated output canvas and its table point belong together. Do not compensate for a wrong point by adding empty
transparent margins to the PNG.

## Per-Item Input Packet

Prepare one packet for each item before generating its first suffix:

1. mapping row from `mm9_equipment_legacy_base_mappings.yml`;
2. item name, description, category, normalized tier, and armor skill when applicable;
3. promoted transparent MM9 inventory PNG;
4. exact original MM9 PCX converted losslessly to PNG and enlarged with nearest-neighbor sampling;
5. selected MM7/MM8 inventory image;
6. selected fitted legacy variant for the exact suffix;
7. audited two-color target mask after applying the row's `geometry_profile`;
8. unarmored target doll in the exact pose;
9. selected legacy variant rendered on that doll; and
10. current MM9 candidate rendered on that doll when performing a repair.

The PCX and promoted inventory icon are mandatory even when the legacy source already has similar colors.

## Placeholder Generation Contract

Generate one item and one suffix per image request. Do not ask an image generator for a contact sheet or multiple
runtime sprites in one output.

The selected legacy variant is the edit base. Preserve its fitted perspective, placement, broad silhouette, material
scale, lighting, and anatomical alignment. Apply the `geometry_profile` before generation when it removes coverage
which does not belong to the MM9 item. Transfer the MM9 design modestly:

- preserve recognizable main colors and material;
- transfer distinctive trim, closures, panels, gems, symbols, edging, or restrained ornaments;
- retain the mapped item's rarity/detail level without copying unrelated legacy insignia;
- reconstruct details in the fitted perspective instead of pasting or projecting inventory pixels; and
- keep the result visually compatible with late-1990s MM6-MM8 paperdoll art.

Do not replace a good fitted base with an unrelated newly invented design. If the requested adaptation requires
rebuilding most of the silhouette, stop and correct the mapping or geometry profile first.

## Canonical AI Edit Prompt

Replace all angle-bracket placeholders. Include the mapping row's exact `transfer_focus` text.

```text
Use case: precise-object-edit
Asset type: fitted equipment-layer sprite for a late-1990s MM6-MM8-style RPG paperdoll

Edit the selected fitted <LEGACY_WORLD> <LEGACY_ITEM_NAME> variant into a good placeholder for MM9 <ITEM_NAME>,
paperdoll suffix <SUFFIX>, category <CATEGORY>, geometry profile <GEOMETRY_PROFILE>.

Inputs:
- Image 1 is the selected fitted legacy variant and is the primary edit base. Preserve its exact fitted pose,
  perspective, placement geometry, lighting direction, anatomical alignment, and broad silhouette.
- Image 2 is the audited two-color target mask. It owns the permitted coverage and exact outer alpha geometry after
  the category-specific geometry profile is applied.
- Image 3 is the selected legacy variant equipped on the exact target doll. It shows the required fit and layer order.
- Image 4 is the promoted MM9 inventory icon. It owns the readable MM9 palette, material, ornament, and item identity.
- Image 5 is the exact original 64x64 MM9 PCX enlarged with nearest-neighbor sampling. It is the binding historical
  design reference.

Transfer focus: <TRANSFER_FOCUS>

Make a restrained source-derived adaptation, not a wholly unrelated redesign. Preserve the legacy variant's fitted
construction and MM6-MM8 painted shading while transferring the MM9 item's recognizable colors, materials, trim,
closures, panels, symbols, gems, and ornaments. Reconstruct those details in the fitted pose. Never stretch, tile,
project, or paste the flat inventory icon over the legacy variant.

Keep every visible equipment pixel within Image 2. Do not move, rotate, mirror, widen, shorten, swap, or detach fitted
parts. Do not include the doll, skin, hair, face, hands, unrelated clothing, other equipment, UI, text, floor, cast
shadow, glow, border, or watermark.

Output one equipment layer only on one perfectly uniform solid #FF00FF magenta chroma-key background. No transparency
checkerboard, gradient, texture, scenery, white matte, or shadow may appear in the background. Magenta must not occur
inside the equipment.

Style: hand-painted MM6-MM8 paperdoll equipment, neutral frontal game-sprite light slightly brighter from upper left,
crisp low-resolution readability after downsampling, restrained highlights, coherent material scale, no modern glossy
3D or photographic rendering.

Category constraints: <CATEGORY_CONSTRAINTS>
```

Use these category constraints verbatim as the starting point, then append item-specific facts only from the mapping
and MM9 sources.

### Armor Constraint

```text
Armor pixels only. Construct the neck, shoulders, sleeves, torso, waist, hem, skirt or lower panels around the actual
body and arm pose. Body armor must end before separate footwear, feet, claws, or hooves. Preserve the distinction
between weapon and empty-right-hand arm poses. Do not bake in skin, hands, a weapon, a shield, boots, or a belt item.
```

### Helmet Constraint

```text
Helmet or cap pixels only. Fit the exact head angle and preserve intentional face, eye, mouth, ear, hair, horn, and
neck openings implied by the MM9 design. Do not bake in a face, eyes, hair, beard, skin, neck, body, armor, or plume
unless that plume is an actual part of the MM9 helmet. A closed helm may occlude the face only inside its audited mask.
```

### Boots Constraint

```text
Boot or slipper pixels only. Fit the left and right foot independently, preserve sole contact and leg direction, and
end each shaft at the height implied by the MM9 design. Do not bridge the legs, swap feet, include floor or shadow, or
bake in trousers, greaves belonging to armor, skin, claws, or unrelated leg pixels. For ankle_only_footwear, remove the
legacy shafts and cover only the audited low-foot region.
```

### Belt Constraint

```text
Belt pixels only. Wrap the exact waist perspective and keep buckle, medallions, gems, strap thickness, and rear edges
coherent around the torso. Do not bake in armor, cloth, skin, hands, pouches, a weapon, or unrelated waist pixels. The
belt must not float away from the body or become a flat horizontal inventory strip.
```

## Category-Specific Geometry Gates

### Armor

- Apply the existing per-doll footwear/foot/claw/hoof exclusion masks.
- `short_torso`, `hip_length`, `thigh_length`, and `full_harness` are binding.
- Separate sleeves and shoulders must follow each arm pose.
- Armor alpha must have zero overlap with the excluded footwear/foot region.
- Armor must not contain a separately equipped belt or boots.

### Helmets

- Audit head coverage against the unarmored doll, not only the legacy helmet.
- Define permitted face/head coverage masks for `chain_hood`, `open_nasal_helm`, `closed_face_helm`, `conical_helm`,
  `open_round_helm`, `unique_face_mask`, and `soft_cap`.
- Preserve required face openings and reject accidental skin-colored or eye-like generated pixels.
- Verify that hair or ears are occluded only where the helmet design actually covers them.
- Do not generate a minotaur variant.

### Boots

- Define per-doll left-foot and right-foot regions and a maximum shaft boundary for each geometry profile.
- Reject bridges between feet, crossed/symmetric pasted boots, floating soles, and leg-direction mismatch.
- `ankle_only_footwear` must remove the source boot shafts before the AI edit.
- Do not generate a minotaur variant.

### Belts

- Define an audited waist band per doll and constrain alpha to it.
- Preserve openings and layer order around armor rather than painting armor pixels into the belt.
- Validate all five doll types, especially non-human torso widths and perspectives.
- Reject a belt whose center buckle is visibly off the doll's centerline without design justification.

## Deterministic Chroma Key, Fit, And Alpha

The image-generation result is a high-resolution RGB proposal, never an authoritative runtime canvas or alpha.

1. Replace exact `#FF00FF` background pixels with full transparency.
2. Mathematically unmix/despill only anti-aliased edge pixels blended with magenta, within a narrow edge band.
3. Preserve legitimate purple, red, silver, white, and bright metal details.
4. Crop without losing semantic vertical extent or separating paired pieces incorrectly.
5. Align semantic regions independently when necessary; do not globally stretch a wrong result.
6. Downsample to the exact selected fitted canvas dimensions.
7. Reapply the audited category-specific alpha. Discard the generated alpha.
8. Ensure fully transparent pixels do not retain a white or magenta matte which can bleed under filtering.
9. Assert exact dimensions, exact alpha, zero forbidden-region overlap, no opaque magenta, and no bright fringe.

Small missed regions may be filled only from neighboring newly generated material or a targeted redraw. Never reveal
or paste a stale stretched MM9 overlay underneath the new candidate.

## Equipped-Composite Review And Repair Loop

Stage candidates outside `assets_dev/worlds/mm9/icons/`. Render through
`render_paperdoll_equipment_preview.py` with the candidate icon root and the real MM9 complex-picture rows.

For each suffix, review:

1. isolated candidate at native scale;
2. nearest-neighbor enlargement;
3. unarmored doll;
4. selected legacy base equipped on the doll;
5. candidate equipped on the doll;
6. MM9 inventory icon; and
7. enlarged original PCX.

An AI visual-review call must see the final equipped composite. A clean alpha/hash check is not visual acceptance.

The reviewer must verify:

- recognizable MM9 identity and the row's transfer focus;
- restrained source-derived adaptation rather than unrelated redesign;
- correct MM6-MM8 painted style, scale, and light;
- exact anatomical fit and runtime placement;
- correct category coverage and openings;
- no stretched/projected inventory details;
- no body parts or unrelated equipment baked into the layer;
- no clipping, crossed pieces, floating seams, holes, bridges, or detached fragments;
- no checkerboard, magenta, white fringe, or transparent edge contamination; and
- correct occlusion in the actual paperdoll layer order.

When a defect is found, use one targeted correction:

```text
Change only <AFFECTED_REGION_AND_DEFECT>. Keep the exact MM9 item identity, accepted colors, materials, fitted legacy
pose, audited silhouette, lighting, uniform #FF00FF background, and every accepted region unchanged. Output equipment
pixels only. Do not add body parts, other equipment, background, text, glow, shadow, checkerboard, or white edge matte.
```

Then deterministically refit, rerender, and repeat review. If two repair iterations still require substantial
silhouette reconstruction, stop generating that family and correct its mapping or geometry profile.

## Atomic Per-Item Workflow

Complete one item before starting the next:

1. validate its mapping and source files;
2. import selected reference offsets and render every base suffix;
3. audit and freeze each target mask;
4. prepare all per-suffix input packets;
5. generate one suffix at a time;
6. deterministically key, fit, and validate it;
7. render and visually review the equipped composite;
8. repair or regenerate until accepted;
9. record all accepted suffixes and hashes in the generic manifest;
10. run the generator in staging mode and verify the complete family;
11. promote the complete item family atomically; and
12. update the progress table and preserve its review contact sheet.

Never promote a partial family. A failure in one suffix leaves the entire item staged.

## Execution Phases

### Phase 0: Preflight And Migration

- Run mapping coverage tests.
- Implement the generic manifest/generator/fitter/reviewer ownership.
- Implement helmet, boot, and belt complex-picture output.
- Migrate the two existing armor families without changing active hashes.
- Prove the generic generator reproduces their active outputs.
- Snapshot engine icon hashes and assert they remain unchanged throughout the goal.

### Phase 1: Geometry-Profile Pilots

Complete and approve these pilots before bulk generation:

| Category | Raw id | Item | Why |
| --- | ---: | --- | --- |
| Armor | 225 | Broderick's Hauberk | Existing fitted reference and both arm poses |
| Armor | 220 | Prize Plate | Unique-tier silhouette override and short torso |
| Helmet | 116 | Coif | Chain hood requires removal of the legacy cone |
| Helmet | 231 | Death Cap | Unique skull-mask geometry |
| Boots | 131 | Sabaton | Normal tall plated pair |
| Boots | 366 | Fuzzy Slippers | Mandatory ankle-only crop |
| Belt | 153 | Regal Belt | Normal jeweled waist fit |
| Belt | 208 | Hubris | Unique medallion belt |

If a pilot exposes a systemic category problem, fix tooling and regenerate the pilot before continuing.

### Phase 2: Standard Equipment

Generate normal tier 0-5 items category by category. Finish and promote each item atomically. Checkpoint the manifest,
progress table, and review evidence after every item so the goal is safely resumable.

### Phase 3: Artifacts, Relics, Sets, And Exceptions

Generate tier-7 and silhouette-override rows after their category's standard items have validated the pipeline. Give
set pieces consistent shared palette and ornament, but keep each item's own source PCX authoritative. Do not add set
symbols absent from the MM9 sources.

### Phase 4: Full Audit And Runtime Promotion

- Verify all 488 exact files and hashes.
- Generate per-category and full-set contact sheets.
- Render every supported suffix without fallback.
- Run representative in-game checks for every doll type and category.
- Restart/reload assets to defeat cached paperdoll textures.
- Build OpenYAMM and run all focused tests.

## Provenance And Acceptance Manifest

Each accepted variant records:

- raw MM9 id, global item id, name, and category;
- exact suffix and runtime filename;
- mapping-file hash and selected legacy item id;
- selected legacy fitted asset path and hash;
- promoted inventory image path and hash;
- original PCX path and hash;
- audited target mask path and hash;
- high-resolution generated source path and hash;
- exact prompt or prompt-spec version;
- image-generation tool/model metadata available from the tool;
- deterministic chroma-key, fit, crop, despill, and alpha operations;
- final fitted output path, dimensions, alpha hash, and content hash;
- equipped-preview evidence path and hash; and
- `review_status: reviewed`.

Rejected candidates and incomplete families do not belong in the acceptance manifest. Preserve them only in an
explicit review/rejected area when diagnostically useful.

## Progress

All rows start pending under this combined goal. The two existing armor families are migration candidates, not yet
combined-goal completions.

### Armor: 350/350 Accepted

| Raw | Global | Item | Progress | Status |
| ---: | ---: | --- | ---: | --- |
| 86 | 10086 | Arming Doublet | 10/10 | migrated, reviewed, promoted |
| 87 | 10087 | Padded Leather | 10/10 | reviewed and promoted |
| 88 | 10088 | Hardened Leather | 10/10 | reviewed and promoted |
| 89 | 10089 | Beldonian Hard Leather | 10/10 | reviewed and promoted |
| 90 | 10090 | Scaled Leather | 10/10 | reviewed and promoted |
| 91 | 10091 | Imperial Scale | 10/10 | reviewed and promoted |
| 92 | 10092 | Brigandine | 10/10 | reviewed and promoted |
| 93 | 10093 | Combat Brigandine | 10/10 | reviewed and promoted |
| 94 | 10094 | Brigan der Combit | 10/10 | reviewed and promoted |
| 95 | 10095 | Aklean Bouila | 10/10 | reviewed and promoted |
| 96 | 10096 | Butted Chain | 10/10 | reviewed and promoted |
| 97 | 10097 | Rivited Chain | 10/10 | reviewed and promoted |
| 98 | 10098 | Iron Chain | 10/10 | reviewed and promoted |
| 99 | 10099 | Steel Chain | 10/10 | reviewed and promoted |
| 100 | 10100 | Chain Haubergeon | 10/10 | reviewed and promoted |
| 101 | 10101 | Chain Hauberk | 10/10 | reviewed and promoted |
| 102 | 10102 | Chedian Chain | 10/10 | reviewed and promoted |
| 103 | 10103 | Chain Harness | 10/10 | reviewed and promoted |
| 104 | 10104 | Lachmon Hauberk | 10/10 | reviewed and promoted |
| 105 | 10105 | Trigvanian Mail | 10/10 | reviewed and promoted |
| 108 | 10108 | Ronenguard Plate | 10/10 | reviewed and promoted |
| 109 | 10109 | Field Plate | 10/10 | reviewed and promoted |
| 110 | 10110 | Full Plate | 10/10 | reviewed and promoted |
| 111 | 10111 | Paladin's Plate | 10/10 | reviewed and promoted |
| 112 | 10112 | Heavy Plate | 10/10 | reviewed and promoted |
| 113 | 10113 | Thjoradric Plate | 10/10 | reviewed and promoted |
| 114 | 10114 | Imperial Harness | 10/10 | reviewed and promoted |
| 115 | 10115 | Dark Plate | 10/10 | reviewed and promoted |
| 200 | 10200 | Igdrasine | 10/10 | reviewed and promoted |
| 201 | 10201 | Poltergeist | 10/10 | reviewed and promoted |
| 202 | 10202 | Swordsbane | 10/10 | reviewed and promoted |
| 220 | 10220 | Prize Plate | 10/10 | pilot reviewed and promoted |
| 225 | 10225 | Broderick's Hauberk | 10/10 | migrated, pilot reviewed, promoted |
| 230 | 10230 | Death Cuirass | 10/10 | reviewed and promoted |
| 367 | 10367 | Quilted Armor | 10/10 | reviewed and promoted |

### Helmets: 64/64 Accepted

| Raw | Global | Item | Progress | Status |
| ---: | ---: | --- | ---: | --- |
| 116 | 10116 | Coif | 4/4 | pilot reviewed and promoted |
| 117 | 10117 | Plain Helm | 4/4 | reviewed and promoted |
| 119 | 10119 | Barbute Helm | 4/4 | reviewed and promoted |
| 120 | 10120 | Loaf Helm | 4/4 | reviewed and promoted |
| 121 | 10121 | Bascinet | 4/4 | reviewed and promoted |
| 122 | 10122 | Sallet | 4/4 | reviewed and promoted |
| 123 | 10123 | Dragon Helm | 4/4 | reviewed and promoted |
| 124 | 10124 | Imperial Helm | 4/4 | reviewed and promoted |
| 125 | 10125 | Jarl's Helm | 4/4 | reviewed and promoted |
| 203 | 10203 | Witchbane | 4/4 | reviewed and promoted |
| 204 | 10204 | Brongnoker | 4/4 | reviewed and promoted |
| 221 | 10221 | Prize Skullcap | 4/4 | reviewed and promoted |
| 226 | 10226 | Broderick's Helm | 4/4 | reviewed and promoted |
| 231 | 10231 | Death Cap | 4/4 | pilot reviewed and promoted |
| 236 | 10236 | Fre's Helm | 4/4 | reviewed and promoted |
| 364 | 10364 | Fur Cap | 4/4 | reviewed and promoted |

### Boots: 44/44 Accepted

| Raw | Global | Item | Progress | Status |
| ---: | ---: | --- | ---: | --- |
| 126 | 10126 | Leather Boots | 4/4 | reviewed and promoted |
| 127 | 10127 | Hardened Boots | 4/4 | reviewed and promoted |
| 128 | 10128 | Chain Boots | 4/4 | reviewed and promoted |
| 129 | 10129 | Ronenguard Boots | 4/4 | reviewed and promoted |
| 130 | 10130 | Steel Boots | 4/4 | reviewed and promoted |
| 131 | 10131 | Sabaton | 4/4 | pilot reviewed and promoted |
| 132 | 10132 | Prote der Fatta | 4/4 | reviewed and promoted |
| 205 | 10205 | Walking Boots | 4/4 | reviewed and promoted |
| 233 | 10233 | Death Boots | 4/4 | reviewed and promoted |
| 238 | 10238 | Fre's Chain Boots | 4/4 | reviewed and promoted |
| 366 | 10366 | Fuzzy Slippers | 4/4 | pilot reviewed and promoted |

### Belts: 30/30 Accepted

| Raw | Global | Item | Progress | Status |
| ---: | ---: | --- | ---: | --- |
| 150 | 10150 | Peasant Belt | 5/5 | reviewed and promoted |
| 151 | 10151 | Fancy Belt | 5/5 | reviewed and promoted |
| 152 | 10152 | Soldier's Belt | 5/5 | reviewed and promoted |
| 153 | 10153 | Regal Belt | 5/5 | pilot reviewed and promoted |
| 154 | 10154 | Dragon Belt | 5/5 | reviewed and promoted |
| 208 | 10208 | Hubris | 5/5 | pilot reviewed and promoted |

Update progress only after accepted files, manifest entries, hashes, and equipped-preview evidence exist.

## Required Automated Verification

Preflight must continue to pass:

```sh
python3 -m unittest \
  tools.mm9_import_discovery.test_mm9_equipment_legacy_base_mappings \
  tools.mm9_import_discovery.test_render_paperdoll_equipment_preview
```

Implement and run focused tests for the generalized tools:

```sh
python3 -m unittest \
  tools.mm9_import_discovery.test_generate_mm9_equipment_variants \
  tools.mm9_import_discovery.test_fit_mm9_ai_equipment_variant \
  tools.mm9_import_discovery.test_prepare_mm9_equipment_ai_review

python3 tools/mm9_import_discovery/generate_mm9_equipment_variants.py --verify-only
```

The final audit must prove:

- exactly 68 mapped target items and exactly 488 accepted variants;
- exact category counts of 35 armor, 16 helmets, 11 boots, and 6 belts;
- exact expected suffix sets with no forbidden or substituted suffixes;
- exactly one MM9 complex-picture row for every generated item;
- every selected reference is MM7/MM8, has a compatible category, placement row, and every required source suffix;
- every accepted output has the audited dimensions and exact audited alpha;
- every forbidden-region overlap count is zero;
- all manifest paths and source/reference/mask/output/review hashes resolve;
- no expected runtime lookup falls back to the unsuffixed inventory icon;
- no accepted file contains opaque `#FF00FF`, checkerboard residue, white edge matte, or unintended bright fringe;
- every supported fitted variant renders through the runtime-equivalent preview path;
- active engine icon hashes remain unchanged; and
- regeneration reproduces all accepted world-owned outputs without overwriting them with stale generated data.

Build after code, loader, table, or promotion changes:

```sh
cmake --build build --target openyamm -j25
```

## Required Visual Verification

Automated checks do not replace visual review. Preserve:

- one equipped-composite image per accepted suffix;
- one item contact sheet showing every supported doll/pose;
- per-category contact sheets at native scale and nearest-neighbor enlargement;
- a full-set catalogue with item ids and names; and
- representative in-game screenshots for every doll type and equipment category.

For armor, review both hand poses. For helmets, inspect face/head openings. For boots, inspect both feet and shaft ends.
For belts, inspect waist alignment and armor occlusion. Review rare/set pieces beside their inventory icons and related
set items for identity consistency.

## Completion Criteria

This goal is complete only when:

1. one generic, regeneration-safe equipment pipeline owns mapping, fitting, review, manifest, and promotion;
2. all 68 mapping rows and geometry profiles have passed their category-specific audit;
3. all 68 MM9 complex-picture entries are generated and runtime-valid;
4. all 488 variants have been generated or explicitly migrated, deterministically fitted, visually reviewed on the
   equipped doll, registered with complete provenance, and promoted atomically by family;
5. no supported runtime lookup uses an inventory-icon or missing-suffix fallback;
6. engine/base assets remain byte-for-byte unaffected;
7. all automated verification, contact-sheet review, representative in-game review, and the OpenYAMM build pass; and
8. every progress row records its full suffix count and completed final render.

A pleasant isolated sprite, correct alpha, existing legacy variant, inventory-level color match, or successful asset
lookup does not by itself complete an item. The equipped composite and category-specific fit are the acceptance truth.
