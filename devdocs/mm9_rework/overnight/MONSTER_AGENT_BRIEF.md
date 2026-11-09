# Overnight monster agent brief (2026-10-30)

You build **one** MM9 monster body (or the pair you are named), complete and installed, unattended. The user is asleep and nobody
answers questions. Decide what you can, write down what you could not, and keep going until the body is done or has failed
twice seriously. Do not re-delegate: you are the worker.

## Read first
1. `devdocs/mm9_rework/OVERNIGHT_MONSTERS.md`, in full. Its **Quality rules**, **Budget** and **Rules for this repository** bind you
   as hard requirements, on top of the briefs.
2. `level_generation/creatures/claude_shared/MM9_HUMANOID_BRIEF.md` and `MM9_ANIMAL_BRIEF.md`, in full, plus everything they send
   you to. Non-humanoid bodies follow the animal brief's route.
3. The approved work: `mm9_imp_claude`, `mm9_lich_claude`, `mm9_skeletonwarrior_claude`, `mm9_yrsa_claude/v2`. Reuse their scripts,
   and do not change those projects.

## Budget gate, before EVERY paid Meshy job
Run `python3 tools/creature_meshy.py balance`. If the backup balance is **<= 3785** or under 500, submit nothing more: finish what
you can with what you have and say so. Up to 40 credits for your body.

## Status file
Keep `devdocs/mm9_rework/overnight/status/monster_<body>.md` current at each milestone (phase, lease, credits so far, what is done and
verified, what is next, background processes). If your session dies, another agent resumes from it and from the project's files.

## Lessons from tonight's bodies (read before you start)
- **Do your own second attempt.** If a gate fails, fix it before reporting. Report a failure only after a second serious try, with numbers and why. Every first report tonight went back for a second pass.
- **Measure from the start, not at the end:** collapse, arm and hand, cloth and strips through the body (thighs AND torso), and jitter against MM9, on the first rig. Half-joint helpers on shoulders, elbows, hips, knees and neck, with hinge pivots at the outside of the bend, cut folds by half or better on the Mummy.
- **Hand corrections:** clearing a hand must not fail jitter, and smoothing must not put the hand back in the body. Solve on keys and fade at clip ends. The Zombie's `hand_rest.py` left 6.6 deg/f; the Mummy traded one gate for the other.
- **Strips and ribbons:** a rigid strip stands off as a shard in sitting, crouching and dead poses. Skin it from the triangle under it (Mummy). A band pinned on a limb can go through the chest in attacks: check that too. Measure braid and hair tips against the robe.
- **Held weapons:** the fist closes round the shaft, thumb on target, no finger through it, in every clip (Guard failed this). Check the weapon against the body in Death and Dead.
- **Compare with MM9 by eye, tier by tier:** tone (Guard tier A far too orange, Zombie bands read as tiger stripes), hair that MM9 does not have (Ghost, Dripper), and collars or flaps of hair at the neck.
- **UVs:** read the UV report before any paid retexture. Do not put two heads on one Meshy upload (Guard: 10 credits lost, heads crossed).
- **Faces:** a shared central face plus tier paint can give doubled irises or a seam (Honk). Look at each tier's head close up.
- **Open robes:** a corpse seen from the feet needs a lining and a plain dark cap. Boots keep leg weights only.
- **Per-tier images:** one shared set + mask + ramps is the rule. A true design difference may use its own part or image: keep it to the part that differs (Zombie's torso, 6.3 MB), record it as a deviation with the memory cost, and confirm per-tier binding on every LOD.
- **Close-ups must frame the joint they name.** Strips for every tier, and playback at normal speed (`run_creature_review.py ... playback`).
- **Script clips** nothing drives (Wakeup, Resurrect, Coffin) are measured and reported, but they do not hold up a body.
- **Rows at half scale** keep the sprite row height: record that the health bar floats.
- **Mixed references:** a Codex image filter may refuse weapon prompts. Do not reword around it: build the weapon from MM9's outline.

- **Bone lengths:** `mirror_source.py` breaks limb lengths on an asymmetric bind (it wrecked the Highwayman's legs). Build in raw ABC space with `mirror_glb.py` last unless the bind is symmetric, and run `python3 level_generation/creatures/claude_shared/bone_length_audit.py <glb>` on every build: no limb joint may change by over 10 %.
- **Collapse gate:** copy `mm9_evilsorcerer_claude/scripts/collapse_gate.py`, which reads every LOD0 primitive. The cat's and the mummy's read only the first.
- **`clips_mm9.py`:** a moved hip pivot stretches the hip through its offset path. Use `ORBIT` from `mm9_ghoul_claude/scripts/`.
- **One set first:** the Ghoul carried three tiers on one texture set. Try that before any per-tier image. Region masks mix in order, also in the shader: subtracting a later mask from an earlier one bleeds base colour as smudges.
- **`cast:`** goes under `animation:` in `actors.yml`, not `clips:`. A wrong binding turns everyone's regression red.
- **Never kill by grep or script name.** Other agents run scripts with the same names (Monk killed the Nosferatu's strips this way). Kill only a literal PID you started and verified by parent and working directory.
- **Head projection needs occlusion (user, Guard, 2026-10-31):** a Codex view projected through a helmet painted the face onto the helmet and the helmet onto the face: four eyes, rivets on the throat. On any layered head (helmet, hood, crown, collar, mask) project with a visibility test per layer, or paint each layer from its own view. Check every tier's head at full size from front, quarter and side, not from a small sheet.
- **Hands in wide sleeves (user, Honk female, 2026-10-31):** a thin forearm with a small hand bent off the arm axis reads as a bad graft. Measure forearm width, hand length against the face, and wrist angle against MM9, and look at the arm from the front in Standing at full size.
- **Carry every MM9 clip (user, Guard, 2026-10-31):** do not drop clips because nothing drives them yet. Bind extras in `script_clips` (`sleep`, `aware`, cower set, second deaths, backpedal), as `mm9_clansoldier_claude` does, and list any you leave out with why.
- **One paint source per face feature (user, Highwayman and Gezzampt, 2026-10-31):** painted eyes or teeth that disagree with the real geometry give four eyes and two rows of teeth; two blended views give a double nose and beard. Fade the head set into the neck with no patch edge. Read each tier's face at full size, front on.
- **Grafts and grips (user, Trellborg, 2026-10-31):** a grafted hand must be welded to the forearm with no gap in any clip, and a weapon's grip must pass through the closed palm: check the fist from the palm side by eye, as well as the finger numbers.
- **Viewer shots are heavy:** each headless Chrome renders on the CPU. Run at most 2 shot scripts at once. Before you finish, make sure none of your Chromes is left running (`ps` for your project's viewer URL in `/tmp/openyamm-viewer-shots-*` profiles). Tonight 14 leaked and pushed the load past 300.

## Before you report
- `README.md` in the reference format, ending "User artistic acceptance: not recorded".
- Viewer shots and sheets that you have looked at yourself (Read the PNGs). Numbers alone are not acceptance. Sheets must include:
  MM9 vs ours; every tier; texture close-ups; close-ups at knees, groin, armpits, elbows, neck and mouth in sitting, crouching and
  death poses (as far as the body has them); frame strips of every clip, including attack, hit and death.
- Collapse gate per clip and joint region; never excuse a fold count because a shot looks clean.
- In-game check with `--assets "$PWD/output/mm9_rework/assets_dev"` and a unique `--isolated` name.
- Run `python3 level_generation/projects/mm9r_common/review_root.py` so the review root holds your install.
- Release the lease.
- Do not edit `mm9_overview/index.html` or the ledger: the orchestrator does both.

## Final report (short, the orchestrator reads it)
Route and deviations; each gate's numbers; credits; sheet paths; viewer URL; a one-paragraph summary and "what to look at" for
the overview page; **what you did not check**. If you gave up, say why and whether it is installed. Do not call a body finished if a gate
failed: say which gate and by how much.
- Open tube ends (sleeves, collars, boots) must sit inside the body in every pose. Check rings at bind against the torso, not only in shots: the Nosferatu's sleeve tops stood 4.7 cm outside the yoke.
- In `clips_mm9.py` replace `np.where(np.abs(off) > 0.004, off * k, 0.0)` with `np.sign(off) * np.maximum(np.abs(off) - 0.004, 0.0) * k`: the hard cut pops when a drift crosses 4 mm.
