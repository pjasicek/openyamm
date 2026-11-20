# Dropped MM9 clips, group D (run2-clips-groupD, 2026-10-31): DONE

Bodies: imp, skeletonwarrior (`mm9_skelwar.glb`), lich: every missing MM9 clip, graft only (user decision today, lifting the
approved-project hold for clip grafting); annud, forad: only the clips their MM9 scripts and dialogue play (user decision).
Credits: 0 (no Meshy, no Codex). Leases claimed 13:57 UTC (mm9:imp, mm9:skeletonwarrior, mm9:lich, mm9:annud_redeye,
mm9:forad_darre) and released at the end.

## Counts (ABC clips without bind poses; installed without Dead)
| Body | Source | Installed before | After | Added (role -> clip <- MM9) |
|---|---|---|---|---|
| imp | IMP 16 | 9 | 16 | fidget2 <- fidget2, aware <- aware, hit2 <- wince2, death2 <- die2, dead2 (die2 held), backpedal, backpedal_run; attack_melee2 -> AttackRanged (MM9 Hattack1 = Rattack1's keys) |
| skelwar | SKELETONWARRIOR 20 | 12 | 20 | search, attack_melee_old <- Hattack1OLD, attack_ranged_old <- RAttack1OLD, hit2 <- wince2, death2 <- die2, dead2, backpedal <- BackPedal, backpedal_run; fidget2 -> ResurrectSpell (same keys) |
| lich | LICH 18 | 15 | 18 | death2 <- die2, dead2, backpedal, backpedal_run |
| annud | PEASANTM6 61 (PeasantMale 43 + own + work loops) | 8 | 14 | cower, conv1 <- conv1, conv3, bow, play_death, play_getup; conv2 -> Talk (installed) |
| forad | FORADDARRE 6 + PeasantMale 43 | 9 | 15 | cower, sit, agree, applause, argument_speak6 <- Sc2_Forad6, argument_speak20 <- Sc2_forad26 |
Left out: none on imp, skelwar, lich. Annud and forad: every library clip their scripts do not play (lists in each README),
reason "not played by this NPC".

## Which clips the shopkeepers' MM9 scripts play
- Annud's body = DAT class ShopkeeperHuman2MaleA (row 54, all such shopkeepers). Scripts on those objects (all world DATs):
  NPCbase.scr (row default) and retainer.scr -> NPCBase.inc -> BaseRun.inc `LoopAnim Cower`; Trislan.scr (Guberland City play):
  conv1, conv2, conv3, stand (no such clip: Standing), Play_Death -> Play_getup, Bow. shopkeeper.scr, npcshopkeeper.scr (empty
  anim parameter), HideModel.scr (Annud on the Isle), NPC5/61/128/129/142.scr, BankOrb.scr: none.
- Forad: forad.scr (`playanim bow`, installed) and basemelee.scr (Afterworld) -> BaseRun.inc `LoopAnim Cower`; ARG_Forad.scr in
  Thronheim City (Argument scene): Sit (loop), Agree, Applause, Sc2_Forad6, Sc2_forad26 (his own ABC).
- RUDE rows carry no animation names. Wander markers that name animations (fidget1/2/5, Taunt, hAttack2) belong to guards,
  Hatlati (a commoner) and monsters, not these NPCs.
- Not counted: MM9's engine may play clips by itself (wince2, die2, cowerstart/cowerend around Cower); no script names them.

## Route (per project; each `extra_clips.sh` reproduces the installed GLB byte for byte, checked)
- All five `clips_mm9.py` copies gained opt-in `soft_offsets` (the soft line) and per-role `hold` (Dead2); with the accepted
  roles each rebuilds the accepted clips byte for byte (md5 checked on all five). Binder templates of imp/lich/skelwar updated.
- imp: clips_mm9 (grip.json) -> trident_clear (Aware, Hit2, Death2, Dead2) and new `trident_clear_wide.py` (Fidget2) -> graft into
  `work/split4.glb` -> floor (`floor_ops_extra*.txt`, Death2 smoothing 0.05 instead of 0.07: 1-frame take-off dip -2.5 -> -1.5 cm)
  -> mirror_glb -> graft onto the installed export.
- skelwar: clips_mm9 on the body and on the before-skirt body -> finger_keys (RAttack1OLD as AttackRanged, release 0.6 s, renamed by
  new `rename_clip.py`) -> new `skirt_keys_extra.py` -> graft into skins -> floor -> new `skirt_floor_extra.py` -> ground-death again
  (the before-skirt root left the corpse 2.9 cm up) -> graft.
- lich: clips_mm9 -> graft into `mm9_lich_glow.glb` -> new `cloth_flat_extra.py` -> floor -> mirror -> graft.
- annud: clips_mm9 -> arm_clear x2 (Cower, Conv3, PlayDeath) -> hand_rest (Conv1, Bow) -> floor -> graft.
- forad: clips_mm9 (own source added) -> hand_rest (ArgumentSpeak6 R) -> floor -> graft.
Byte check (`graft_byte_check.py`) OK on all five. `check_winding` 0 inverted on all five. Installed with
`tools/install_model.py --world mm9`; script_clips bound under the flock on every descriptor (imp 3, skelwar 2, lich A/B via the
shared anchor, annud 1, forad 1).

## Measured, new clips (installed GLB; outputs in each project's `review/clips_restore_D/` or `v2/review/clips_restore_D/`)
| Body | Floor living / dying / corpse (cm) | Hands > 1 cm (worst, frames) | Jitter vs MM9 raw | Bones | Other |
|---|---|---|---|---|---|
| imp | -0.8..+2.7 / Death2 -1.5 one frame / 0 | none | arm 0 excess; Death2 shoulder skin 2.4/2.9 FAIL (limit 2.0; accepted Death 1.4) | 0 stretching | trident worst 0.5 cm (was 3.0 on Fidget2) |
| skelwar | -0.9..+0.8 (BackpedalRun airborne to 18.9, as Running) / 0 / 0 | Death2 L 6.0 25 f, R 6.0 10 f (both hands on the hilt, kneeling); AttackMeleeOld L 4 f, R 2 f; Search R 5 f (fist on the scimitar) | arm 0 excess; shoulder skin Death2 17-18, BackpedalRun 11, AttackMeleeOld 2.6 FAIL (accepted Death 20-25, Running 39-45) | L Thigh 1.17 in AttackMeleeOld (accepted hip slide, R Thigh 0.10-0.15 m) | skirt: BackpedalRun 4/33 f 3.9 cm, AttackMeleeOld 14/37 4.1, Death2 11/101 0.9, others 0 |
| lich | Backpedal -1.9..+1.3, BackpedalRun -1.9..+3.0 / Death2 -2.4 / 0 (rides 14 cm on its sleeves, as the accepted Dead's 12) | Backpedal L 2.0 3 f, BackpedalRun L 1.7 1 f (accepted Walking 0.8/1.0) | arm 0 excess; Death2 shoulder skin 5.5 FAIL (accepted Death 3.4-3.6 FAIL) | within 6 % | |
| annud | 0 / PlayDeath -2.7 one frame / 0; PlayGetUp -2.7..+4.0 | Conv1 L 3.0 33 f (hand at the chin), R 2.1 72 f; Bow R 3.6 13 f; PlayGetUp L 4.5 8 f (hand on the head) | Conv1 upper arm 1.25/1.06 deg/f FAIL (limit 1.0; arm_clear gave 14.6), Bow shoulder skin 2.3 FAIL | within 7.5 % | forearms in sleeves up to 6 cm (cloth on cloth, as accepted) |
| forad | 0 | Applause 2.2 (the clapping hands meet); Sc2_Forad6 R cleared 7.6 -> 0 | 0 fails | 0 | seated clips grounded on the feet (MM9 raw floats 27 cm); R foot 7 cm above L |
Strips read: imp `strip_new_0/1.png`, skelwar `strip_new_0/1.png` + `clay_death2.png`, lich `strip_new_0.png`, annud
`clay_new.png`, forad `strip_new_0.png` (raw) + `clay_new.png` + MM9 source sit compared.

## Regression
`mm9_actor_models_build_every_binding` (`--world mm9`, `OPENYAMM_REGRESSION_FILTER`, actors suite): **PASS, 147 descriptors on
58 models, 0 failed** after all five installs and bindings; rerun after annud's last (clip-only) reinstall: **PASS, 149
descriptors on 59 models, 0 failed** (another agent's model joined meanwhile). `review_root.py` run.

## Not checked
No viewer (textured) shots, no normal-speed playback, no in-game run of any new clip; nothing drives these script clips yet.
Collapse gate, detached-parts audit and LOD1-3 not run on the new clips. Imp viewer GLB `export/mm9_imp_full.glb` not updated
(`work/full_extra.glb` holds the clips, used for the trident gate). Forad's seat height against the Thronheim scene not checked.
The lich hand_rest was not applied to the backpedal walks (2.0 cm, below the accepted lines' targets).
