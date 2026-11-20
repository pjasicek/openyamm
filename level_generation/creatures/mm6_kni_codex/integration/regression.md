# Proposed integration regression — not run in this batch

Name: `mm6_knightplate_actor_model_tiers_match_native_height_and_sword`.
World: MM6. Controlled indoor fixture: `6d07.blv`; summon monster IDs **565, 566, 567**.
Use the existing barbarian tier fixture in `game/outdoor/HeadlessOutdoorDiagnostics.cpp` as the local structural
reference: load native frames, initialize actor models, synchronize each summoned actor and inspect posed bounds.
Do not duplicate its gameplay implementation.

| Descriptor | Name | Native alpha × frame scale | Expected height | Proposed bound |
|---|---|---|---:|---:|
| KnightPlate A | Death Knight | 255 × 0.799988 | 203.997 | 195–214 |
| KnightPlate B | Doom Knight | 255 × 0.899994 | 229.498 | 219–240 |
| KnightPlate C | Cuisinart | 255 × 1.049988 | 267.747 | 256–280 |

Measure the body in Standing at several times, without the attached sword. The median model body height is
1.9123855345 m; the configured A scale is 106.671451. B/C use the same scale and `scale_reference: KnightPlate A`.
Check B/A ≈ 1.125009 and C/A ≈ 1.312505, allowing 1% numeric tolerance, alongside the 5% absolute bounds above.
Height is alpha-measured rather than the padded PNG canvas height. Confirm the target sizes visually before adopting.

Verify all eight roles, all three skins, one shared body texture set, four colour and four shadow LODs, 58 joints,
finite posed bounds, and a rigid sword attached at `Sword`. The separate sword has four colour LODs and the same
skin names. Check its crop/mask and blade normals under both indoor and outdoor lighting.

Attack melee impact and the native Dark ranged launch share 0.71875 s; the launch socket is `SwordTip`.
Check ordinary combat movement, role transitions, recovery, death-to-corpse continuity and projectile launch direction.
Verify the conservative neck/head look offsets (35° yaw, 20° pitch) do not hit pauldrons while targeting the party.
Stride 1.35 m is the rounded mean of twice the Walking foot excursions (1.40663/1.28712 m); tune only if actual
movement-speed synchronization shows sliding. The native ranged attack reuses the same animation; no new spell or FX.

Then inspect all three tiers with sprites side by side in `6d16.blv` (Warlord's Fortress) and in a controlled
`oute3.odm` outdoor run. `6d20.blv` is another native encounter map. Include front, side, three-quarter and rear views,
walking/running, attack, hit, fidget, death and corpse, plus all distance LODs. Keep existing MM6 Guard/Barbarian and
MM7/MM8 model/sprite smoke coverage to detect unrelated shared-registry regressions.

Builds, installation, game launches, GPU captures and runtime regression are explicitly assigned to the orchestrator
by MM6_CODEX_BATCH_GOAL.md. None were run by this production session.

## Review round 1 integration delta

Replace only `mm6_kni_sword.glb` with SHA-256 `1d724cff0a0d9a2b28019894494644ab961b90088181b6189ef8e85fd47aaed4`.
The body and `integration/actors.yml` are unchanged. New sword LOD triangles: 2292 / 1146 / 457 / 180.
Inspect dull grey steel and leather, fuller/bevel silhouette, grasp, Attack at 0.71875 s, Death near 0.292 s and
all distance LODs in the native renderer. There is a measured 1.717 mm hidden grip/cuff contact during Death
(under the 2 mm allowance); no blade or hand-furniture contact was detected across eight clips.
Source design and final close-ups are linked in `HANDOFF.md` Review round 1. No new binding, scale, stride,
blow time, projectile marker, clip, rig or body-colour changes are proposed.
