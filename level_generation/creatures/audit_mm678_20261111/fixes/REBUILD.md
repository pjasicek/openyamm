# Stream: rebuilds

One agent (`rebuild`). Read [COMMON.md](COMMON.md) first, then the project rules for any MM6–MM8 3D creature:
- step 0, five Codex HD masters from the native bitmaps ([CLAUDE_HD_MASTER_REFERENCES.md](../../CLAUDE_HD_MASTER_REFERENCES.md));
- [CLAUDE_HUMANOID_NPC_PLAYBOOK.md](../../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) in full, including the arm and hand gate;
- [CLAUDE_CREATURE_TEXTURES.md](../../CLAUDE_CREATURE_TEXTURES.md) for tiers and the head set;
- the [texture quality pass](../../claude_shared/TEXTURE_QUALITY_PASS.md) as the default from the start: `uv_atlas.py`
  UVs, a 4K paint downsampled once, gentle grade;
- the [modelling guidelines](../../../GAME_ASSET_MODELLING_GUIDELINES.md);
- the `creature-to-3d` skill's scope and resume rules.
A complete rebuild includes LODs, the binding, regressions and an in-game indoor/outdoor look
(`./tools/run_game.sh --isolated`, engine screenshots).

## Route: MM9 donor skeletons and clips (the user approved donors on 2026-11-11)

MM9's own humanoids were built on the **Yrsa route**: the MM9 skeleton (names and rest rotations kept, joints
translated), MM9's clips (`clips_mm9.py`), grafted five-finger MPFB hands with 15 finger bones per side
(`graft_hands.py`, `finger_alias`), a separate head set, fists solved round held shafts (`finger_keys.py`), and
`hand_rest.py` and `pole_clear.py`. The MM9 bodies, including MM9 Guard, show the result. Reference projects:
`mm9_yrsa_claude`, `mm9_guard_claude` (halberd, fist round the shaft, skirt hinges), `mm9_highwayman_claude`
(FIGHTERBASE child clips), `mm9_peasantf1_claude` … `f8`, `mm9_lizardorc_claude`.

For an MM6–MM8 rebuild, the mesh comes from **MM6–MM8 HD masters** (not MM9 renders), is fitted to the donor
skeleton with joints translated to the new body's proportions, and plays the donor's clips. Map them onto our clip
names and actor events.
- Re-time each clip to the native sprite's timing where the native has a distinct action.
- Measure strides, gait rate and floor, and set contact times from the MM9 clip events.
- Re-run `claude_shared/motion_audit.py`. The attack's motion ratio against MM9 should come out at about 1.0, and no
  region more than 12 % bad beyond Standing.
Legends of Might and Magic donors (`options_mm9_lomm.md` §3, `reference/legends_of_mm/Data/MODELS.REZ` through
`tools/mm9_import_discovery/extract_rez.py`) are allowed too. The **MM9 Dragon is excluded** (user: its clips do not
fit). If a donor does not suit a body, use the playbook's library route, and record why.

**Order:** pilot on the Guard (the closest donor match). Look at the result in the viewer and the game, then the
others. Install each model when its checks pass, keeping `work/before_rebuild/` for a one-command revert. Write a
short before/after sheet (viewer shots, identical cameras, every tier) per model into the ledger.

**Owners (from 2026-11-11 16:10):** two agents share this list.
- `rebuild` (the first agent) keeps the Guard pilot, then PeasantF1, Thief and Merchant.
- `rebuild-2` takes the Titan's hands, the lizardman peasant and the Werewolf.
Both write `LEDGER_rebuild.md`, and each reads the other's rows before starting a model.

## Models

| Order | Model | What must change | Suggested donor |
|---|---|---|---|
| 1 | `mm6_gua` Guard (halberd) | Meshy auto-rig with rigid fists (no finger bones); attack swings one arm on straight legs (ratio 0.34); rear elbow flares | MM9 GUARD (same weapon) |
| 2 | `mm6_ttn` Titan, **hands only** | Rigid open hands (Discord OY-27, "hands look messy in the attack"); Cast collapses the left shoulder and armpit at 1.6–2.05 s and the hand sinks into the belly. Keep the body, textures and other clips. Graft five-finger hands with finger chains (the Yrsa route's `graft_hands.py`), key fists and the cast hands, and fix the Cast shoulder. Optionally take its attacks from LoMM TITAN (HAttack, StepOn, Wipe) | LoMM TITAN for clips |
| 3 | `mm6_pfem` PeasantF1 (New Sorpigal woman) | See the user's history below | MM9 PEASANTFEMALE |
| 4 | `mm6_thf` Thief | Meshy auto-rig; mitten hands; cloak tears in Sprint; texture atlas 15.6 % | MM9 HIGHWAYMAN + FIGHTERBASE (dagger, throw) |
| 5 | `mm6_mer1` Merchant (club) | Codex install on QA hold (club grip gaps up to 75 mm, body penetration 64 mm); "hands noted as odd"; atlas 13.9 %; bland attack (0.42) | MM9 PEASANTMALE or NOBLEMAN body clips; club attack from FIGHTERBASE or TRELLBORG |
| 6 | `mm8_lizardman_peasant` | The last image-to-3D standard body; Meshy auto-rig; attacks are Walk played once; spiky hands; 49 % of its texture surface on specks | MM9 LIZARDORC (`mm9_lizardorc_claude`) or LoMM LIZARDWARRIOR; peasant behaviour as MM8's other peasants |
| 7 | `mm6_wwf` Werewolf | Meshy auto-rig, rigid open claws, "placeholder quality, awaiting user review", bodybuilder proportions bulkier than the sprite | LoMM ORC or TROLL; MM9 BIGFOOT or GEZZAMPT (digitigrade legs) |

### PeasantF1: what the user has already said (read before starting)

- 2026-10-30, on the installed v3: "the body is good, face is terrible", "hands are terrible, especially in
  standing". For her: "no attack needed".
- The v4 rebuild (`mm6_pfem_v4_claude/`) was rejected for **heavy hair** and **heavy far LODs**. Its review rounds
  also asked for:
  - no pale skin;
  - no graft lines at the neck;
  - no clay or smudged skin;
  - head in proportion;
  - arms not too thin;
  - a symmetric body;
  - a more subtle fidget.
  Read its README and `mm6_peasants_fix_claude/README.md`, where three arm-fix rounds ended in "revert the female to
  original one".
- So: keep the v3 body's look and proportions, and keep a light hairstyle and light far LODs. Give her a good face
  (head set) and good five-finger hands with a natural Standing hand pose, not clasped. Her attack slot may stay a
  restrained gesture (native peasants reuse the walk), but must not push hands into the skirt.

## Credits

The stream cap is 600 (COMMON.md), about 85 per model. The Titan's hands should need little or none. Record the
credits per model.
