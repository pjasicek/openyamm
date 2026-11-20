# MM9 Monster Legacy Sprite Mapping

The selected MM9 monster replacements use existing MM6/MM7/MM8 sprites exclusively. Converted MM9 3D model renders
are reference material only and are not intended for the runtime sprite set.

The authoritative replacement selection is:

- `tools/mm9_import_discovery/mm9_monster_legacy_replacements.tsv`

It has one entry for every MM9 `MONSTERS.txt` row whose `IsMonster` value is exactly `1`. Each entry selects a merged
OpenYAMM actor id and records whether the visual match is high or medium confidence. A/B/C families are kept together
where a three-rank legacy family exists. This table selects presentation only.

MM9 owns runtime monster ids `9000-9999`, with imported source row `N` assigned runtime id `9000 + N`. The world
contributes independent gameplay and descriptor tables:

- `assets_dev/worlds/mm9/data_tables/monster_data.txt`
- `assets_dev/worlds/mm9/data_tables/monster_descriptors.txt`

The descriptor rows reuse the selected legacy `mXXX` sprite and sound columns. The gameplay rows are independent MM9
records, so their names, strength, attacks, AI, resistances, and treasure can be tuned without changing or inheriting
the selected MM6-MM8 monster at runtime. Gameplay values are generated from MM9 `MONSTERS.txt`; the replacement id is
used only for the descriptor, blood presentation, sprites, and sounds.

The generated translation audit is:

- `assets_dev/worlds/mm9/data_tables/monster_conversion_audit.tsv`

Generation rejects an unclassified source monster, projectile, damage family, condition, spell, movement value, or
treasure category instead of silently inheriting legacy behavior.

## Gameplay translation

Direct source values are retained for level, HP, AC, experience, damage dice, alternate-attack chance, flight, and the
five MM9 resistance families. Fields whose runtime units or domains differ are translated as follows:

- MM9 elemental resistance is assigned to OpenYAMM Fire, Air, Water, and Earth resistance.
- MM9 spirit resistance is assigned to Mind, Spirit, and Body resistance. Light, Dark, and Physical map directly.
- Source resistance `1000` is emitted as `Imm`; lower numeric resistance values remain numeric.
- MM9 movement velocity is multiplied by the DAT-to-ODM coordinate scale `2.56`. Flying actors use authored fly
  velocity; actors with no walk, run, or fly velocity are stationary.
- MM9 actor recovery is `source * 0.1` seconds. It is converted to OpenYAMM monster recovery ticks while accounting for
  OpenYAMM's real-time recovery scale; source `30` therefore becomes `180` ticks, or three seconds.
- Numeric MM9 movement tiers become progressively larger OpenYAMM wander ranges. Script families select Normal,
  Aggressive, or Suicidal classic AI without adding an MM9 SCR runtime to combat.
- MM9 treasure level and category are retained. Because the source has no per-monster drop chance, non-empty treasure
  uses a conservative world-specific 25% chance.

MM9 projectile names map to existing elemental monster projectiles and FX recipes. Thrown knife, axe, skull, and egg
attacks use namespaced projectile tokens backed by the existing MM6-MM8 object sprites; they do not alter any legacy
monster row. The Dragon King's authored third fire-breath projectile replaces its otherwise redundant second attack,
because OpenYAMM supports two direct attacks rather than three.

MM9 spell descriptors retain their authored mastery and skill number. Exact supported spells remain exact. The main
adaptations are Elemental Bolt to Fire Bolt/Lightning Bolt/Ice Bolt/Rock Blast according to the actor's projectile
family, Chain Lightning to Lightning Bolt, Natural Armor to Stone Skin, Wound to Harm, SpellReaver to Dispel Magic,
and unsupported MM9 condition/area spells to the closest supported projectile spell. A zero-chance spell 2 with a
descriptor is the complement of spell 1, matching the MM9 table convention. A `concat` spell is converted into an
on-hit poison, disease, fear, curse, or paralyze condition instead of a separate cast.

OpenYAMM supports only one special condition per monster row. Combined MM9 conditions retain the stronger primary
condition. MM9 Steal uses item damage as the closest supported inventory consequence, and temporary Stun uses the
lowest paralyze tier. Source self-resurrection has no equivalent in the classic actor table and is retained in the
audit for a future explicit runtime mechanic; it is not misrepresented as summoning.

## Source inventory

The authoritative model/skin inventory and searchable reference gallery are:

- `test_img/mm9_monster_pose_catalog/inventory.tsv`
- `test_img/mm9_monster_pose_catalog/inventory.yml`
- `test_img/mm9_monster_pose_catalog/index.html`

The inventory contains 134 MM9 monster rows, 119 distinct model/skin variants, and 50 distinct models. Model and skin
names come directly from `mm9/extracted/DATA/DATA/MONSTERS.txt`; the incomplete `ACTOR.txt` table is not used for
monster visuals. This prevents the placeholder sheep models seen in the earlier NPC discovery pass.

Two source-format details are handled explicitly:

- `NettleSpore.spr` is an animated skin container. Its first real DTX frame is used for the static reference pose, while
  the authoritative inventory retains the original SPR name.
- Bird C names a missing `drow.dtx`. The reference renderer records the defect and uses the crow model's real default
  `crow.dtx`; it does not substitute a placeholder model.

The generator fails if a model, skin, SPR frame, or model-default resolution cannot be found, or if any model fails to
render cleanly.

## Replacement review

The generated side-by-side catalogue is:

- `test_img/mm9_monster_legacy_comparison/index.html`

It shows the actual MM9 model/skin pose beside the selected MM6-MM8 sprite and can be filtered by source number,
monster name, family, legacy id, or confidence. The current selection has 75 high-confidence and 59 medium-confidence
mappings. Medium confidence is used for MM9-only forms such as Lobbers, Nagates, Jellyspores, Dagrells, Magreebs, and
Tunnel Terrors; these still have deliberate visual/role matches rather than placeholders.

Important selection notes:

- Lobbers use the Treant family, the only hostile plant left after the MM6 Cactus rows were retired from the engine
  tables (they were the small-plant match before). They are weak hostile plants, not high-tier Nightmares.
- Thralls use the all-male primitive Cyclops family; the former Magyar family was female.
- Militiamen use the male MM6 leather Bandit family, while the Beldonian Horde uses male MM6 ringmail fighters with
  swords and shields.
- Dagrells and Magreebs use the upright Wasp family as the nearest insectoid body plan.
- Evil Sorcerers use the more modern MM7 Mage family.
- Bigfoots use the upright furry MM6 Werewolf family instead of Behemoths.
- Jellyspores are underwater monsters. Their fallback remains documented, but they should stay unused until OpenYAMM
  implements underwater gameplay.

The legacy preview generator resolves both lowercase `palNNN.act` and original mixed-case `PalNNN.act` files. This is
required for correct MM8 rank colors; missing the mixed-case palettes previously produced misleading magenta previews
for families such as Trolls and Lizardmen.

## Family tier pictures

Map-stats encounter slots and spawn points resolve a slot picture `<base>` to monsters by the pictures `<base> A`,
`<base> B` and `<base> C`, as in MM6-MM8. The reviewed family table
`tools/mm9_import_discovery/mm9_monster_families.yml` groups MM9 rows into such families: an id, a display name and the
A/B/C tiers as MM9 source numbers. A family is normally one MONSTERS.txt body ordered by level (Dragonfly Mite,
Dragonfly, Fire Dragonfly become `MM9 Dragonfly A/B/C`, runtime ids 9075-9077); two-row bodies are A/B families. The
file comments every exception: the five-row skeleton body (spawns use Skeletoid, Bone Thrasher, Skeleton L16), the
pods and lobbers split by element, the male and female Honk bodies, and the Lesser and Greater Demon pair.

The generator writes `MM9 <family> A|B|C` into the monster_data picture column and the monster_descriptors
InternalName of family rows; bosses and the remaining rows (Dragon King, Lich King, Njam, Yanmir, Ebora, Skull Thrower,
Skeleton L40, MagreebBaby, Concubine) keep the unique `MM9 <n> <name>`. Model bindings in
`assets_dev/worlds/mm9/models/actors.yml` key on these descriptor names, and imported maps place monsters by id.

`tools/mm9_import_discovery/generate_mm9_map_stats_encounters.py` names the families in the MM9 rows of the engine
`map_stats.txt` (world id `mm9`): each MAPSTATS.txt encounter monster becomes its family picture base, for example
Isle of Ashes `Skeletoid`/`DragonFlyMite` become `MM9 Skeleton`/`MM9 Dragonfly`. Names match a MONSTERS.txt row
(case, spaces and punctuation ignored, a repeated name meaning its first row) or a family name; source misspellings are
listed as `mapstats_aliases`. It changes only the encounter picture and name columns, including MM9's fourth slot in
the trailing columns, and keeps chances, difficulty and appear ranges. It fails if a MAPSTATS monster has no family.

## Regeneration

The source gallery requires converted MM9 GLB/model sidecars and DTX preview PNGs:

```bash
python3 tools/mm9_import_discovery/generate_mm9_monster_pose_catalog.py \
  --model-root /path/to/OpenMM9/artifacts/model_exports/models \
  --skin-preview-root /path/to/combined/mm9/skin/previews
```

Generate the merged legacy candidates and then the comparison page with:

```bash
python3 tools/mm9_import_discovery/generate_legacy_actor_candidate_catalog.py
python3 tools/mm9_import_discovery/generate_mm9_monster_legacy_comparison_catalog.py
```

After changing the authoritative replacement selection or source mechanics, regenerate the MM9-owned runtime tables
with:

```bash
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py
```

Normal `regenerate_mm9_maps.sh` runs the table generator before transcoding and mirrors the tables to the editor world
unless `--no-editor-copy` is used; it then runs `generate_mm9_map_stats_encounters.py` on the engine `map_stats.txt`
next to the world root. Both tools replace their output files rather than rewriting them in place, so hard-linked
staging copies keep their own version.

The comparison generator rejects missing or extra source numbers, duplicate mappings, unknown merged actor ids, and
missing preview images.
