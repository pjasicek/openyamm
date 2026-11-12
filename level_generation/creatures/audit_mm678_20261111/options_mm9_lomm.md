# MM6–MM8 rework options: MM9 and LoMM rigs and clips (2026-11-11)

This is a research note for the MM6–MM8 3D monster audit (`bound_models.json`, 185 GLBs). Nothing was built, bought
or installed. Every number was measured read-only with the repository's own readers:
`tools/mm9_import_discovery/convert_abc_model.read_abc` for ABC files, `extract_rez.py` for LoMM `MODELS.REZ`, and
`claude_shared/texture_quality.py` for GLBs. The throwaway census scripts were not kept. To redo the count, loop
`read_abc` over the files and print `nodes`, `animations[].name` and their key times.

## 1. How the MM9 creatures were made, and why they look better

### The two routes side by side

| Step | MM9 route (`claude_shared/MM9_ANIMAL_BRIEF.md`, `MM9_HUMANOID_BRIEF.md`) | MM6–MM8 route as installed (`CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, `CLAUDE_QUADRUPED_PLAYBOOK.md`) |
|---|---|---|
| Reference | Codex HD masters **rendered from the MM9 3D model and its full-colour DTX skin** (Magreeb: renders with the skin ×4 plus a top view, `mm9_magreeb_claude/README.md` Route 0). The views agree with each other because they come from one real 3D body. | Codex HD masters **invented from small native sprites** (`CLAUDE_HD_MASTER_REFERENCES.md`). Codex has to make up the 3D shape and the back and side detail. |
| Mesh | Meshy Smart Topology 15k from the three-quarter master, cleaned (the wolf: voxel remesh of a hidden inner shell and fur layers), then **fitted onto the MM9 body**: ICP of the core, head ICP and a chain fit per limb (`fit_magreeb.py`, `fit_quad.py`). The proportions come from an artist-made model. | Meshy Smart Topology (8k for quadrupeds). The proportions come from the sprite reading. Joints are read from mesh slices (quadrupeds) or a Meshy auto-rig plus ring fits (humanoids). |
| Skeleton | **The original MM9 ABC skeleton**, with bone names unchanged (`convert_abc_model.py`). Weights come from the nearest MM9 vertex per chain and are then diffused (`rig_body.py`). Humanoids also get grafted five-finger MPFB hands with 15 bones per side, driven from MM9's finger curl (`finger_alias`, Yrsa v2). | Humanoids: the Explosive RPG pack "humanoid set" skeleton (`B_*` bones; 106 of 185 GLBs), or Mixamo (5). Non-humanoids: our own rigs (74) with automatic heat weights. |
| Clips | **MM9's own keyframed clips**, made by animators for that exact body: PCHIP resampled at 30 fps, loop seams closed, and MM9 clip events used as contact times and sockets (`clips_mm9.py`; the dragonfly's `Socket_Mouth`). Corrections are solved on keys or low-passed and checked with `jitter_gate.py` against the untouched MM9 clip. | Humanoids: library clips (the humanoid set, Mixamo) retargeted by world-rotation copy. Then a long chain of repairs: feet, toes, foot pitch, floor, arm clearance, grip solves, and attacks authored over mocap (natm). Non-humanoids: **procedural clips** (`anim_rat.py`: sine and IK footholds; the spider is "all procedural") or flight authored over a Mixamo idle (Harpy `mm7_m262`, Gargoyle `mm7_m234`). |
| UVs | `claude_shared/uv_atlas.py`: xatlas charts, small charts merged, one texel density with the head about 1.8× denser, brute-force packing at 2048 with a 2 px margin (`TEXTURE_QUALITY_PASS.md` §3). | Most models were built before the 2026-10-30 default: Meshy's own UVs copied back with `transfer_uv.py` (humanoids, `enable_original_uv: false`), or Smart UV Project + pack (older quadrupeds' `uv_export.py`). |
| Paint | Meshy retexture at **4K** on our UVs, downsampled once to 2K colour and 1K normal/ORM. | Mostly **2K** Meshy paints on those layouts (`CLAUDE_CREATURE_TEXTURES.md`, "Sharp textures": "earlier 2K paints on Smart UV layouts … smudged and blotchy"). |
| Grade | Gentle: `grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5`. | The old defaults (fine 0.5, local 0.6, AO 0.7), which the texture recipe found "put blotches on the paint". |
| Tiers | Region mask and ramps fitted to **other full-colour MM9 skins** of the same body (Magreeb C takes MAGREEB2's chroma by luminance percentile). | Region mask and ramps from 8-bit native **sprite palettes** (same engine contract, poorer source colour). |
| Head | A separate head set (Codex head turnaround + head-only retexture) or a denser head chart, plus an anatomy check of chin and jaw. | A 1K head set from a head-only retexture (same idea), but on the 2K paint and older layouts. |

### Measured gap (LOD0 base colour, largest material per model)

| `texture_quality.py` | MM9 installed creatures (112 GLBs) | MM6–MM8 bound (185 GLBs, `texq/`) |
|---|---|---|
| Atlas use, median (p25–p75) | **57.7 %** (53.1–61.3) | **41.8 %** (33.0–49.4) |
| Equivalent fully-used square, median | 1,538 px | 1,331 px |
| Surface on fragments (islands under 8 triangles), median | **0.85 %** | **9.8 %** (p75 18.7 %) |
| Stretch p90, median | 1.15 | 1.86 |
| Models meeting atlas ≥ 55 % | 74 / 112 | 27 / 185 |
| LOD0 triangles, median | 8,839 | 7,598 |

### What plausibly explains the quality gap, most likely first

1. **Paint resolution and layout.** A 4K paint on xatlas charts against a 2K paint on Meshy or Smart UV layouts. The
   texture-pass pilots measured the effect directly. Magreeb: fine detail 2.4×, fragments 10.3 → 2.1 %. Troll
   `mm8_m480`: atlas 18.9 → 56.4 %, and the user found it "clearly better" (`texpass_mm678/HANDOFF.md`). The MM6–MM8
   fragment share (median 9.8 %) is exactly what the recipe calls blotchy, and the old harsh grade added to it.
2. **Animator-made clips on their own skeleton.** No retarget error to repair, so no jitter, no stiff procedural
   cycles, and real secondary motion (tails, hair, cloth and wing chains are bones in MM9, e.g. the Banshee's 135
   nodes). The MM6–MM8 playbooks themselves list the fixes that retargets need: toes curled up 4–7 cm, feet pitched
   about 20°, a corpse 28 cm under the floor. The memory note "library clips over procedural" records the user's
   view that procedural clips lack sway and momentum.
3. **Better references.** Masters rendered from a real 3D model and a 512–1024 px colour skin give Meshy consistent
   views and plausible anatomy. Masters from a roughly 100 px sprite make Codex guess, and Meshy then guesses again.
4. **Proportions from an artist model.** Fitting to MM9 vertices fixes limb lengths and joint placement, so the
   numeric arm and hand gates fight fewer faults.
5. Process: the MM9 batch (2026-10-29 to 11-04) ran with every later gate already in place. Those gates are
   detached parts, flat shading, symmetry, head orientation and mouth cavity checks, and viewer-shot acceptance.
   Most MM6–MM8 models predate some of them.

Items 1 and 5 can be fixed without new rigs: the MM6–MM8 texture pass queue (groups A/B, about 82 models, about
1,200–1,750 credits) is already planned in `claude_shared/texpass_mm678/HANDOFF.md`. Items 2–4 need a new rig and
clips, which is where MM9 and LoMM donors come in.

## 2. MM9 skeletons and clips that fit MM6–MM8 monsters

`mm9/extracted/MODELS/MODELS/` holds 151 ABC files that parse. 61 have both an attack clip and a death clip; most of
the rest are peasant and NPC variants with one clip that take their clips from a parent body (`PEASANTMALE` has 43).
**Every ABC has its own skeleton.** Bodies rigged with 3ds Max Biped share `Bip01 …` bone names, so clips can move
between bipeds by name, but rest poses and proportions differ. Some files keep part of their clips in a child model:
`HIGHWAYMAN`, `DOOKMILITIA` and `PHANTOM` load `FIGHTERBASE` through ChildModels (`mm9_highwayman_claude/README.md`,
`merge_child.py`). Installed results: about 100 bodies in `assets_source/worlds/mm9/models/` from about 100
`mm9_*_claude` projects. Not built yet: `WYVERN`, `RABBIT`, `DUCK`, `GOPHER`, `BUTTERFLY`, `JAJARB`, `PHANTOM`.

| Type | ABC (nodes, clips) and combat clips | Built in MM9 |
|---|---|---|
| Biped, armed fighter | GUARD (35, 20: Hattack1-2, cower, sleep), CLANSOLDIER (30, 23), FIGHTERBASE (32, 12: Hattack2, Rattack1 throw, die1-2; parent of HIGHWAYMAN/DOOKMILITIA/PHANTOM), KIRA (50, 36: wattack1-3, block, dodge ×3; no death clip), NOBLEMAN (38, 15), TRELLBORG (32, 18, club), THRALL (37, 14: BigAttack ×2) | yes |
| Biped, caster | EVILSORCERER (31, 18: rAttack1, ResurrectSpell), LICH (49, 19), LICHKING (36, 20), NOSFERATU (47, 17: RAttack1, resurrect), SCHOLAR (94, 23), MONK (81, 35: Hattack1, cast), EBORA (68, 22: walk, fly, launch, land, Castspell), YANMIR (39, 20: staff, StepOn) | yes |
| Biped, undead and brute | SKELETON (40, 17), SKELETONWARRIOR (33, 21), ZOMBIE (32, 18), GHOUL (54, 16), MUMMY (32, 22), GIANT (39, 17: mallet, rangeattack), BIGFOOT (27, 19), TROGLODYTE (58, 18: full five-finger Biped hands), LIZARDORC (40, 16), COLLOIDALWARRIOR (56, 16) | yes |
| Biped with tail or odd legs | IMP (65, 16: tail, trident), STAGE1DEMON (76, 18: neck, jaw and tongue chains, block, dodge), STAGE2DEMON (105, 19: tail, digitigrade legs), GEZZAMPT (27, 17: `HorseLink` digitigrade legs), TERROR (51, 15: head-mouth on legs) | yes |
| Biped, peasant | PEASANTMALE (45, 43), PEASANTFEMALE (73, 20), PEASANTMALEDWARF (41, 21), PEASANTFEMALEDWARF (53, 10), PEASANTHOMALE/HOFEMALE (35/86, half-orc, 11/13), children; all with hattack1, wince, die1 and cower | yes (about 40 projects) |
| Winged biped | WINGEDMUTANT (87, 16, air-only: HAttackAir1-2, RAttack1, dieair + fall + falldown), EBORA (above) | yes |
| Floating, no legs | GHOST (58, 12: dress chains; no death clip), BANSHEE (135, 17: hair, full air set, ResurrectSpell), EVILEYETERROR (74, 18: eyestalk chains, six RangeAttack sockets), JELLYSPORE (51, 9, water) | yes |
| Dragon | DRAGON = Dragon King (113, 15: fly, land, stand, spitacross, Rattack1-3, WingAttack, die1) | yes |
| Wyvern | WYVERN (80, 15, air-only: fly, flap, HattackAir1-2, dieair + fall + falldown ×2) | **no** |
| Quadruped | WOLF (31, 17), DOG (40, 10; no attack or death), CAT (40, 11; no death), GOAT (38, 12: HAttack1, RunAttack), COW (38, 15), SHEEP/RAM (36), PIG (30, 14), RABBIT (25, 15), MOUSE (7, 3) | all but RABBIT |
| Many-legged | BASILISK (107, 15: six legs, frills, RAttack1), NAGATE (53, 13: six-legged beetle, mandibles), MAGREEB (52, 16: four legs and two claws), DAGRELL (67, 18) | yes |
| Bird | CROW (28, 13: fly, HattackAir1, dieair + fall), HEN (34, 13), ROOSTER (35, 11), GOOSE (21, 8) | yes |
| Serpent and flier | DRAGONFLY (31, 21: S-curved snake body with four wings, Rattack1), FLYINGICKY (62, 19: bat-winged worm), SEAMONSTER (33, 12, swim set), LOBBER (37, 11) | yes |

### Donor map for MM6–MM8 families

Rig key: **set** = humanoid set (`B_*`); **own** = our rig with procedural or authored clips; **mx** = Mixamo.
"Fit" rates anatomy and clip coverage only; it was not tested.

| MM6–MM8 family (GLBs, rig) | MM9 donor | LoMM donor (§3) | Fit |
|---|---|---|---|
| Fighters and soldiers: mm6_fgt, figc, kni; mm7_m222, m226, m230, m406; mm8_m656, m432, m412, m604 (set) | GUARD, CLANSOLDIER, FIGHTERBASE family, KIRA (sword set) | SOLDIER, BANDIT (7 weapon attacks) | good |
| Thieves: mm6_thf (own), mm7_m410 (set) | HIGHWAYMAN + FIGHTERBASE (dagger throw) | BANDIT | good |
| Archers and crossbows: mm6_arc1, mm7_m154, m214, mm8_m416 (set) | none with a bow | PLAYER BASE: Wattack_bow1, Reload_bow, Wattack_Crossbow1 on the 95-node player skeleton (= MM9 PLAYER) | medium |
| Casters: mm6_sor1, dru1, mnk1, cle (own); mm7_m170, m174, m274, m426, m290, m294; mm8_m472, m460, m420 (set) | EVILSORCERER, LICH, SCHOLAR, MONK, EBORA (Castspell) | PLAYER BASE (wand, staff, scroll), MONK (concentrate), PRIEST (no attack) | good |
| Peasants, merchants, nobles: mm6_pman_v2, pfem, pmn2 (mx), natf, natm, mep, mfp, fmp, mer1, nobl; mm7 peasants m302, m312, m322, m332, m342, m352, m362, m372; mm8_m424, m428, m444, m464, m620 (set) | PEASANTMALE (43 clips), PEASANTFEMALE, PEASANT*DWARF, NOBLEMAN | PRIEST, NOBLEMAN | very good: the MM9 peasants are built this way (about 40 projects) |
| Dwarves: mm6_dwa1, mm7_m190, mm8_m632 (set) | DWARF (21, WAttack1-2, Rattack1) | DWARF (same body), DWARFKING (cape and beard chains) | good |
| Goblins: mm6_gob2, mm7_m246, 7m452, m442 (set) | GEZZAMPT or IMP (small bodies), PEASANTHOMALE | **GOBLIN** (68, 17: WAttack, Rattack throw, Threat), ORC | good with LoMM |
| Ogres, trolls, giants: mm6_ogr, mm6_ttn (own); mm7_m461, m414, m162; mm8_m440, m540, m436, m476, m480, m520, m612 (set) | GIANT (mallet, rock throw), BIGFOOT, TRELLBORG (club), THRALL | **TROLL**, TITAN / TITANGRAND (StepOn, Wipe), ORC | good |
| Beast-headed bipeds: minotaurs mm6_min1, m286, m484, m488; mm6_jak1; mm6_wwf (own); mm8_ratman | GEZZAMPT (digitigrade), BIGFOOT, TROGLODYTE; head reshaped by the mesh fit | ORC, TROLL | medium |
| Lizardmen: mm6_lzd, mm8_m404 (set), lizardman_peasant (own); Troglodyte mm7_m418 | **LIZARDORC**, **TROGLODYTE** (same monster) | LIZARDWARRIOR (3 skins), TROGLODYTE | very good |
| Skeletons: mm6_ske (mx), mm7_m398, mm8_m628 (set) | SKELETON, SKELETONWARRIOR | SKELETONWARRIOR (SKELETON has no death clip: it gibs) | very good |
| Other undead: Zombie m438, Ghoul m470, Lich mm6_lch / m270, Wight m430, vampires m422, m468, m464 (set) | ZOMBIE, GHOUL, LICH / LICHKING, NOSFERATU | **WIGHT** (66: 3 hattacks, Rattack1), ZOMBIE, MUMMY | very good |
| Ghosts and genies: mm6_gst, mm6_djn, mm7_m242, m238, mm8_m536 (set) | **BANSHEE** (full air set), GHOST (no death clip) | none | good |
| Demons: mm6_demon (mx), mm7_m178 (set) | **STAGE1DEMON**, STAGE2DEMON, IMP | none | good |
| Winged bipeds: harpies mm6_hrp (own), m262; gargoyles mm6_gar, m234; angel m150; raven man m584; demonfly mm6_wdm (mx) | WINGEDMUTANT (air only), EBORA (ground and air) | **HARPY** (25 clips, ground and air; 83 of 87 nodes shared with the Winged Mutant), **GARGOYLE** (Standup statue ambush) | very good |
| Dragons: mm6_drag, cdr1, drg1, wyrm; mm7_m182; mm8_m492, m548, m616 bone dragon (own) | **DRAGON** (Dragon King: fly, land, breath, WingAttack) | DRAGONRED (same skeleton family: Sleep, WakeUp; no walk or fly) | good; the wyrm `mm6_wyrm` (wingless land dragon) is medium |
| Wyverns: mm7_m434 = mm8_m560 (own) | **WYVERN** (unbuilt, air only) | none | very good |
| Bats: mm6_bat, mm7_m158 (own) | FLYINGICKY (partial) | **BAT** (37: Roost, Launch, air attack, rattack, die + fall) | very good with LoMM |
| Birds: roc m390, thunderbird m552, phoenix m572 (fliers); cockatrice mm6_ckt, chicken 7m504 (ground) (own) | CROW (fly, air attack, death fall); HEN / ROOSTER (ground) | BIRD (5 clips, no attack) | good |
| Canines and felines: dire wolf mm8_wolf, zdog m509, zcat 7m500 (own) | **WOLF** (approved), DOG and CAT (no attack or death) | none | very good for wolves |
| Winged quadrupeds: griffin m258, manticore m278 (own) | WOLF or CAT body; wings would have to be added | none | low |
| Hoofed: unicorn m544, gorgon (bull) m564 (own) | GOAT (HAttack1, RunAttack), COW, RAM | GOAT, COW | medium |
| Rats: mm6_rat, mm7_m382, mm8_m452 (own) | RABBIT (unbuilt, full set), MOUSE (3 clips) | RABBIT | low |
| Spiders and insects: mm6_spi1, mm7_m402; wasp warrior m556; bloodsucker mm6_bld; dragonfly m186 (own) | NAGATE (six legs), MAGREEB; DRAGONFLY / FLYINGICKY for fliers | **SPIDER** (3 hattacks, web Rattack), **SPIDER2** (3 skins) | good for spiders with LoMM |
| Serpents: cobra mm6_cob, sea serpent mm6_seas, sea monster m394, couatl m408; hydras mm6_hyd, m266 (own) | SEAMONSTER (the same monster as m394), **DRAGONFLY** for the couatl (a snake with four wings) | none | good for m394 and m408; none for hydras |
| Snake-bodied humanoids: medusa mm6_med, m282; naga m624; serpentmen m524; salamander m568 (own) | none | none | none |
| Eyes: mm6_bh, mm7_m166 (own) | **EVILEYETERROR** (eyestalks, 6 sockets) | same body | very good |
| Earth and golems: mm6_ert, mm8_m504, golem mm7_m254 (set) | COLLOIDALWARRIOR (slime biped) | **GOLEMSTONE** (full set), ELEMENTALEARTH (no death clip: it gibs) | good |
| Effect bodies and machines: fire, air, water and light elementals; oozes; robot; reactor; boulder; juggernaut; crystal walker; nightmare; fish school; treant; dragon turtle; centaur | JELLYSPORE, GREENMAN (5 clips) and FISH (1) are weak | none | keep own rigs |

How the route would apply: a new Meshy mesh built from **MM6–MM8 HD masters** is fitted and weighted to the donor
skeleton, as in `fit_quad.py`/`fit_magreeb.py`. Humanoids also get the grafted five-finger hands and a head set (memory
rule: MM9 humanoids keep MM9 clips with grafted hands; non-humanoids put a Meshy mesh on the MM9 skeleton). This
differs from MM9 in two ways:

- There is no donor mesh in the MM6–MM8 creature's own proportions to fit to. Either the mesh is pulled to the donor's
  proportions, or the donor's bones are rescaled and its rotation keys kept. That would need a stride and floor pass,
  and contact or reach checks for attacks.
- The masters still come from sprites, so cause 3 above remains.

None of this has been tried on an MM6–MM8 body. `mm6_*`, `mm7_*` and `mm8_*` project READMEs mention no MM9 or LoMM
rig.

## 3. What Legends of Might and Magic offers

`reference/legends_of_mm/Data/MODELS.REZ` (593 resources) was extracted to a scratch folder with `extract_rez.py`. It
holds 580 ABC files; 46 are top-level characters and creatures, plus 9 in `PLAYER/`. All but FISH parse with
`read_abc`, matching `devdocs/lomm/README.md`. The HD skins in `Data/SKINS/*.DTX` are 1.39 MB each, about 512² with
mips (`DRAGONRED.DTX` is 5.6 MB, about 1024²). The meshes are low-poly (215–1,307 triangles), so as with MM9 only the
skeleton, the clips and the skin colours would be reused.

| LoMM model | Skeleton | Nodes / tris | Clips (combat) | In MM9? | MM6–MM8 use |
|---|---|---|---|---|---|
| HARPY | Biped + wing and hair chains | 90 / 572 | 25: ground (Stand, Walk, Wince1, Die1) and air (Launch, Fly, Glide, Land, HAttackAir1-2 kicks, Rattack1, WinceAir1-2, DieAir1-2 + Fall + FallDown) | no (shares 83 of 87 nodes with the Winged Mutant) | harpies, angel, raven man, demonfly |
| GARGOYLE | Biped + wings | 82 / 772 | 18: Standup, Stand, Launch, Flap, Land, HAttackair1-2, Winceair1-2, DieAir1-2 + falls | no | gargoyles |
| BAT | own (`B*` chains) | 37 / 215 | 16: Roost, Launch, StandAir, HAttackAir1, rattack1, WinceAir1-2, DieAir1-2 + falls | no | bats |
| SPIDER / SPIDER2 | own, 8 legs + mandibles | 41 / 773; 49 / 528 | 14 / 13: Hattack1-3, Rattack1 (web), Wince, Die1-2; SPIDER2 also run; skins brown, red, black | no | spiders |
| GOBLIN | Biped + ponytail | 68 / 440 | 17: WAttack1, HAttack1-2, Rattack1 (throw), Threat, Die1-2 | no | goblins |
| ORC | Biped | 39 / 494 | 17: WAttack1-3, Rattack1 (thrown axe), Die1-2 | no | ogres, minotaurs (no MM6–MM8 orc) |
| TROLL / WIGHT | Biped (59 of 61 nodes shared) | 61 / 574; 66 / 873 | 15 / 15: Hattack1-2 (+3 for the Wight), Rattack1 (Wight), die1-2 | no | trolls, ogres; wights |
| TITAN / TITANGRAND | Biped | 65 / 678; 61 / 959 | 18 each: HAttack1-2, Rattack1, StepOn, Wipe, Die1-2 | no | titans, cyclops, gog |
| LIZARDWARRIOR (+ LIZARDMAN skin) | Biped | 61 / 630 | 16: WAttack1-2, Rattack1, die1-2; skins green, brown, blue | no | lizardmen |
| GOLEMSTONE / ELEMENTALEARTH | Biped | 27 / 782; 17 / 502 | 12 / 14: HAttack1-2(-3), Die1-2 (Golem only; the Earth Elemental gibs) | no | golems, earth elementals |
| DWARFKING | Biped + cape and beard chains | 55 / 802 | 16: WAttack1-2, RAttack1, Die1-2 | no (MM9 DWARF is its base) | dwarf boss |
| BANDIT / SOLDIER | Biped | 24 / 458; 26 / 556 | 20: Wattack1-7, Rattack, die1-2; 15: wattack1-2, Die1-2 | no | fighters, thieves |
| DRAGONRED | Dragon (105 of 121 nodes shared with MM9 DRAGON) | 122 / 1,307 | 15: Sleep, WakeUp, Stand, hop, HAttack1, RAttack1-3, WingAttack, Die1; no walk or fly | no | dragon lair boss |
| PLAYER BASE + 8 class bodies | 95-node player Biped, **identical node names to MM9 `PLAYER.abc`** | 95 / 812–926 | BASE: 54 clips: walk, Run, backpedal, swim, climb, crouch set, Jump, taunt1-3, Wattack throw / Crossbow1 / wand1 / staff1 / bow1 / scroll, Reload × 5, Wince0-6, Die0-6, CrouchDie1-2; class bodies: Wattack_Melee1, Wattack_twohanded1 | partly (MM9 PLAYER has 5 clips) | archers, crossbowmen, casters, generic human deaths |
| Also in MM9 (same or reworked) | Basilisk, Dagrell, Dragonfly, Dwarf, EvilEyeTerror, Lich, LichKing, Monk, Mummy, Nobleman, Skeleton, SkeletonWarrior, Troglodyte, Zombie, and the animals (Cow, Goat, Hen, Rooster, Pig, Duck, Rabbit, Gopher) | | Basilisk and Dwarf are identical by node names; Skeleton 27 / 42, Monk 28 / 55: older versions | | prefer the MM9 versions |
| PRIEST, PRINCESS, BIRD | Biped, Biped, own | | no attack clips (BIRD: flap, wince, die) | | townsfolk, birds |

**Lineage.** Both games come from New World Computing on LithTech. Matching node names show shared rigs: LoMM Harpy
and MM9 Winged Mutant, LoMM Red Dragon and MM9 Dragon King, LoMM and MM9 player skeletons. The tools and the rig-reuse
route that work on MM9 should therefore work on these LoMM rigs; the README calls this "expected, not tried".
Clip events (`Rattack`, `Lattack`, `lunge`, `RangeAttack`, `bite`, `Velocity`) give contact times in the same way as
MM9's.

**Verified:** the REZ extraction, that 54 of 55 creature and player ABCs parse, node counts and names, LoMM-to-MM9
node-name overlap, clip names, durations and event strings, LOD0 triangle counts and skin file sizes.

**Not verified:**

- **Clip quality.** No clip was played back or viewed; there was no Blender or viewer use under this task's limits.
- Rest-pose equality between the LoMM and MM9 versions (only names were compared).
- GLB export of a LoMM ABC through `convert_abc_model.py` (needs `pygltflib`).
- Whether LoMM bodies keep clips in ChildModels files, as MM9's Highwayman does.
- Whether any donor's clips survive the proportion change to an MM6–MM8 body.
- Whether reusing MM9 or LoMM skeletons and clips in the MM6–MM8 worlds is acceptable content provenance. MM9's are
  already shipped in the MM9 world; LoMM's are not used anywhere yet. That is for the user to decide.

## Summary for the rework decision

- The **texture gap** (4K paint on xatlas UVs, gentle grade) can be closed without touching rigs: the
  `texpass_mm678/HANDOFF.md` queue.
- The **motion gap** can be closed by donors where anatomy matches closely. These are the best candidates:

  | MM6–MM8 family | Donor |
  |---|---|
  | Wyverns | MM9 WYVERN |
  | Dragons | MM9 DRAGON |
  | Eyes | MM9 EVILEYETERROR |
  | Ghosts and genies | MM9 BANSHEE |
  | Dire wolf | MM9 WOLF |
  | Undead humanoids | MM9 SKELETON, ZOMBIE, GHOUL, LICH, NOSFERATU |
  | Wights | LoMM WIGHT |
  | Lizardmen and troglodyte | MM9 LIZARDORC, TROGLODYTE |
  | Harpies and gargoyles | LoMM HARPY, GARGOYLE |
  | Bats | LoMM BAT |
  | Spiders | LoMM SPIDER |
  | Goblins | LoMM GOBLIN |
  | Trolls | LoMM TROLL |
  | Titans | LoMM TITAN |
  | Couatl | MM9 DRAGONFLY |
  | Sea monster | MM9 SEAMONSTER |
  | Peasants and fighters | MM9 peasant and fighter bodies |

- Families with **no donor** keep their own rigs and would get only the texture pass: snake-bodied humanoids,
  hydras, effect-bodied elementals, machines, oozes, centaur and griffin/manticore.
- A **pilot** should come first: one non-humanoid on an MM9 skeleton (e.g. the wyvern) and one on a LoMM skeleton
  (e.g. the bat or a harpy). It would check proportion fitting and clip quality before anything is queued.
