# Xeen: XD-04's caged children, four skins (2026-11-25, agent xeen-fb4-dungeon6)

D-163 put XD-04's four caged children on Xeen copies of MM9's elf-eared boy and girl (`mm9_peasantboy_claude`,
`mm9_peasantgirl_claude`; D-44: Xeen binds its own copies). The user then allowed new skins ("you can generate new
skins for them if it makes sense, i don't mind"): the goblin-eared boy (npc 4053) should match his portrait
`assets_dev/worlds/xeen/icons_x2/npc14053.png` (ginger hair, freckles, green-tinged pointed ears), and each child should
look different, in village clothes.

Ramps only (CLAUDE_CREATURE_TEXTURES.md): no new paint, no Meshy, no Codex. Every skin is a `KHR_materials_variants`
variant added beside the MM9 ones; the shared images stay, the new data is three masks and the ramps.

| Skin | Child | Head | Body (ramps on the existing region mask) |
|---|---|---|---|
| `xboy_ginger` | 1, row 11930, npc 4053 | boy e's freckled head; hair (and brows) ramped to bright copper-ginger by a new head mask (`textures/xboy_ginger_head_mask.png`) | grey-brown homespun vest, undyed linen sleeves, dark brown breeches, dark leather belt |
| `xboy_dark` | 3, row 11932 | boy b's dark-haired head (as painted) | moss-green vest, cream sleeves, russet breeches, brown belt |
| `xgirl_rose` | 2 (Rosebud), row 11931 | g1e's light brown hair (as painted) | madder-rose dress, linen trims; skin ramp g1e's |
| `xgirl_flax` | 4, row 11933 | g1e's hair ramped flaxen by a head mask (`textures/xgirl_flax_head_mask.png`) | woad-blue dress, brown trims; skin ramp g1e's |

The ears attachment (`xeen_peasantboy_elfears.glb`) has `xboy_ginger` and `xboy_dark` too: the ear skin ramped a faint
goblin green (`textures/xboy_ears_mask.png`, the whole ear, 75 % toward a yellow-green on its own shading).

## Route

1. `scripts/skins.py <work>`: reads the MM9 sources in `assets_source/worlds/mm9/models/`, classifies hair texels on the
   head sets (warm, saturated, not bright; feathered inward only, so the face keeps no orange rim), writes the masks,
   fits each region's ramp to a target (the base texel's brightness in the new hue and saturation, `fit_ramps`), and
   writes the specs `<work>/boy.json`, `ears.json`, `girl.json` and CPU previews (`<work>/img`).
2. `scripts/add_variants.py <mm9 glb> <out> <spec>`: appends the variants, copying a LOD0 material per variant and its
   `_LOD2`/`_LOD3` far copies, new mask images where set.
3. `lod_repair_claude/scripts/fix_variant_maps.py <out> <final> --levels 2,3` (its venv): far maps for the variants
   whose LOD0 maps differ (the ginger head and flaxen hair masks, boy b's head).
4. `export/` -> `python3 tools/install_model.py export/<name>.glb --world xeen --name <name>.glb` for `xeen_peasantboy`,
   `xeen_peasantboy_elfears`, `xeen_peasantgirl1e`.

Fit (8-bit mean / p95): body regions 1.9-3.7 / 4.9-10.6; ginger hair 1.16 / 3.57; ears 0.85 / 3.33; girl dresses and
trims 2.3-3.0 / 9.2-12.3; flaxen hair 1.65 / 5.37.

Bindings: `assets_dev/worlds/xeen/models/actors.yml` descriptors `Xeen Goblin-eared boy` (xboy_ginger), `... boy 2`
(xboy_dark), `... girl` (xgirl_rose), `... girl 2` (xgirl_flax); rows in `source/monsters.yml` `characters`.
Captures: `output/xeen_fb/p4_dungeon6/xd04_cap/` (`boy_talk_before_after.png`, `after2/`).
Not done: the portrait's sulky mouth (the face paint smiles; a texture change, not a ramp).
