# MM6 New Sorpigal guard (gua) — 3D model, 2026-10-08

Guard / Lieutenant / Captain (descriptors 553/554/555, palettes 748/749/750), built with the
[humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md): closed-fist HD masters → Meshy Smart Topology → own cleanup
and UVs → Meshy API auto-rig → halberd from the native sprite → clips solved from the native keys → retexture
+ head set → region tiers. Runtime: `assets_dev/worlds/mm6/models/mm6_gua.glb` (9,181 tris; LODs 4,588/1,651/549).
Meshy credits: 33 of 60 (Smart Topology 5, rig 5, Dying Backwards 3, body retexture 10, head retexture 10).

## Pipeline (replayable)

| Step | Script / output |
|---|---|
| HD masters | `references_hd/` (Codex edit of the stage-1 masters with closed grip fists), `references_head/` |
| Smart Topology | `meshy/smart_topology_v1`, 14,959 tris, pose mode off (fists kept, right fist has a real tunnel) |
| Coif repair | `scripts/coif_repair.py`: Meshy's coif was a closed cylinder over the eyes; eye window with an inward lip, jaw hug, collar extension |
| Cleanup | `analyse_parts.py` (visibility) → `step1_gua.py`: hidden head faces deleted, region decimation → 8,619 tris |
| UVs | `uv_gua.py` (+ `uv_check.py`, `draw_uv_layout.py`): overlap-free, face window 32 texels/cm, body 9–13 |
| Rig | Meshy API rig (24 bones, no finger chains) → `build_rig_gua.py`: weights by nearest surface point, rigid fists/head, clips resampled to whole frames, feet levelled, wrists damped |
| Halberd | `trace_halberd.py` (outline from native `guawinc0`), `make_halberd.py` (412 tris), `seat_halberd.py` (ray-tested fist tunnel, widened) |
| Clips | `carry_halberd.py` (Standing, Walking, Running), `attack_halberd.py`, `hit_halberd.py`, `death_halberd.py`; solver `gua_rig.py`; chain `rebuild_anim.sh` |
| Twist bones | `twist_gua.py setup|bake` on rig_v6: Left/RightForeArmTwist1/2 (Meshy bone tails are importer guesses ~22 m long, so the forearm is measured elbow → wrist joint); each clip's hand twist baked 45 % / 85 % along the forearm |
| Hand audit | `hand_audit.py` (per-frame skin stretch/area ratios for hand, wrist, forearm, elbow + follow-cam close-ups), `hand_closeup.py` |
| Gate | `pose_audit.py`: penetration ≤ 2 cm, wrist ≤ 60° (one 66° frame mid-fall), forearm twist ≤ 85°, floor ≥ 0 |
| Textures | `prepare_textures.py`, `head_tiers.py`, `../claude_shared/compose_head_set.py`; runtime `build_runtime.sh --install` |
| Regression | `mm6_gua_actor_models_bind_new_sorpigal_guards` (headless `actors` suite) |

## Clips (native timing)

Standing (held carry, 1.0 s), Walking (Meshy, halberd see-saws with the arm swing), Running (Meshy), Attack (0.75 s,
two-handed chop from native keys a–f; the halberd rolls in the fist so the crescent edge leads the downstroke), Hit (0.75 s), Death
(Meshy Dying Backwards frames 4–44 retimed to 1.0 s, right arm re-solved, halberd on the floor), Dead.

## Textures and tiers

- Body 1K (squeezed to u × 0.90; the halberd strip is u 0.905–0.995), head set 1K, ORM with baked AO in R.
- Mail: [native shading transfer](../NATIVE_SHADING_TRANSFER.md) by height (`native_shading.json`), ring detail
  normals; mail ramps from `transfer_ramps`. Sleeves/trousers: palette-family ramps. Coif luminance matched to the
  shirt mail. User review 2159 (mail too bright and flat) → fixed this way.
- Halberd (user reviews 2159/2161): axe and spike have their own atlas cells; the steel is built from the traced
  vector outline (native tone, bevelled bright rim, engraved border, fine noise, bevel normals), because sprite
  pixels are blurry at this density and the restored 2× art draws the spike at a different angle. Wood shaft with
  grain, one blue band under the blade, native-blue gem, dark iron butt.

## Hand/wrist review (2026-10-09)

User asked for a frame-by-frame check of both hands in the attack. Found: right wrist folded 53–57° back in the
wind-up (frames 2–7) and strike (9–10), pinching the wrist skin to ~0.45× edge length; left forearm at the 85° twist
clamp plus 28–42° wrist twist in frames 9–12 (candy-wrapper pinch mid-forearm). Fix: forearm twist bones and an attack
solve that keeps the forearm bone untwisted and prefers twisting over bending (`attack_halberd.py` `TWIST`: wrist
weight 1.6, twist weight 0.4, total twist limit 115°). After: wrist bend ≤ 37° on both hands, wrist-zone stretch
0.80–1.10× (was 0.67–1.23×); close-ups `review/R_close_sheet_v2.png`, `L_close_sheet_v2.png`. Hit and Death were not
re-solved: their forearm bone still twists up to 85° from the elbow (only the smaller hand-to-forearm remainder is
spread by the twist bones); the same `TWIST` solve settings would apply there.

## Halberd edge (2026-10-09)

User review (screenshot): the blade did not slice; the spike led the downstroke. Cause: the axe (crescent) is the
Halberd bone's +X side, but `gua_rig.halberd_frame` and the attack's roll keys used −X, so every roll pointed the
spike forward. Fixed both, and the attack's roll now follows the blade: during the downstroke (frames 7–11) the edge
points along the blade head's velocity, in the wind-up it faces the strike direction (spike leads the lift), eased
from/to the carry roll (max 49° roll, ≤ 38°/frame). Checks `review/slice_sheet.png`, in game
`review/ingame/slice_zoom.png`.

## Strike direction and grip (2026-10-09)

User review (screenshot of the strike end): blade out at the guard's right side, broadside, rear hand high at the
chest with the butt above the left shoulder. The native frontal frames draw the strike at image left only because
they are 2D; native `e` shows the shaft foreshortened and the blade edge-on, i.e. pointing at the viewer. Now:
frame 8 brings the blade up and over, the strike (frames 9–12) points the shaft forward and 40–45° to the right,
10–25° down, right grip 0.34–0.38 m in front of the hips at waist height, left grip at the front of the left hip,
blade landing ~1 m in front; keys chosen with a probe over grip positions and shaft directions that scores both
wrists, twist and fist/wrist clearance from the torso. The rear arm: a closed fist only takes the shaft about 81° to
the forearm, so a hanging rear elbow would need a 65–80° wrist bend; the solver keeps the rear elbow at about
shoulder height (`ELBOW_DROP`, `ELBOW_W`) with the wrist at 25–39°. Wrist bend ≤ 39° on both hands over the clip,
wrist-zone skin 0.72–1.20×, Attack penetration left arm 1.7 cm (3 vertices), halberd 1.5 cm (16 vertices).
Checks `review/slice7_sheet.png`, in game `review/ingame/slice_zoom2.png`.

## Known limits / open

- Rear (left) elbow flares to about shoulder height in the strike: the rigid fist cannot hold the shaft diagonally
  across the palm as a real rear hand does.
- Ring highlights a little less contrasted than the sprite; skin paler than the sprite's tan (offered to the user).
- The coif's eye-window rim is slightly ragged in geometry (texture hides it at game distance).
- Engine change in this work: `game/fx/WorldFxSystem.cpp` treats a missing `sockets` map as no sockets.

## Death at source speed (2026-10-10)

`death_halberd.py` plays Dying Backwards 4..44 at source speed (1.67 s, 40 frames; was 1.67x in 1.0 s): the engine
finishes a longer death before the corpse ([clip timing audit](../CLIP_TIMING_AUDIT_20261010.md)). Replayed: twist
setup/bake, pose audit (as before; halberd >= 0.8 cm above the floor), rig_v7 head split, build. Backups
`work/rig_v{5,6,7}_pre_death_timing.blend`.
