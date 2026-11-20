# MM6 source-sheet row scale screening

Per-pose restored/native size ratios; compare medians by recorded raw-sheet row. Prefer the longest common named vertical landmark pair, excluding diagnostic points; otherwise use alpha>=128 silhouette height. Flag >=2% relative row difference with at least two distinct generated cells per row; pixel aliases count once. Width and sqrt(area) are supporting screens.

These are review candidates, not confirmed uniform-scale defects.

```json
{
  "families": 60,
  "frames": 3481,
  "frames_grouped": 3478,
  "frames_without_sheet_mapping": 3,
  "source_sheets": 1257,
  "multiple_row_sheets": 588,
  "multiple_row_families": 56,
  "multiple_row_with_landmarks": 382,
  "sheets_with_two_or_more_frames_in_compared_rows": 428,
  "landmark_sheets_with_two_or_more_frames_in_compared_rows": 275,
  "candidate_sheets": 131,
  "candidate_families": 47,
  "landmark_candidate_sheets": 84,
  "landmark_candidate_families": 32,
  "landmark_candidates_with_one_export_scale": 83,
  "nonoverlapping_landmark_candidate_sheets": 73
}
```

## Inspected examples

Inspected seven current native/restored static contacts at 150% native logical size, with fixed coordinates and saved landmark guides; also inspected the retained Dwarf fidget raw sheet. Native references already include integer placement; only the manifest anchor correction is added. No animation viewing or visual acceptance is claimed.

| Family / sheet | Finding | Contact |
| --- | --- | --- |
| BDwarf A / standing_redo_01 | Lower row is shorter: -3.21% in native-normalized helmet-to-sole span. Current pixels agree with saved markers. Different views share the rows, so view and row effects are confounded. | [image](mm6_dwa1_standing_redo_01.png) |
| BDwarf A / fidget_redo_01 | Clear row-boundary height difference: -4.08%. Upper-row feet track the native guide; all three lower-row feet stop above it when crowns are aligned. Retained raw sheet was also inspected. | [image](mm6_dwa1_fidget_redo_01.png) |
| BDwarf A / walk_0_redo_01 | Counterexample: -0.02% between rows, with closely matching height across all six frames. Two rows do not necessarily cause drift. | [image](mm6_dwa1_walk_0_redo_01.png) |
| PeasantM4 A / walk_4_redo_01 | Lower row is shorter: -4.50%. Planted soles align; upper-row crowns sit slightly above their native guides and lower-row crowns below. Current alpha-height measurement independently agrees. | [image](mm6_natm_walk_4_redo_01.png) |
| BThief A / walk_2_redo_01 | Opposite direction: lower row is taller by +3.58%. With aligned hood tops, lower-row feet extend beneath native guides. Width ratios trend narrower, so uniform scaling needs a separate trial. | [image](mm6_thf_walk_2_redo_01.png) |
| ElemFire A / walk_3_redo_01 | Lower flame row has shorter overall extent: -7.06%. Current silhouette measurement is -6.97%, supporting a real extent difference. Flame geometry changes prevent treating this as a proven whole-body uniform scale error. | [image](mm6_fie1_walk_3_redo_01.png) |
| PeasantM3 A / hit_redo_01 | Lower row is shorter: -3.64%. Original pose heights vary substantially; normalization preserves those differences. Lower-row restored soles stop above the native guides despite aligned head tops. | [image](mm6_mep_hit_redo_01.png) |

Row-associated size drift recurs across several creatures. Of 275 multirow sheets with at least two distinct cells per compared row and a common usable saved landmark span, 84 cross the 2% screen (32 families): 68 shrink in later rows and 16 grow. These are candidates, not 84 confirmed uniform-scale defects. 83 of the 84 use one export scale across their sheet, supporting variation in generated geometry rather than a different export resize. The reviewed humanoid examples show actual head-to-sole differences. A global bottom-row multiplier is inappropriate: some sheets match, some grow, and width/proportions can change independently. Prioritize reversible frame-specific trials for Dwarf fidget/standing and PeasantM4 rear walk, checking a second feature and width before deciding on regeneration.

## All screening candidates

| Family | Sheet | Rows | Basis | Row difference |
| --- | --- | ---: | --- | ---: |
| BRobot A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -16.03% |
| Cobra A | attack_redo_01 | 2 | head_top_candidate / lower_jaw | 1→2: -11.11% |
| BGenie A | death_corpse_redo_01 | 2 | extent_max / extent_min | 1→2: -11.11% |
| BRat A | standing | 2 | silhouette only | 1→2: +10.67% |
| BOoze A | death_corpse_redo_01 | 2 | crest / right | 1→2: -8.75% |
| ElemWater A | death_corpse_redo_01 | 2 | head_anchor / waist_calibration | 1→2: +7.62% |
| ElemFire A | walk_3_redo_01 | 2 | tail / tip | 1→2: -7.06% |
| SeaSerpent A | walk_3_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -6.79% |
| Bloodsucker A | unused_native_0_redo_01 | 3 | silhouette only | 1→2: -1.87%, 1→3: +6.58% |
| ElemAir A | hit_redo_01 | 2 | silhouette only | 1→2: -6.20% |
| ElemFire A | walk_1_redo_01 | 2 | tail / tip | 1→2: -5.96% |
| BBat A | unused_native_2_redo_01 | 2 | silhouette only | 1→2: -5.89% |
| DragonLand A | hit_redo_01 | 2 | foot_or_remnant_anchor / head_or_remnant_feature | 1→2: -5.87% |
| Cactus A | attack_0_redo_01 | 2 | lower_spine_envelope / upper_spine_envelope | 1→2: -5.83% |
| BGoblin A | accepted_front_death_corpse_redo_01 | 2 | silhouette only | 1→2: +5.46% |
| ElemFire A | walk_2_redo_01 | 2 | tail / tip | 1→2: -5.36% |
| ElemFire A | hit_redo_01 | 2 | tail / tip | 1→2: -5.22% |
| Bloodsucker A | unused_native_1_redo_01 | 4 | silhouette only | 1→2: -2.46%, 1→3: -5.02%, 1→4: -1.52% |
| SeaSerpent A | walk_1_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -5.00% |
| BGhost A | standing_redo_01 | 2 | silhouette only | 1→2: -4.93% |
| BSpider A | walk_1 | 2 | silhouette only | 1→2: +4.92% |
| BGoblin A | accepted_front_hit_redo_01 | 2 | silhouette only | 1→2: -4.81% |
| BBat A | standing_redo_01 | 2 | silhouette only | 1→2: -4.79% |
| FighterLeath A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -4.77% |
| SeaSerpent A | walk_4_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -4.74% |
| BHydra A | standing_redo_01 | 2 | floor_contact / top_silhouette | 1→2: +4.50% |
| PeasantM4 A | walk_4_redo_01 | 2 | crown / sole | 1→2: -4.50% |
| BLich A | hit_redo_01 | 2 | silhouette only | 1→2: -4.44% |
| PeasantF2 A | death_corpse_redo_01 | 2 | crown / sole | 1→2: +4.38% |
| Jackalman A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +4.36% |
| LizardArch A | death_corpse_redo_01 | 2 | floor_contact / top_silhouette | 1→2: +4.26% |
| DragonLand A | unused_native_redo_01 | 2 | foot_or_remnant_anchor / independent_body_feature | 1→2: -4.19% |
| BGhost A | walk_3_redo_01 | 2 | hood / visible_hand_exit | 1→2: +4.14% |
| Cobra A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -4.11% |
| BDwarf A | fidget_redo_01 | 2 | crown / sole | 1→2: -4.08% |
| BLich A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +4.03% |
| LizardArch A | walk_1_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -3.95% |
| BMedusa A | death_corpse_redo_01 | 2 | grounded_coil / independent_wrist_or_neck | 1→2: -3.93% |
| BOoze A | attack_redo_01 | 2 | silhouette only | 1→2: -3.86% |
| BSpider A | walk_2 | 2 | silhouette only | 1→2: +3.78% |
| PeasantF1 A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +3.71% |
| Cactus A | death_corpse_redo_02 | 2 | silhouette only | 1→2: +3.71% |
| ElemWater A | fidget_redo_01 | 2 | hand_check / head_anchor | 1→2: -3.69% |
| LizardArch A | walk_4_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -3.67% |
| PeasantM3 A | hit_redo_01 | 2 | crown / sole | 1→2: -3.64% |
| Nobleman A | walk_2_redo_01 | 2 | crown / sole | 1→2: -3.60% |
| BThief A | walk_2_redo_01 | 2 | crown / sole | 1→2: +3.58% |
| ElemWater A | unused_native_0_redo_02 | 2 | hand_check / head_anchor | 1→2: -3.53% |
| ElemEarth A | death_corpse_redo_01 | 2 | base / upper_extent | 1→2: -3.48% |
| BOoze A | walk_3_redo_01 | 3 | silhouette only | 1→2: +3.47%, 1→3: +2.05% |
| BRobot A | hit_redo_01 | 2 | silhouette only | 1→2: +3.47% |
| BMonk A | death_corpse | 2 | silhouette only | 1→2: -3.45% |
| Werewolf A | death_corpse | 2 | silhouette only | 1→2: +3.39% |
| PeasantM3 A | attack_redo_01 | 2 | crown / sole | 1→2: -3.39% |
| BGhost A | hit_redo_01 | 2 | silhouette only | 1→2: -3.38% |
| PeasantM3 A | walk_3_redo_01 | 2 | crown / sole | 1→2: -3.33% |
| BGenie A | fidget_redo_01 | 2 | crown / vortex_tip | 1→2: -3.29% |
| BHydra A | death_corpse_redo_01 | 2 | floor_contact / top_silhouette | 1→2: +3.27% |
| PeasantM2 A | attack_redo_01 | 2 | crown / sole | 1→2: -3.24% |
| BDwarf A | standing_redo_01 | 2 | helmet_spike / sole | 1→2: -3.21% |
| Barbarian A | hit_redo_01 | 2 | silhouette only | 1→2: -3.20% |
| BSpider A | walk_3 | 2 | silhouette only | 1→2: +3.16% |
| Cleric A | walk_0_redo_01 | 2 | head / sole_height | 1→2: -3.08% |
| Druidess A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -3.04% |
| Sorcerer A | walk_4_redo_01 | 2 | crown / sole | 1→2: +2.99% |
| KnightPlate A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -2.97% |
| Ogre A | fidget_redo_01 | 2 | silhouette only | 1→2: -2.93% |
| Bloodsucker A | walk_4_redo_01 | 2 | silhouette only | 1→2: +2.92% |
| PeasantM3 A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +2.92% |
| KnightPlate A | walk_2_redo_01 | 2 | crown / sole | 1→2: -2.88% |
| LizardArch A | attack_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.85% |
| Guard A | hit_redo_01 | 2 | crown / sole | 1→2: -2.85% |
| LizardArch A | fidget_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.84% |
| PeasantF2 A | walk_0_redo_01 | 2 | crown / sole | 1→2: -2.80% |
| BMedusa A | walk_1_redo_01 | 2 | coil_baseline / neck_ring | 1→2: -2.80% |
| PeasantM2 A | hit_redo_01 | 2 | crown / sole | 1→2: +2.80% |
| FighterLeath A | walk_3_redo_01 | 2 | crown / sole | 1→2: -2.79% |
| SeaSerpent A | walk_0_redo_01 | 2 | floor_contact / top_silhouette | 1→2: +2.78% |
| BDwarf A | walk_2_redo_01 | 2 | helmet_spike / sole | 1→2: -2.76% |
| PeasantM3 A | walk_2_redo_01 | 2 | crown / sole | 1→2: +2.76% |
| BGenie A | walk_0_redo_01 | 2 | crown / vortex_tip | 1→2: -2.74% |
| Ogre A | hit_redo_01 | 2 | silhouette only | 1→2: -2.72% |
| BMinotaur A | standing_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.70% |
| Bloodsucker A | fidget_redo_01 | 2 | silhouette only | 1→2: +2.66% |
| Cactus A | adequate_redo_01 | 2 | lower_spine_envelope / upper_spine_envelope | 1→2: +2.65% |
| ElemWater A | unused_native_1_redo_01 | 2 | hand_check / head_anchor | 1→2: +2.63% |
| ElemEarth A | walk_4_redo_01 | 2 | crown / feet | 1→2: -2.63% |
| BGenie A | walk_1_redo_01 | 2 | crown / vortex_tip | 1→2: -2.60% |
| BArcher A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +2.57% |
| BGenie A | walk_2_redo_01 | 2 | crown / vortex_tip | 1→2: -2.56% |
| PeasantF2 A | hit_redo_01 | 2 | crown / sole | 1→2: -2.51% |
| ElemEarth A | attack_redo_01 | 2 | crown / feet | 1→2: -2.50% |
| PeasantF2 A | standing_redo_01 | 2 | crown / sole | 1→2: -2.50% |
| ElemEarth A | walk_0_redo_01 | 2 | crown / feet | 1→2: -2.50% |
| BHydra A | hit_redo_01 | 2 | floor_contact / top_silhouette | 1→2: +2.48% |
| BDwarf A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -2.46% |
| Barbarian A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +2.46% |
| BGoblin A | standing_sides_redo_01 | 2 | silhouette only | 1→2: -2.44% |
| PeasantM2 A | walk_1_redo_01 | 2 | crown / sole | 1→2: -2.42% |
| ElemFire A | walk_0_redo_01 | 2 | tail / tip | 1→2: -2.38% |
| BMinotaur A | walk_2_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.33% |
| BHydra A | unused_native_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.33% |
| FighterChain A | walk_3_redo_01 | 2 | crown / sole | 1→2: +2.33% |
| BGhost A | attack_redo_01 | 2 | silhouette only | 1→2: -2.31% |
| BGenie A | attack_redo_01 | 2 | crown / vortex_tip | 1→2: -2.31% |
| Ogre A | walk_2_redo_01 | 2 | silhouette only | 1→2: +2.30% |
| BRat A | walk_4 | 2 | silhouette only | 1→2: +2.30% |
| BThief A | hit_redo_01 | 2 | crown / sole | 1→2: -2.29% |
| FighterChain A | standing_redo_01 | 2 | crown / sole | 1→2: -2.27% |
| DragonCave A | walk_4_redo_01 | 2 | head_back / planted_sole | 1→2: -2.26% |
| Bloodsucker A | death_corpse_redo_01 | 2 | silhouette only | 1→2: +2.25% |
| BDwarf A | walk_1_redo_01 | 2 | helmet_spike / sole | 1→2: -2.20% |
| BRobot A | standing_redo_01 | 2 | silhouette only | 1→2: -2.20% |
| BRobot A | fidget_redo_01 | 2 | silhouette only | 1→2: -2.19% |
| PeasantF4 A | walk_1_redo_01 | 2 | crown / sole | 1→2: -2.18% |
| PeasantM3 A | walk_0_redo_01 | 2 | crown / sole | 1→2: +2.16% |
| BBat A | hit_redo_01 | 2 | silhouette only | 1→2: -2.16% |
| BMinotaur A | walk_1_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.13% |
| BHarpy A | walk_2_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.13% |
| BHydra A | walk_0_redo_01 | 2 | floor_contact / top_silhouette | 1→2: -2.13% |
| Cobra A | fidget_redo_01 | 2 | head_top_candidate / lower_jaw | 1→2: -2.11% |
| ElemWater A | walk_0_redo_01 | 2 | hand_check / head_anchor | 1→2: -2.08% |
| Jackalman A | hit_redo_01 | 2 | silhouette only | 1→2: -2.07% |
| ElemFire A | death_corpse_redo_01 | 2 | silhouette only | 1→2: -2.06% |
| FighterChain A | attack_redo_01 | 2 | crown / sole | 1→2: -2.05% |
| PeasantM1 A | walk_1_redo_01 | 2 | crown / sole | 1→2: -2.04% |
| BThief A | walk_0_redo_01 | 2 | crown / sole | 1→2: -2.02% |
| BDwarf A | walk_3_redo_01 | 2 | helmet_spike / sole | 1→2: -2.02% |
| PeasantF2 A | walk_3_redo_01 | 2 | crown / sole | 1→2: -2.02% |
| Jackalman A | standing_redo_01 | 2 | crown / sole | 1→2: -2.01% |
| Sorcerer A | walk_0_redo_01 | 2 | crown / sole | 1→2: -2.00% |

## Limits

- Candidates require visual review; weapons, effects and changed anatomy can fool bounds.
- Saved landmarks are prior annotations, not fresh measurements of every current pixel.
- Rows can correlate with views or phases; this does not establish row layout as the cause.
- Measurements describe current selected masters; historical superseded sheets are excluded.
- No automatic fix, artwork change, acceptance change or saved viewer offset is applied.
