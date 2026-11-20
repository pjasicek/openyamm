# MM7 Necromancer (mm7_m294): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). Jog from
[package h11](../gait_rollout_20261031/h11/README.md). Before: `work/before_anim/mm7_m294.glb` (SHA-256 ed79f5d5…, the
h11 export byte for byte) and `work/before_anim/actors_mm7.yml`.

## Part 1: Jog, the ragged split cape stretched (2026-11-11)

**Audit:** cloth bad Jog 24.0 (Standing 0.9). **Cause:** the h11 jog (2.55 m in 0.74 s, `swing_height` 0.5) throws
the cape strips around the knees; the strips between chains stretch.
**Fix** (h11 composer copied to `scripts/`, reproduces the installed export byte for byte): Jog with `swing_height`
0.35, stride 2.2 m in 0.68 s; cloth settings unchanged. `run_stride_length` 2.5554 -> 2.2003.

| Clip | Cloth bad | Leg | Peak speed |
|---|---|---|---|
| Jog | 24.0 -> 14.2 | 12.2 -> 10.4 | 2.58 -> 2.18 |

Walking (16.3, not in the brief) was tried too: re-simulating its cape with h11's cloth sim over the installed body
(`resim_cloak.py`) made it worse (26.5), so it stays as installed. Checks (`review/finish.txt`, `review/m294_probes.txt`):
gate PASSED (chase Jog x1.03–1.24 both rulesets); winding 0; only Jog samplers changed; bob 4.7 %, toe-out 5°, lowest
-0.6 cm, free-arm contacts R 46 % / 38 mm (installed Jog 49 % / 37 mm, Walking 57 % / 37 mm); floor and gait audits
clean; every-binding regression PASS; viewer check clean. Sheet `review/jog_viewer_before_after.png` (top installed).

Rebuild: `python3 scripts/compose_gait.py work/mm7_m294_pre_gait.glb export/mm7_m294.glb jobs/m294_jog.json`.

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.5** (`scale_keys.py --joints '*' --factor 0.5 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 1.2, 'arm': 15.2, 'head': 21.4, 'spine': 43.1, 'leg': 4.1, 'cloth': 1.5} -> {'hand': 0.9, 'arm': 1.9, 'head': 6.0, 'spine': 9.5, 'leg': 3.5, 'cloth': 1.0} {'peak_speed': (2.55, 1.26), 'amp_p90': (0.1691, 0.0896), 'body_share': (0.271, 0.2)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
