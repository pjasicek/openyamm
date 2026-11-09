# MM9 NPCs: finishing brief (2026-11-04, user request)

The previous orchestrator session (another account) stopped at its weekly limit on 2026-11-02 at about 23:06 UTC, with three
jobs half-done. The user then asked (2026-11-04) to finish the interrupted work **and build the four remaining MM9 NPCs that were
on hold**. A new orchestrator spawned you for exactly one job below. Nobody answers questions mid-job: decide what you can, write
down what you could not, and finish.

## Rules that bind you
Read and follow, in this order of precedence (later wins on conflicts):
1. [RUN2_COMMON.md](RUN2_COMMON.md): git, installs, leases, regression, safe deletes, game runs, reading your own sheets, final report.
   Its credit stop line (3785) is replaced by the budget below.
2. [TOWNSFOLK_BRIEF.md](TOWNSFOLK_BRIEF.md): playbooks to read, MM9 skeleton and clips (never Mixamo), `clips_mm9.py` soft line,
   binding (`MM9 <row> <role>` descriptors under the `mm9_actors_yml.lock` flock, rows in
   `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated, binding test PASS), map placement is the orchestrator's,
   and its "Lessons from wave 1".
3. [VARIANTS_BRIEF.md](VARIANTS_BRIEF.md): no duplicated bodies (run `claude_shared/mm9_meshcmp.py` first), approved models are
   frozen, the face pre-screen list, see-through linings, rigid head, relaxed hands, ears, the **memory rules** and the
   **face lessons**.

Hard points repeated because they were broken before:
- **Memory:** every Blender or heavy Python job under `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 <cmd>`;
  at most ONE Blender process of yours at a time, `--threads 4`. Up to eight agents run at once on this machine (user raised the cap from five, 2026-11-04).
- **Meshy:** only through `tools/creature_meshy.py`; run `python3 tools/creature_meshy.py balance` before EVERY paid job; if the
  backup balance is <= 1740, submit nothing. Caps: a finishing job at most 20 credits; a new body at most 60.
  Check a job's status before resubmitting anything after an interruption: never pay twice.
- **Faces:** finalise face geometry before the head paint and never move it after; never smooth or relax a Meshy nose/mouth to
  hide paint faults; after two failed patch passes on a face, repaint fresh (Meshy 4K head retexture on the final mesh).
  Codex HD masters: ask for calm, warm expressions. Review every face zoomed in the viewer's lighting: front close-up, 3/4,
  TRUE PROFILE, low 3/4 from below the chin, party view; every tier; against MM9's face.
- **Cloth checks from every side, every tier:** the user also looks from behind and slightly below. PeasantF4 r40 passed its
  front/3-4 sheets on one tier and still showed inside-out sleeve walls from the back on the other tier. Sheets for any cloth or
  see-through fix include back, back 3/4 and low back views for every tier.
- **Normal edits need a smooth falloff:** turning the normals of a downward-facing region (nose underside, under-chin) to cure dark
  top-light shading is allowed, but as a weight fading over several cm, never a hard region: Fre r36's hard-edged under-chin edit made
  the lower face read as a separate, differently lit panel (user, 2026-11-04).
- **Faces must be symmetric:** check the lower face left against right with a midline overlay in the front close-up. A lopsided
  jaw from Meshy's own head is still a fault: symmetrize the geometry from the good side before painting (half-orc women, 2026-11-04).
- **Viewer:** the review server runs on `http://127.0.0.1:8912/` (repo root). Do not start or kill it. At most 2 viewer shot
  scripts at once, no Chrome of yours left running.
- Never git add/commit/stash/reset/restore --staged. No `game/`/`engine/` edits, no engine builds, no Vulkan.
- Do not edit `claude_shared/mm9_overview/index.html` or the ledgers; keep your status file current.

## Jobs

### Job 1: half-orc women HOF1/HOF2 (finish)
Project `level_generation/creatures/mm9_peasanthof_claude/`, lease `mm9:peasanthof`, status `status/townsfolk_peasanthof.md`.
Installed 2026-11-02 21:46 (`mm9_peasanthof1.glb` rows 61-63, `mm9_peasanthof2.glb` row 64). A fix round was running when the
session stopped: exports `export/mm9_phof2_*` from 23:45 and `review/sheet_faces_final_r2.png` (00:06) exist but are NOT installed
and their gates were not read. First work out from the README, status file, `work/` logs and file times what that round already
did. The coordinator's notes for that round (2026-11-02 20:52), all still to be closed:
1. HOF2 row 64: the sleeve poke (grafted right-hand flap over the cuff, Running 27 mm / Death 25 mm) must reach 0 mm; the left-wrist
   see-through ring (41-87 px in every clip) must close (re-weight the flap fully to the hand/forearm or trim it and cap the wrist
   like `mm9_kira_claude/scripts/wrist_fill.py`; line or cap the left cuff).
2. Hair, HOF1 a/b: reads as a smooth dark-brown leather helmet; MM9's is a copper-red bob with braids framing the face. Fit the hair
   to MM9's silhouette (overlay), brighten toward MM9's copper/auburn, give it strand texture.
3. Faces: tier A pale, doughy and blank; MM9's are warm and ruddy with tusks. Warm the skin, keep tusks, a gentle closed smile is
   fine. Tone the pale pink ears to the face skin. Two patch passes at most, then a fresh head paint on the final geometry
   (15 credits left in the body's 70 cap).
4. HOF1 Death legs through the skirt 5.6 cm: push the skirt out in that clip or pull the thighs in.
Then: viewer sheets (front close-up, 3/4, profile, low, party, full body vs MM9) for all three tiers, before/after, read zoomed;
rerun failed gates; reinstall; binding test.

### Job 2: Igrid (wyrd_old, row 263) and the Bembridge Scholars (rows 274/275) (finish)
Projects `level_generation/creatures/mm9_wyrdold_claude/` and `mm9_scholar_claude/`, leases `mm9:wyrdold` and `mm9:scholar`,
status `status/variants_wyrdold.md` and `status/townsfolk_scholar.md`. Both were reinstalled at 23:59 / 00:02 UTC in the middle
of a coordinator review round, so the installed GLBs carry fixes whose gates were only partly run, and Igrid's README was being
written. First verify the installed GLB hashes against the project exports and the READMEs, and finish the records. The round's
notes (2026-11-02 22:00), close every one:
- Igrid: (1) the grey area above the circlet must read as a soft white linen coif under the hood (cloth, folds), not a bald cap;
  (2) wrinkles must be natural creases, not a painted orange net; (3) Death: hand into the body, see-through mid-fall, sleeve R,
  legs through the robe. README says r5 is close (Death torso 350 px at one 3/4 view, right hand 4.1 cm in one frame): finish.
- Scholars: (1) tier B's dark gaps at the jaw sides between beard and face: close them; (2) B's stern downturned mouth: MM9's
  Master Scholar smiles slightly, lift the corners (geometry first if needed, then paint); (3) shoes through the robe in Running,
  Death, Cower: tuck them inside the hem; (4) Fidget left hand 5.3 cm: prove with a gate run without the inner linings that the
  linings confuse the gate, or fix the arm. Also the faint ear outline on tier A's hair.
Up to 10 credits each for a fresh head paint if a face needs it. Do Igrid first, then the Scholars; one Blender at a time.

### Jobs 3-6: the four NPCs that were on hold (new)
One agent per body. Rows from `mm9/extracted/DATA/DATA/MONSTERS.txt`; models in `mm9/extracted/MODELS/MODELS`, skins in
`mm9/extracted/SKINS/SKINS`.

| Job | Project | MM9 model / skin | Row |
|---|---|---|---|
| 3 | `mm9_krohn_claude` | KROHN.abc / Krohn.dtx | 255 Krohn |
| 4 | `mm9_fre_claude` | FRE.abc / Fre.dtx | 256 Fre |
| 5 | `mm9_skraelos_claude` | SKRAELOS.abc / skraelos.dtx | 257 Skraelos |
| 6 | `mm9_greenman_claude` | GREENMAN.abc / greenman.dtx | 266 Green Man |

Start with `mm9_meshcmp.py` against every built MM9 body (`level_generation/creatures/mm9_*_claude`) and look at the MM9 model
with its skin: a variant of a built body (cap 20 credits) beats a new body (cap 60). Check which clips its DAT objects' scripts
play. If the body is not a humanoid, follow the MM9 non-humanoid route (Meshy mesh on the MM9 skeleton with MM9's clips, see
`mm9_dragonfly_claude` and the quadruped playbook) and record why. Binding: `MM9 <row> <name>` descriptor, row in
`mm9_npc_actor_rows.tsv`, tables regenerated, binding test PASS. Status file `status/townsfolk_<body>.md`.
Reference projects for unique characters: `mm9_sigmund_claude`, `mm9_kira_claude`, `mm9_markel_claude`, `mm9_wyrde_claude`,
`mm9_wyrdold_claude`.

### Job 7: dwarf women DF1-DF4, ears (user review 2026-11-04)
Project `level_generation/creatures/mm9_peasantdf_claude/`, lease `mm9:peasantdf`, status `status/variants_peasantdf.md`.
User: "df1-df4 - check if something can be done with their ears" (`review/user_20261104/ears.png`: in a low 3/4 close-up the ear is
a flat painted outline on the side of the head, no real ear shape). Compare with MM9's dwarf women's ears (with their hair), then give
every tier a real ear: reshape/extrude the existing ear area or add a modelled ear (procedural ears on the head bone were used on the
half-orc women, `mm9_peasanthof_claude`; ear checks `mm9_peasantdm1_claude/scripts/ear_views.py`), tucked into the hair where MM9's hair
covers it, painted as skin toned to the cheek; no paint outline left on the cheek. Also in the same screenshot: a hard horizontal
seam across the lower neck and faint polygon crack lines across the cheek and jaw; fix them if they are the same build step
(neck seam: average normals and feather both textures to one tone). The user has not approved DF1-DF4 yet; the earlier pendant and
temple fixes must stay. Viewer ear sheets (both sides, low 3/4, party) before/after, every tier, read zoomed. Cap 20 credits.

### Job 8: PeasantF4 forearm sleeves (user review 2026-11-04)
Project `level_generation/creatures/mm9_peasantf4_claude/`, lease `mm9:peasantf4`, status `status/variants_peasantf4.md`.
User: "the arm part from elbow down has like transparent parts or like holes in the sleeve" (`review/user_20261104/6.png`, `7.png`,
`8.png`): under the elbow-length outer sleeve the forearm sleeve shows olive/dark-green jagged fragments and translucent-looking
patches (one-sided faces, back faces or z-fighting between the forearm sleeve and the outer sleeve's inner side / lining), and the
back view shows dark see-through areas. Also visible: jagged spikes at the bodice hem over the apron belt (both sides) and small light
triangles on the chest front (holes). Find the cause per artefact (lining winding, missing faces, overlapping shells, a wrong
material class), fix all of them, then run the see-through gate on every clip and the sleeve poke gate. Viewer sheets of the arms
(front, back, 3/4, low) and torso before/after, read zoomed. Cap 20 credits.

### Job 9: PeasantF2 neck graft (user review 2026-11-04)
Project `level_generation/creatures/mm9_peasantf2_claude/`, lease `mm9:peasantf2`, status `status/townsfolk_peasantf2.md`.
User: "the head graft transition not good, I can see it like it was soldered on her body" (`review/user_20261104/neck_graft.png`,
viewer front close-up): a dark jagged band runs along the head/body boundary above the necklace, and the neck skin (pale pink, head
paint) meets the chest skin (warm orange, body paint) at a hard line. Make the neck flow into the chest: no dark band (find whether it
is paint, a gap/overlap in the geometry, or shading across the seam), one skin tone across the seam (feather both textures to a shared
tone over a few cm, average the normals across the seam), the necklace stays intact. Also in the same shot, fix while you are there:
a thin vertical midline line down the forehead, nose bridge and neck (mirror seam), and nostrils that still read as dark blots. Do not
move face geometry; paint and seam normals only unless the band is geometric. Viewer front close-up, 3/4, profile, low 3/4 and party,
both tiers, before/after, read zoomed. Cap 20 credits.

**PeasantF7, same job** (the same agent built F2 and F7 with the same graft; project `mm9_peasantf7_claude/`, lease `mm9:peasantf7`,
status `status/townsfolk_peasantf7.md`). User: "peasantf7 the same + the black stuff on her upper lip"
(`review/user_20261104/neck_graft.png`, `upper_lip.png`). In the shots:
- the same dark band along the graft above the necklace, plus dark V-shaped notches on the neck at the graft line, a dark wedge under
  the chin, pale V / M marks on the chest below the necklace and a stray dark tag on the left shoulder (likely shading facets on
  split normals or paint left from the old graft: find out which);
- a black triangle in the middle of the upper lip and a dark slit between the lips (mouth cavity or a gap showing through): the
  mouth must read closed and clean, lips one continuous shape;
- nostrils still dark brown blots (soft small shadows on the real openings only).
Fix F2 first, then F7 with the same method; both tiers each.

## Final report (short; the orchestrator pre-screens before the user sees anything)
What changed; each gate's numbers before and after; credits spent with balances; absolute paths of the sheets you read, including
the face sheet (front close-up, 3/4, true profile, low 3/4, party, every tier) and the full body vs MM9; the viewer URL; a
one-paragraph "what to look at"; **what you did not check**. Do not call anything finished if a gate failed: name it and by how much.
