# Headless To Doctest Migration Inventory

This document inventories `game/outdoor/HeadlessOutdoorDiagnostics.cpp` and classifies each current headless
`runCase` by whether it should remain in the headless regression suite or move to doctest.

Line numbers refer to the source file at the time this inventory was created and may drift.

## Classification

- `doctest-direct`: can move to `tests/` using current public APIs and lightweight fixtures. These are pure rules,
  table/data checks, party/item logic, or deterministic service checks.
- `doctest-with-adaptation`: should move to `tests/`, but first needs a small helper extraction or test seam. Typical
  examples are helpers currently local to `HeadlessOutdoorDiagnostics.cpp`, shared data fixtures, fake world runtimes,
  or focused event-runtime harnesses.
- `stay-headless`: should stay in headless regression for now because it validates real map/world/application
  integration: BLV/ODM loading, active world runtime, movement/collision against authored geometry, actual map event
  scripts, save/load, cross-map transitions, audio/application lifecycle, or end-to-end UI/application state.

## Summary

- Original headless cases inventoried: 275
- Moved to doctest after this inventory: 19
- Remaining classified headless cases: 256
- Remaining `doctest-direct`: 40
- `doctest-with-adaptation`: 80
- `stay-headless`: 136

Already moved:

- `spellbook_ui_layout_uses_canonical_school_slot_mapping` was moved from headless into
  `tests/SpellbookUiLayoutTests.cpp`.
- `default_party_seed_preserves_unique_portrait_picture_ids` was moved into `tests/PartyRegressionTests.cpp`.
- `monster_target_selection_prefers_matching_living_members` was moved into `tests/PartyRegressionTests.cpp`.
- `monster_target_selection_skips_invalid_members` was moved into `tests/PartyRegressionTests.cpp`.
- `default_seed_monster_target_selection_matches_female_preference` was moved into
  `tests/PartyRegressionTests.cpp`.
- `party_damage_sets_unconscious_within_endurance_threshold` was moved into `tests/PartyRegressionTests.cpp`.
- `party_damage_sets_dead_below_endurance_threshold` was moved into `tests/PartyRegressionTests.cpp`.
- `monster_data_parses_blood_splat_on_death_flag` was moved into `tests/MonsterTableRegressionTests.cpp`.
- `monster_attack_style_classification_examples` was moved into `tests/MonsterTableRegressionTests.cpp`.
- `inventory_move_accept_reject_and_swap` was moved into `tests/PartyRegressionTests.cpp`.
- `inventory_cross_member_move_and_full_rejection` was moved into `tests/PartyRegressionTests.cpp`.
- `inventory_member_auto_transfer_places_item_in_first_free_slot` was moved into
  `tests/PartyRegressionTests.cpp`.
- `gameplay_selection_blocks_impairing_conditions` was moved into `tests/PartyRegressionTests.cpp`.
- `party_shared_experience_uses_learning_and_skips_incapacitated_members` was moved into
  `tests/PartyRegressionTests.cpp`.
- `member_experience_mutation_clamps_like_oe` was moved into `tests/PartyRegressionTests.cpp`.
- `default_party_seed_first_member_matches_requested_spell_state_and_inventory` was moved into
  `tests/PartyRegressionTests.cpp`.
- `map_navigation_matches_authoritative_world_map` was moved into `tests/MapStatsRegressionTests.cpp`.
- `map_navigation_rows_apply_explicit_arrival_positions` was moved into `tests/MapStatsRegressionTests.cpp`.
- `inventory_auto_placement_uses_grid_rules` was moved into `tests/PartyRegressionTests.cpp`.
- `inventory_auto_placement_fills_columns_vertically` was moved into `tests/PartyRegressionTests.cpp`.

## Recommended Migration Order

1. Move `doctest-direct` party, inventory, item, character-sheet, navigation, gold/chest, and simple data checks.
2. Move Arcomage cases by extracting `ArcomageRegressionHarness` into `tests/` or a small reusable test helper.
3. Move spell backend cases by adding a fake/shared world runtime test fixture instead of initializing outdoor runtime.
4. Move house/dialogue/service cases by extracting reusable house/dialogue fixtures from the headless file.
5. Move event-runtime cases only after there is a focused event test harness that can execute scripts without
   constructing full outdoor application/world state.
6. Keep true world/application smoke tests headless. Those should be fewer and intentionally integration-level.

## `doctest-direct`

- 022 `chest` L6441: `gold_heap_amount_thresholds_match_oe_ranges`
- 023 `chest` L6470: `chest_loot_fixed_items_follow_item_identification_rule`
- 024 `chest` L6512: `chest_loot_random_generation_follows_item_identification_rule`
- 027 `arcomage` L6697: `arcomage_selected_card_data_matches_expected`
- 037 `dialogue` L7370: `arcomage_library_match_sanity`
- 081 `dialogue` L10271: `party_ground_movement_blocks_water_entry_without_water_walk`
- 082 `dialogue` L10322: `party_airborne_movement_allows_water_entry_without_water_walk`
- 111 `dialogue` L12842: `recovery_enchant_increases_recovery_progress`
- 130 `dialogue` L13988: `item_generator_unique_rare_item_marks_party_and_does_not_repeat`
- 131 `dialogue` L14059: `house_data_magic_guild_types_are_explicit`
- 157 `dialogue` L15720: `roster_join_offer_mapping_samples`
- 170 `dialogue` L16733: `character_sheet_uses_equipped_items_for_combat_and_ac`
- 171 `dialogue` L16794: `character_sheet_primary_stats_do_not_double_count_equipment_bonuses`
- 172 `dialogue` L16832: `character_sheet_uses_na_for_ranged_without_bow`
- 173 `dialogue` L16873: `character_sheet_marks_experience_as_trainable_at_oe_threshold`
- 174 `dialogue` L16915: `character_sheet_resistance_split_does_not_double_count_equipment_bonuses`
- 175 `dialogue` L16953: `experience_inspect_supplement_reports_shortfall_and_max_trainable_level`
- 176 `dialogue` L16988: `recruit_roster_member_loads_birth_experience_resistances_and_items`
- 178 `dialogue` L17190: `event_experience_variable_awards_direct_member_experience_without_learning_bonus`
- 181 `dialogue` L17365: `inventory_item_use_spell_scroll_prepares_master_cast`
- 182 `dialogue` L17410: `inventory_item_use_spellbook_consumes_on_success_when_school_and_mastery_match`
- 186 `dialogue` L17723: `inventory_item_use_spellbook_fails_when_spell_is_already_known`
- 187 `dialogue` L17766: `inventory_item_use_spellbook_fails_without_matching_school_and_preserves_item`
- 188 `dialogue` L17815: `inventory_item_use_spellbook_fails_without_required_mastery_and_preserves_item`
- 189 `dialogue` L17864: `inventory_item_use_readable_scroll_returns_text_without_consuming`
- 190 `dialogue` L17897: `inventory_item_use_potions_and_horseshoe_apply_expected_effects`
- 193 `dialogue` L18117: `equip_plan_requires_skill_and_respects_doll_type`
- 194 `dialogue` L18162: `party_rejects_race_restricted_artifact_for_wrong_member`
- 195 `dialogue` L18226: `equip_rules_respect_class_restricted_artifacts`
- 196 `dialogue` L18263: `artifact_ring_of_planes_applies_resistance_bonuses`
- 197 `dialogue` L18321: `artifact_shield_blocks_condition_application`
- 198 `dialogue` L18389: `special_antidotes_enchant_blocks_poison_application`
- 199 `dialogue` L18478: `rare_and_special_slaying_damage_multipliers_match_target_family`
- 210 `dialogue` L19483: `lua_event_runtime_supports_evt_jump_alias`
- 230 `dialogue` L20820: `resolve_character_attack_sound_id_uses_shared_weapon_family_mapping`
- 258 `dialogue` L23648: `ring_auto_equip_uses_first_free_then_replaces_first_ring`
- 259 `dialogue` L23749: `amulet_replacement_keeps_displaced_item_held`
- 260 `dialogue` L23823: `explicit_ring_slot_replaces_selected_ring_even_with_free_slots`
- 261 `dialogue` L23907: `weapon_conflict_rules_match_expected_cases`
- 275 `dialogue` L24926: `audio_shutdown_remains_safe_after_sdl_quit`

## `doctest-with-adaptation`

- 028 `arcomage` L6739: `arcomage_player_play_amethyst_applies_expected_effects`
- 029 `arcomage` L6807: `arcomage_conditional_card_branches_match_expected_effects`
- 030 `arcomage` L6879: `arcomage_player_discard_marks_card_as_discarded`
- 031 `arcomage` L6931: `arcomage_ai_turn_can_be_simulated_headlessly`
- 032 `arcomage` L6994: `arcomage_mm8_special_cards_apply_expected_effects`
- 033 `arcomage` L7082: `arcomage_play_again_refills_hand_like_oe`
- 034 `arcomage` L7213: `arcomage_turn_change_clears_previous_shown_cards`
- 105 `dialogue` L12327: `party_spell_backend_rejects_cast_without_spell_points`
- 106 `dialogue` L12399: `party_spell_backend_haste_applies_party_buff_and_spends_mana`
- 107 `dialogue` L12476: `party_spell_backend_fire_bolt_spawns_projectile`
- 108 `dialogue` L12547: `party_spell_backend_bless_applies_character_target_buff`
- 109 `dialogue` L12623: `party_spell_backend_supports_all_defined_non_utility_spells`
- 110 `dialogue` L12761: `party_spell_scroll_override_cast_uses_fixed_master_skill_without_mana`
- 120 `dialogue` L13443: `generic_actor_dialog_resolves_lizardman_portraits`
- 121 `dialogue` L13495: `dwi_actor_peasant_news`
- 122 `dialogue` L13537: `dwi_actor_lookout_news`
- 123 `dialogue` L13567: `single_resident_auto_open`
- 124 `dialogue` L13603: `fredrick_initial_topics_exact`
- 125 `dialogue` L13644: `multi_resident_house_selection`
- 126 `dialogue` L13680: `dwi_shop_service_menu_structure`
- 127 `dialogue` L13752: `house_service_shop_standard_stock_generates_and_buys`
- 128 `dialogue` L13826: `house_service_shop_stock_uses_house_data_tiers`
- 129 `dialogue` L13917: `house_service_shop_stock_excludes_rare_items`
- 132 `dialogue` L14095: `house_service_guild_spellbook_stock_generates_and_buys`
- 133 `dialogue` L14170: `house_service_shop_sell_accepts_matching_item`
- 134 `dialogue` L14284: `dwi_temple_service_participant_identity`
- 135 `dialogue` L14326: `dwi_temple_skill_learning`
- 136 `dialogue` L14397: `dwi_guild_skill_learning`
- 137 `dialogue` L14460: `dwi_training_service_uses_active_member`
- 138 `dialogue` L14521: `dwi_training_service_stays_open_after_success`
- 139 `dialogue` L14583: `dwi_tavern_arcomage_submenu`
- 140 `dialogue` L14647: `dwi_bank_deposit_withdraw_roundtrip`
- 141 `dialogue` L14718: `brekish_topic_mutation`
- 142 `dialogue` L14763: `fredrick_topics_after_brekish_quest`
- 143 `dialogue` L14842: `fredrick_topics_exact_after_brekish_quest`
- 144 `dialogue` L14916: `award_gated_topic_stephen`
- 145 `dialogue` L14968: `hiss_quest_followup_persists_across_reentry`
- 146 `dialogue` L15024: `mastery_teacher_not_enough_gold`
- 147 `dialogue` L15077: `mastery_teacher_missing_skill`
- 148 `dialogue` L15130: `mastery_teacher_insufficient_skill_level`
- 149 `dialogue` L15185: `mastery_teacher_wrong_class`
- 150 `dialogue` L15239: `mastery_teacher_character_switch_changes_logic`
- 151 `dialogue` L15315: `mastery_teacher_offer_and_learn`
- 152 `dialogue` L15416: `actual_roster_join_rohani`
- 153 `dialogue` L15473: `actual_roster_join_rohani_full_party`
- 154 `dialogue` L15535: `actual_roster_join_dyson_direct`
- 155 `dialogue` L15580: `promotion_champion_event_primary_knight`
- 156 `dialogue` L15637: `promotion_champion_event_multiple_member_indices`
- 158 `dialogue` L15778: `synthetic_roster_join_accept`
- 159 `dialogue` L15841: `synthetic_roster_join_full_party`
- 160 `dialogue` L15941: `adventurers_inn_hire_moves_character_into_party`
- 161 `dialogue` L15994: `adventurers_inn_hire_preserves_roster_spell_knowledge`
- 162 `dialogue` L16067: `party_dismiss_moves_member_to_adventurers_inn_tail`
- 163 `dialogue` L16133: `adventurers_inn_roster_members_use_roster_portraits_and_identified_items`
- 164 `dialogue` L16207: `roster_join_mapping_and_players_can_show_topic`
- 183 `dialogue` L17459: `spellbook_speech_audio_resolves_for_success_failure_and_store_closed`
- 184 `dialogue` L17568: `damage_speech_audio_resolves_for_all_default_seed_members`
- 185 `dialogue` L17635: `damage_speech_audio_resolves_for_roster_seeded_party_members`
- 204 `dialogue` L19078: `generated_lua_event_scripts_are_loaded_from_files`
- 205 `dialogue` L19149: `generated_lua_event_scripts_load_for_every_scripted_map`
- 206 `dialogue` L19203: `outdoor_terrain_texture_atlas_builds_for_non_default_master_tiles`
- 207 `dialogue` L19261: `lua_event_runtime_has_complete_handler_inventory_for_every_scripted_map`
- 208 `dialogue` L19334: `lua_event_runtime_executes_scripted_map_handlers_without_errors`
- 215 `dialogue` L19749: `outdoor_scene_yml_matches_legacy_ddm_authored_state`
- 219 `dialogue` L20093: `outdoor_party_runtime_wait_advances_buff_durations_with_game_clock`
- 220 `dialogue` L20144: `transport_routes_filter_by_weekday_and_qbit`
- 231 `dialogue` L20902: `transport_action_spends_gold_advances_time_and_queues_map_move`
- 232 `dialogue` L21028: `tavern_rent_room_defers_recovery_until_rest_screen`
- 233 `dialogue` L21111: `temple_donate_applies_oe_reputation_gating_and_buffs`
- 262 `dialogue` L23991: `empty_house_after_departure`
- 263 `dialogue` L24023: `event_fountain_heal_and_refresh_status_work`
- 264 `dialogue` L24094: `event_luck_fountain_grants_permanent_bonus_once`
- 265 `dialogue` L24176: `event_hidden_well_uses_bank_gold_gate_and_mapvar_progress`
- 266 `dialogue` L24264: `event_beacon_actual_stat_checks_include_temporary_bonuses`
- 267 `dialogue` L24305: `event_beacon_actual_stat_checks_include_equipped_item_bonuses`
- 268 `dialogue` L24347: `event_buoys_grant_skill_points`
- 269 `dialogue` L24419: `event_palm_tree_requires_perception_skill`
- 270 `dialogue` L24495: `long_tail_tobersk_buy_topic_remains_available_after_purchase`
- 271 `dialogue` L24537: `event_tobersk_buy_and_sell_update_gold_items_and_weekday_price`
- 274 `dialogue` L24869: `event_teacher_hint_sets_autonote_and_note_fx`

## `stay-headless`

- 001 `indoor` L4389: `indoor_scene_runtime_activate_event_uses_scene_context_for_summons`
- 002 `indoor` L4454: `indoor_scene_snapshot_roundtrips_party_and_world_runtime_state`
- 003 `indoor` L4570: `party_spell_system_supports_indoor_shared_runtime_for_party_buff_and_beacon`
- 004 `indoor` L4710: `house_transport_actions_work_through_indoor_shared_world_runtime_interface`
- 005 `indoor` L4831: `indoor_movement_controller_snaps_to_floor_and_blocks_walls`
- 006 `indoor` L4944: `indoor_movement_controller_steps_over_low_wall_segments`
- 007 `indoor` L5039: `indoor_event_runtime_trigger_mechanism_uses_authored_state_semantics`
- 008 `indoor` L5137: `indoor_scene_party_buff_updates_shared_scene_party_state`
- 009 `indoor` L5222: `indoor_support_sampling_prefers_highest_floor_under_body_footprint`
- 010 `indoor` L5305: `indoor_support_sampling_prefers_raised_open_door_surface_at_d18_seam`
- 011 `indoor` L5366: `indoor_world_runtime_exposes_actor_queries_and_direct_damage`
- 012 `indoor` L5501: `party_spell_system_supports_indoor_shared_runtime_direct_actor_damage`
- 013 `indoor` L5604: `indoor_world_runtime_lethal_damage_generates_corpse_loot_and_exhausts_corpse`
- 014 `indoor` L5745: `indoor_world_runtime_summon_friendly_monster_materializes_non_hostile_actor`
- 015 `indoor` L5821: `indoor_open_mechanism_faces_are_not_used_as_support_floor`
- 016 `indoor` L5867: `indoor_d18_local_startup_override_position_allows_movement`
- 017 `indoor` L5967: `indoor_event_runtime_summon_item_materializes_sprite_object`
- 018 `indoor` L6059: `indoor_event_runtime_open_chest_materializes_layout_and_supports_grid_ops`
- 019 `indoor` L6200: `indoor_world_runtime_snapshot_roundtrips_chest_runtime_state`
- 020 `indoor` L6306: `indoor_check_monsters_killed_respects_invisible_as_dead`
- 021 `indoor` L6363: `indoor_event_runtime_cast_spell_queues_fx_request`
- 025 `chest` L6580: `dwi_chest_events_materialize_non_empty_layouts`
- 026 `chest` L6649: `dwi_chest_event_100_materializes_final_chest`
- 036 `dialogue` L7321: `dwi_tavern_arcomage_play_requests_match`
- 043 `dialogue` L7592: `local_event_457_spawns_runtime_fireball_and_cannonball_projectiles`
- 044 `dialogue` L7665: `local_event_457_cannonball_uses_gravity_but_fireball_does_not`
- 045 `dialogue` L7765: `map_delta_pickable_sprite_objects_materialize_runtime_world_items`
- 046 `dialogue` L7844: `spawn_world_item_resolves_object_mapping_and_velocity`
- 048 `dialogue` L7945: `event_summon_item_supports_item_and_object_payloads`
- 049 `dialogue` L8016: `campfire_global_event_adds_food_and_hides_on_clear`
- 050 `dialogue` L8079: `barrel_global_event_adds_permanent_stat_and_clears`
- 051 `dialogue` L8157: `event_meteor_shower_ground_impact_damages_party`
- 052 `dialogue` L8208: `dwi_world_actor_runtime_state`
- 053 `dialogue` L8245: `dwi_peasant_actor_5_does_not_flee_on_start`
- 055 `dialogue` L8336: `non_flying_actor_snaps_to_terrain`
- 056 `dialogue` L8396: `dwi_world_spawn_runtime_state`
- 057 `dialogue` L8447: `spawn_points_materialize_on_first_outdoor_load`
- 058 `dialogue` L8510: `treasure_spawn_points_materialize_world_items_on_first_outdoor_load`
- 059 `dialogue` L8573: `spawn_points_remain_metadata_after_first_visit`
- 060 `dialogue` L8682: `dwi_actor_action_sprites_present_in_monster_data`
- 061 `dialogue` L8716: `friendly_actor_does_not_engage_party`
- 062 `dialogue` L8768: `friendly_actor_can_idle_wander`
- 063 `dialogue` L8843: `friendly_actor_3_cycles_idle_and_walk`
- 064 `dialogue` L8926: `friendly_actor_3_accumulates_motion_under_tiny_deltas`
- 065 `dialogue` L8995: `actor_3_runtime_preview_changes_while_wandering`
- 066 `dialogue` L9091: `actor_51_stays_on_ship_support`
- 067 `dialogue` L9148: `actor_51_movement_preserves_ship_floor`
- 068 `dialogue` L9197: `friendly_actor_3_stands_and_faces_party_on_contact`
- 069 `dialogue` L9263: `friendly_actor_3_stops_wandering_when_party_is_near`
- 070 `dialogue` L9320: `party_attack_on_actor_3_causes_damage_and_hostility`
- 071 `dialogue` L9380: `party_attack_on_actor_3_stunned_hit_reaction_does_not_restart_on_second_hit`
- 072 `dialogue` L9504: `party_attack_on_actor_3_lethal_damage_enters_dying_before_dead`
- 073 `dialogue` L9608: `party_attack_on_actor_3_lethal_damage_stays_deadly_while_inactive`
- 074 `dialogue` L9733: `party_attack_on_actor_3_aggros_nearby_lizard_guard`
- 075 `dialogue` L9848: `party_attack_on_actor_3_causes_wimp_flee`
- 076 `dialogue` L9911: `party_attack_on_hostile_actor_61_still_applies_damage`
- 077 `dialogue` L9962: `party_movement_ignores_friendly_actor_3_collision`
- 078 `dialogue` L10066: `party_movement_collides_with_hostile_actor_61`
- 079 `dialogue` L10154: `party_is_pushed_out_of_actor_overlap`
- 080 `dialogue` L10210: `party_movement_reports_actor_contact`
- 083 `dialogue` L10378: `friendly_actor_3_preview_palette_and_frame_cycle`
- 084 `dialogue` L10445: `hostile_actor_pursues_party`
- 085 `dialogue` L10513: `hostile_actor_uses_long_party_acquisition_despite_short_relation`
- 086 `dialogue` L10592: `long_hostile_actor_pair_engages_at_2048`
- 087 `dialogue` L10675: `hostile_melee_actor_uses_side_pursuit_when_far`
- 088 `dialogue` L10740: `hostile_melee_actor_far_pursuit_accumulates_motion`
- 089 `dialogue` L10825: `hostile_melee_actor_uses_direct_pursuit_when_close`
- 090 `dialogue` L10890: `hostile_actor_51_respects_nearby_blocking_face`
- 091 `dialogue` L11013: `hostile_actor_51_ignores_hostile_actor_across_blocking_face`
- 092 `dialogue` L11229: `outdoor_geometry_reports_steep_terrain_tiles`
- 093 `dialogue` L11268: `hostile_actor_enters_attack_state`
- 094 `dialogue` L11340: `mixed_actor_53_pursues_and_can_choose_ranged_attack`
- 095 `dialogue` L11436: `mixed_actor_53_ranged_release_spawns_arrow_projectile`
- 096 `dialogue` L11528: `mixed_actor_53_arrow_hits_party_without_impact_effect`
- 097 `dialogue` L11592: `party_arrow_projectile_can_damage_actor_53`
- 098 `dialogue` L11651: `party_spell_projectile_can_damage_actor_53`
- 099 `dialogue` L11715: `party_fireball_splash_can_damage_party_near_target_actor`
- 100 `dialogue` L11837: `party_fireball_splash_can_damage_multiple_nearby_actors`
- 101 `dialogue` L11940: `mixed_actor_53_arrow_ignores_friendly_lizardman_blocker`
- 102 `dialogue` L12043: `pirate_and_lizardman_hostile_actors_damage_each_other`
- 103 `dialogue` L12142: `spell_projectile_spawns_visible_impact_effect`
- 104 `dialogue` L12232: `hostile_actor_attack_persists_when_party_moves_away`
- 112 `dialogue` L12918: `hostile_melee_actor_respects_recovery_after_attack`
- 113 `dialogue` L13014: `dwi_reinforcement_wave_event_463_spawns_all_groups`
- 114 `dialogue` L13104: `dwi_reinforcement_wave_event_463_does_not_duplicate_alive_groups`
- 115 `dialogue` L13157: `world_actor_killed_policy_actor_id_mm8`
- 116 `dialogue` L13191: `event_can_show_topic_actor_killed_uses_scene_context`
- 117 `dialogue` L13255: `world_actor_death_generates_corpse_loot`
- 118 `dialogue` L13339: `world_actor_death_emits_audio_event`
- 119 `dialogue` L13377: `world_group_killed_policy_counts_spawned_runtime_actors`
- 180 `dialogue` L17273: `party_monster_kill_grants_shared_experience`
- 200 `dialogue` L18562: `outdoor_world_time_advances_without_timer_programs`
- 201 `dialogue` L18599: `save_game_roundtrip_restores_party_world_and_movement_state`
- 202 `dialogue` L18936: `outdoor_atmosphere_prefers_delta_sky_and_matches_oe_time_windows`
- 203 `dialogue` L19036: `outdoor_atmosphere_falls_back_to_environment_mapping`
- 209 `dialogue` L19431: `out01_true_mettle_house_event_171_enters_house_1`
- 211 `dialogue` L19533: `outdoor_event_runtime_snow_override_reaches_atmosphere_state`
- 212 `dialogue` L19582: `outdoor_event_runtime_rain_override_reaches_atmosphere_state`
- 213 `dialogue` L19631: `outdoor_daily_fog_rollover_happens_at_3am_not_midnight`
- 214 `dialogue` L19697: `outdoor_red_fog_profile_tints_atmosphere_state`
- 216 `dialogue` L19838: `app_background_music_follows_selected_map`
- 217 `dialogue` L19920: `app_house_entry_pauses_background_music_until_exit`
- 218 `dialogue` L20033: `app_f5_time_advance_reduces_party_buff_duration`
- 223 `dialogue` L20410: `out02_boundary_transition_opens_west_and_east_neighbor_dialogs`
- 224 `dialogue` L20529: `map_transition_dialog_uses_transition_presentation_and_oe_copy`
- 225 `dialogue` L20608: `ordinary_damage_queues_minor_speech_reaction`
- 226 `dialogue` L20652: `major_damage_threshold_queues_minor_and_major_speech_reactions`
- 227 `dialogue` L20700: `damage_minor_speech_ignores_combat_cooldown`
- 228 `dialogue` L20721: `damage_major_speech_bypasses_active_speech_cooldowns`
- 229 `dialogue` L20742: `damage_impact_sound_request_uses_armor_family_mapping`
- 234 `dialogue` L21305: `app_tavern_rent_room_closes_dialog_runs_rest_ui_and_wakes_at_6am`
- 235 `dialogue` L21456: `app_transport_map_move_applies_cross_map_heading`
- 236 `dialogue` L21511: `app_pending_map_move_loads_outdoor_runtime_at_explicit_coordinates`
- 237 `dialogue` L21586: `outdoor_scene_start_uses_authored_party_start_facing`
- 238 `dialogue` L21619: `outdoor_scene_forward_motion_follows_positive_world_yaw`
- 239 `dialogue` L21692: `outdoor_support_floor_resolves_the_windling_at_original_coordinates`
- 240 `dialogue` L21773: `app_boundary_map_transition_confirm_preserves_world_direction_on_all_edges`
- 241 `dialogue` L21893: `app_map_transition_confirm_applies_oe_travel_side_effects`
- 242 `dialogue` L22072: `app_map_transition_cancel_leaves_state_unchanged`
- 243 `dialogue` L22179: `game_audio_nonresettable_common_sounds_do_not_restart_active_impact_clip`
- 244 `dialogue` L22213: `app_quicksave_quickload_restores_inventory_barrel_shop_and_qbits`
- 245 `dialogue` L22433: `closed_house_entry_is_rejected_before_house_mode_with_oe_status_text`
- 246 `dialogue` L22509: `app_quicksave_quickload_preserves_empty_house_after_departure`
- 247 `dialogue` L22588: `app_open_house_action_rejects_after_closing_time`
- 248 `dialogue` L22684: `app_service_house_entry_opens_true_mettle_root_menu`
- 249 `dialogue` L22751: `app_party_defeat_zeros_gold_increments_num_deaths_and_uses_expected_respawn_map`
- 250 `dialogue` L22864: `app_regular_house_entry_auto_opens_single_resident_dialog`
- 251 `dialogue` L22934: `app_single_teacher_house_entry_unlocks_teacher_autonote`
- 252 `dialogue` L23068: `app_outdoor_decoration_billboard_activation_uses_global_decoration_events`
- 253 `dialogue` L23230: `app_pending_map_move_loads_indoor_runtime`
- 254 `dialogue` L23289: `dwi_terrain_atlas_does_not_leave_opaque_magenta_water_transition_fill`
- 255 `dialogue` L23366: `app_startup_boots_seeded_out01_session`
- 256 `dialogue` L23485: `app_adventurers_inn_house_opens_character_overlay`
- 257 `dialogue` L23561: `app_quicksave_quickload_preserves_visited_map_runtime_state`
- 272 `dialogue` L24604: `app_npc_granted_item_enters_held_cursor_slot`
- 273 `dialogue` L24706: `app_npc_granted_item_displaces_previous_held_item_to_inventory_or_ground`
