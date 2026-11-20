# MM9 shared-mesh variants: batch brief (2026-11-02, user request)

The user asked to build the MM9 models whose mesh is the same as (or only slightly extends) another model, instead of
buying a new Meshy body for each. The mesh comparison (orchestrator, 2026-11-02;
script `level_generation/creatures/claude_shared/mm9_meshcmp.py` (the original /tmp copy was lost in a reboot), region-wise
surface distance in cm between MM9's own ABC meshes) found:

| Model (MM9 file) | Rows (MONSTERS.txt): skin | Same mesh as | Difference |
|---|---|---|---|
| PeasantHOM2.ABC | 59 Shopkeeper: PeasantHOM2a | PeasantHOM1 (built: `mm9_peasanthom1_claude`) | identical |
| PeasantM7d.abc | 25 Town: PeasantM7d; 27 Shopkeeper: PeasantM7c | PeasantM7 (built: `mm9_peasantm7_claude`) | body identical; ~4 % of head vertices, up to 5 cm (elf ears) |
| PeasantM8d.abc | 23 Commoner: PeasantM8d | ForadDarre (built: `mm9_forad_claude`) | body identical (0.3 cm); head up to 4 cm (elf ears) |
| Hanndl.abc | 260 Hanndl (Gate Keeper): Hanndl | PeasantM6 = Annud (built: `mm9_annud_claude`) | identical apart from one small arm piece (up to 7 cm, 3 % of arm vertices) |
| hag.abc | 245 Old Hag: hag | Yrsa (built: `mm9_yrsa_claude`) | torso and legs identical; head (22 % of head vertices, up to 8 cm) and part of the arms (up to 10 cm) differ |
| PeasantF3.abc | 35 Prisoner: PeasantF3b; 40 Shopkeeper: PeasantF3a | PeasantF1 (built: `mm9_peasantf1_claude`) | torso and arms identical; headwear differs by up to 20 cm; legs ~2 cm |
| wyrd_young.ABC + wyrd_mature.ABC | 265 Wyrde of the Unknown (Morgan): wyrdyoung; 264 Wyrde of the Knowing (Verdandi): wyrdmature | each other | identical: ONE new body, two skins. (`wyrd_old.abc`, row 263, is a different mesh: not in this batch) |
| Peasantboy1.ABC + Peasantboy2.ABC + Peasantboy1e.ABC | 69 Commoner Child: Peasantboy1; 70 Townsfolk Child: Peasantboy3; 73 Commoner Child (elf): Peasantboy2 | each other | Boy1 = Boy2 body (head/hair up to 4 cm); Boy1e = Boy1 body + one 14-vertex head piece: ONE new body |
| PeasantGirl2.ABC + PeasantGirl3.ABC + PeasantGirl1e.ABC | 71 Commoner Child: Peasantgirl2; 72 Townsfolk Child: Peasantgirl3; 74 Townsfolk Child (elf): Peasantgirl1 | each other | Girl3 = Girl2 body (hair up to 2.4 cm); Girl1e = Girl2 body + ears: ONE new body |

Re-run the comparison yourself on your pair before relying on it (`python3 level_generation/creatures/claude_shared/mm9_meshcmp.py <a>:<b>`,
names are file stems; it also reports skeleton match and the residual after removing a rigid shift), and look at both MM9 models side by side.

## The rule: no duplicated bodies
- **Identical mesh, different skin:** a new tier of the existing GLB (region mask + ramps if the skin is a recolour; its own
  1K head colour (+ normal) per tier if it is a different person, as PeasantDM1/DM2 tier B; a new body paint only if the
  clothes are different art). Prefer the cheapest route that matches MM9's skin.
- **Same body + a small extra piece (elf ears, a head piece, an arm piece):** reuse the built body, its rig, weights and
  clips; add/reshape only the differing part (e.g. elf ears: PeasantM1d `mm9_peasantm1d_claude` and PeasantF8 have elf
  ears to learn from), and install as its own GLB (`mm9_<model>.glb`) from the same project, or as a tier if the geometry
  difference can live in one GLB without changing the approved tiers. The approved model's look must not change.
- **Same body, different head (Hag, PeasantF3):** reuse the body, rig and clips; build only the new head/headwear
  (Codex HD head masters per the HD master references; a Meshy job for the head piece only if needed, graft at the neck as
  the hand grafts do; or sculpt/reshape the existing head when the difference is small). Own GLB.
- **New shared body (Wyrde, boy, girl):** one Meshy body on the full approved MM9 humanoid route, the other models as tiers
  or small-piece variants of it. Use MM9's own skeleton and clips (`PeasantChildBoy.abc`/`PeasantChildGirl.abc` are MM9's
  child base rigs if their clip libraries are the ones these rows play: check the DAT objects' `ScriptName`s and
  NPCbase.scr, as Annud did).

## Approved models are frozen
Forad, Annud, Yrsa, PeasantF1, PeasantM7 and PeasantHOM1 are user-approved. Build variants from their project sources into
new outputs (new GLB, or new tiers added without changing the existing tiers). If you must reinstall an approved GLB to add a
tier, prove the existing tiers are unchanged (byte-identical textures/ramps for them, same mesh and clips) and keep a rollback.
Never re-run a step a README says must never re-run (e.g. a project's UV script whose paid paints depend on it).

## Budget (Meshy)
- User, 2026-11-02 evening: **another 1000 credits** for the remaining models. **New floor: the backup balance must stay above 1740**:
  run `python3 tools/creature_meshy.py balance` before EVERY paid job; if backup <= 1740, submit nothing.
- Caps: a variant on a built body **at most 20 credits** (typically one 4K retexture of the existing mesh, 10); a new shared
  body (Wyrde, boy, girl) **at most 60** for the whole family.
- Codex images (HD masters) only through `level_generation/creatures/claude_shared/codex_slot.sh`. Ask for calm, warm
  expressions; never "fierce" or "cold".

## Route, gates, binding, records
Everything in [TOWNSFOLK_BRIEF.md](TOWNSFOLK_BRIEF.md) applies (playbooks to read, MM9 skeleton and clips, `clips_mm9.py` soft
line, binding under the `mm9_actors_yml.lock` flock with `MM9 <row> <role>` descriptors and rows in
`tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated, binding test PASS; map placement is the
orchestrator's), including its "Lessons from wave 1". Also, from the user's review of 2026-11-02:
- **Faces:** pre-screen every face against MM9's: no doubled nostrils (the painted nose must fit the geometry's nose), no
  second lip layer (closed mouth cavity painted as lip, no pink plate), no pale crescent under the lower lid, no second brow,
  no eye-plate band, no Meshy/Codex details painted where the mesh has none (braid beads on ears), no net-like strand
  patterns on skin. Fix scripts: `mm9_peasantf1_claude` (`tweak_pf1.py`, `warp_nose_pf1.py`, `project_face_pf1.py`),
  `mm9_peasantdm1_claude/scripts/fix_ear_pdm1.py`, `mm9_peasantm2_claude/scripts/fix_net_pm2.py`.
- **See-through openings:** cloth is one-sided. Run `mm9_peasantdm2_claude/scripts/see_through_gate.py` on every clip and
  line the rims (`linings.sh`, `rim_lining.py`, `neck_cap.py` in that project) until cuffs, boots, collar and hems show no
  background.
- **Rigid head:** the whole face (lips, chin, jaw) moves with the Head bone (Kira's jaw shear, `mm9_kira_claude/scripts/face_rigid.py`).
- **Hands:** relaxed natural fingers following MM9's hand pose, not splayed claws (`mm9_kira_claude/scripts/finger_pose.py`);
  no hollow sleeve/vambrace ends (`wrist_fill.py`).
- **Ears:** close-ups of both ears and under the jaw, every tier (`mm9_peasantdm1_claude/scripts/ear_views.py`).

Lease: `python3 tools/creature_workspace.py claim --project <project> --identity mm9:<body> --owner <you>` (no `--budget 0`;
the tool refuses it). Status file `devdocs/mm9_rework/overnight/status/variants_<body>.md`. Do not edit the overview page or
the ledger: the orchestrator does. At most 2 viewer shot scripts at once, no Chrome left running, kill only literal PIDs you
started. Never run git add/commit/stash/reset/restore --staged; do not touch `game/` or `engine/`; no Vulkan builds.

Final report: what changed, credits spent (with balances), which approved files were touched and the proof they are unchanged,
gates, sheets read (absolute paths), what to look at, what you did not check.

## Memory (user, 2026-11-02: an OOM killed the session at ~110 GB)
- Run every Blender or heavy Python job under a hard cap: `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 <cmd>`
  (raise to 20G only for one job that truly needs it). At most ONE Blender process of yours at a time, `--threads 4`.
- No unbounded sampling/arrays (point clouds, per-pixel loops over 4K x many views): bound sizes, process in chunks.
- After a reboot or kill: check for half-written exports/textures, verify installed GLB hashes, and check Meshy job status before
  ever resubmitting a paid job.

## Face lessons added 2026-11-02 (after this brief was first written)
- Review faces zoomed, in the viewer's own lighting, in front close-up, 3/4, TRUE PROFILE, low 3/4 from below and party view.
- "Two mouths"/pout: Meshy can leave loose lip pieces floating over the face (boys): delete those, then sculpt subtle lips into
  the face surface (`mm9_peasantboy_claude/scripts/lip_sculpt.py`); a flat painted band reads as a sticker.
- Never smooth geometry, relax normals or flatten the normal map over Meshy's nose/mouth to hide paint faults (it erased the
  Wyrde's good modelled nose and lips): fix the paint on the geometry; compare with a clay render of the untouched Meshy head.
- Painted nose wider than the geometry reads as a "ghost nose" (girls): warp the paint to the geometry (`warp_nose_pf1.py`).
- Head/body seam lines at the neck: average the normals across the seam and feather both textures to one tone.
- Receding chin / swollen under-chin only shows in profile (PeasantF3).
- Finalise all face geometry (mouth, lips, lids, loose lip pieces) BEFORE the head paint; never move face geometry after
  painting (PeasantM3 and the girls: lips and paint ended up disagreeing).
