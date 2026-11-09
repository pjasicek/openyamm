# Variant PeasantDM3 (dwarf man) — status

- Project `level_generation/creatures/mm9_peasantdm3_claude/`, lease `mm9:peasantdm3` (owner peasantdm3-agent).
- Rows naming PeasantDM3.abc: 11 Town (PeasantDM3b), 12 Shopkeeper (PeasantDM3a).

## Log
- 14:26 UTC lease claimed (backup 2930). Reading briefs; comparison next. Credits 0.
- 15:20 UTC comparison re-run: DM3 vs DM1 same 41-joint skeleton (only `Bip01 Ponytail1` rest differs, 14 deg: MM9's long
  hair tip), head p90 1.9 / torso 2.4 / arms 1.0 / legs 1.6 cm. Renders (`review/sheet_mm9_dm3_vs_dm1_dm2.png`,
  `review/sheet_mm9_heads_dm3_dm1.png`): DM1's cut (short-sleeved tunic, bare forearms, undersleeves, wrist bands, belt,
  folded boots); DM3 changes the HAIR (long, to the shoulders), the BEARD (longer, pointed) and the costume paint (A purple
  with gold ring-chain yoke; B charcoal tweed open over a cream shirt, ochre braid trims), no medallion. Variant route
  chosen. DAT: row 11 = TownDwarfMaleB (1 placed, no script), row 12 = ShopkeeperDwarfMaleA (1 placed, no script):
  core roles + Fidget2 + Cower (NPCbase), no miner clips.
- 15:30 UTC geometry `scripts/reshape_dm3.py` on a copy of DM1's `eyes_trim.blend` (DM1 untouched): medallion, eye cups and
  shin sliver deleted, beard wedge (-4.2 cm, -2.2 cm forward), bob stretched to the shoulders with push-out from the body,
  lower hair weights Head->Neck->Spine2. Body upload (DM1's UV layout, no medallion) exported; head UVs re-laid
  (texpass_head_uv.py on the reshaped head). Codex body masters (DM1 templates repainted to skin B) and head turnaround
  (painted onto clay silhouettes of the reshaped head) running. Credits 0.
- 15:50-16:00 UTC Codex masters accepted: body (DM1's five approved masters repainted to skin B; alpha haze cleaned) and head
  turnaround painted onto clay silhouettes of the reshaped head (IoU 0.98-0.998; the profile needed one extra targeted run:
  beard 4 cm too long). Meshy: body 4K retexture on DM1's UV layout (10, backup 2925 before), head 4K retexture on new head
  UVs (10, backup 2875 before). Credits **20 / 25**. No job pending.
- 16:00-16:30 UTC head/hair fixes (positions and paint only): ears flattened under the hair (ear_flatten.py), hair curtain
  moved in to the cheek/jaw (curtain_close.py: background showed between face and hair from the front), ear and neck skin
  under the hair shaded to hair shadow (ear_shade.py, neck_body_fix.py). Tiers (tiers_pdm3.py): body R tunic, G trim, B shirt
  panel, A trousers; head R hair/beard; B = shared paint, A = MM9 A colours. Linings (DM2's chain: neck cap, collar, boots,
  wrists). Build ok, winding 0. See-through gate running.
- 16:30-19:00 UTC see-through: sleeves (DM1's cuff_trim ring and folded linen cuffs), boots, belt, collar lined (DM2's
  chain + cuff_lining.py), hair inner twin; rigid beard weights; hands cleaned; boots/belt matched toward MM9's dark leather;
  tier A hair = chroma shift (the quantile ramp gave net-like light strands); curtain field smoothed (a deep crease at the side).
  Viewer face pre-screen both tiers clean (review/shots/sheet_f4_*.png). Gates: jitter 0; arm/hand exact 0 frames > 1 cm
  (sparse Talk L 1.4 cm 3 f as DM1); see-through sleeves 268/186 -> ~42/1, boots 24 -> 0, collar 93 -> 63 (one Death pose),
  torso 82 -> 81 (corpse at floor level); winding 0; detached 0; floor ok x2; viewer 22 switches 0 errors; LOD0 10,656.
- 19:00 UTC installed assets_source/worlds/mm9/models/mm9_peasantdm3.glb (sha256 561040214e77...), bound MM9 11 Town (pdm3_b),
  MM9 12 Shopkeeper (pdm3_a) under the flock, rows 11 -> 326 / 12 -> 328 in mm9_npc_actor_rows.tsv, tables regenerated
  (descriptors 9011 / 9012). Regression running. Credits **20 / 25**. DM1/DM2 sha256 unchanged.
- 19:30 UTC regression actors --world mm9: passed 192, failed 1 (known out05); mm9_actor_models_build_every_binding PASS.
  Floor audit MM9 11 / 12 ok. Final see-through r4: sleeve R 42, L 1, boots 0, trousers 1, collar 63 (Death), torso 81 (corpse,
  floor level). Map placement left to the orchestrator (README "Binding plan").
- Phase: **done**. Credits **20 / 25** (backup 2925 -> 2875 before my two jobs; shared balance moves with other agents). README is
  the record. Lease released.
