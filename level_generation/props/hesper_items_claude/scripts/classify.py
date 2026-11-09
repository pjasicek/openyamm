"""Classifies every Hesper item's ground model (design/kreegan_world/data/items.txt) by route and writes
classification.json: one design per icon, items sharing an icon share its model (the engine binds by icon).

Routes (GROUND_ITEM_3D_PLAYBOOK.md, GROUND_ITEMS_3D_PLAN.md):
  meshy    Meshy Smart Topology, untextured (5 credits), Codex-painted views baked into PBR
  blender  built from components in Blender (regular shapes: rings, chains, canisters, bows, belts), painted the same
  flat     the cheaper route for flat items: a slab or plate in Blender carrying the icon's face
  variant  the mesh of another design (`of`), repainted: no new geometry
  reuse    another project's finished ground model of the same thing, copied as the export
  blocked  the item has no icon of its own yet (visual_status needs_art)
The HD master is the icon's own 1254 px Codex original (art/item_icons/raw), selected in its generation records.
Usage: python3 -I classify.py"""
import csv
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(REPO, 'design', 'kreegan_world', 'art', 'item_icons')
ITEMS = os.path.join(REPO, 'design', 'kreegan_world', 'data', 'items.txt')
STAGE_ITEMS = os.path.join(REPO, 'level_generation', 'projects', 'hesper_stage', 'items.yml')
MESHY_CREDITS = 5

# The items that share one icon in the stage (hesper_stage/items.yml): the twelve colony log tablets and the six
# written readables have one tablet and one slate picture between them.
SHARED_ICONS = {**{f'hes_colony_log_tablet_{n}': 'hes_colony_log_tablet' for n in range(1, 13)},
                **{name: 'hes_data_slate' for name in ('hes_founders_charter', 'hes_drone_control_duty_log',
                                                       'hes_doctor_ilses_notes', 'hes_foundry_work_order',
                                                       'hes_hales_last_note', 'hes_a_nobles_letter')}}

# icon: (family, route, note); route 'variant' names the design it repaints as `of:<icon>`.
ROUTES = {
    # Energy guns: Kreegan resin and bone grown round Ancient emitters; sculptural housings.
    'hes_pulse_pistol': ('gun', 'meshy', ''),
    'hes_noble_sidearm': ('gun', 'meshy', ''),
    'hes_ion_carbine': ('gun', 'meshy', ''),
    'hes_lancer_carbine': ('gun', 'meshy', ''),
    'hes_arc_rifle': ('gun', 'meshy', ''),
    'hes_storm_rifle': ('gun', 'meshy', ''),
    'hes_scatter_lance': ('gun', 'meshy', ''),
    'hes_breaker_lance': ('gun', 'meshy', ''),
    'hes_disruptor_cannon': ('gun', 'meshy', ''),
    'hes_founders_repeater': ('gun', 'meshy', 'colonial ceramic and gold, the one non-Kreegan gun'),
    # Melee: the blades and shafts are Blender (straight, regular); the sculpted hilts, heads and grips come from
    # one Smart Topology job each (the polearm and dagger sessions' hybrid, 2026-10-18).
    'hes_vibro_knife': ('dagger', 'meshy', 'hybrid: Blender blade, Meshy grip'),
    'hes_noble_fang': ('dagger', 'meshy', 'hybrid: Blender blade, Meshy grip'),
    'hes_ssekhs_fang': ('dagger', 'meshy', 'hybrid: Blender blade, Meshy grip'),
    'hes_plasma_saber': ('sword', 'meshy', 'hybrid: Blender energy blade, Meshy hilt'),
    'hes_plasma_longblade': ('sword', 'meshy', 'hybrid: Blender energy blade, Meshy hilt'),
    'hes_vhorrax_courtesy': ('sword', 'meshy', 'hybrid: Blender blade, Meshy hilt'),
    'hes_arc_maul': ('mace', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_thunder_maul': ('mace', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_forgemasters_hammer': ('mace', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_phase_axe': ('axe', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_phase_cleaver': ('axe', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_mraals_cleaver': ('axe', 'meshy', 'hybrid: Blender haft, Meshy head'),
    'hes_ion_pike': ('spear', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_lattice_halberd': ('spear', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_coil_spear': ('spear', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_overseers_rod': ('staff', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_lattice_staff': ('staff', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_conductors_baton': ('staff', 'meshy', 'hybrid: Blender shaft, Meshy head'),
    'hes_vreths_first_cut': ('sword', 'reuse', 'added 2026-10-24: hes_harrower_codex warglaives/ground'),
    'hes_vreths_last_cut': ('sword', 'reuse', 'added 2026-10-24: hes_harrower_codex warglaives/ground'),
    'hes_spinebow': ('bow', 'blender', 'swept limbs and a real string (ranged session route)'),
    'hes_noble_recurve': ('bow', 'blender', 'swept limbs and a real string'),
    'hes_noblebone_longbow': ('bow', 'blender', 'swept limbs and a real string'),
    # Emitters (Hesper's shields): thick domed devices, not plates.
    'hes_buckler_emitter': ('emitter', 'meshy', ''),
    'hes_bastion_emitter': ('emitter', 'meshy', ''),
    'hes_last_light_of_hesper': ('emitter', 'meshy', ''),
    # Worn equipment: volumetric (playbook, section 1).
    'hes_weave_suit': ('body armor', 'meshy', ''),
    'hes_refractor_weave': ('body armor', 'meshy', ''),
    'hes_carapace_mail': ('body armor', 'meshy', ''),
    'hes_black_carapace': ('body armor', 'meshy', ''),
    'hes_grafted_plate': ('body armor', 'meshy', ''),
    'hes_bastion_plate': ('body armor', 'meshy', ''),
    'hes_bulwarks_shell': ('body armor', 'meshy', ''),
    'hes_rebreather_helm': ('helm', 'meshy', ''),
    'hes_sensor_helm': ('helm', 'meshy', ''),
    'hes_survey_helm': ('helm', 'meshy', ''),
    'hes_grip_gauntlets': ('gauntlets', 'meshy', 'a pair'),
    'hes_power_gauntlets': ('gauntlets', 'meshy', 'a pair'),
    'hes_load_gauntlets': ('gauntlets', 'meshy', 'a pair'),
    'hes_mag_boots': ('boots', 'meshy', 'a pair'),
    'hes_grav_boots': ('boots', 'meshy', 'a pair'),
    'hes_anchor_boots': ('boots', 'meshy', 'a pair'),
    'hes_ash_cloak': ('cloak', 'meshy', 'a folded heap'),
    'hes_refractor_mantle': ('cloak', 'meshy', 'a folded heap'),
    'hes_insulator_cloak': ('cloak', 'meshy', 'a folded heap'),
    'hes_vreths_mantle': ('cloak', 'meshy', 'a folded heap'),
    'hes_utility_belt': ('belt', 'blender', 'strap loop and buckle (jewellery session route)'),
    'hes_capacitor_belt': ('belt', 'blender', 'strap loop with cells'),
    'hes_reserve_belt': ('belt', 'blender', 'strap loop with cells'),
    # Jewelry: real shanks, settings and chains in Blender (jewellery session route, no Meshy).
    'hes_conductor_ring': ('ring', 'blender', 'twisted wire band'),
    'hes_induction_ring': ('ring', 'blender', ''),
    'hes_crown_band': ('ring', 'blender', ''),
    'hes_stormglass_ring': ('ring', 'blender', 'two set stones'),
    'hes_xiths_sight': ('ring', 'blender', 'large oval setting'),
    'hes_lattice_pendant': ('amulet', 'blender', 'chain and faceted pendant'),
    'hes_surveyors_pendant': ('amulet', 'blender', 'chain and diamond frame'),
    'hes_nightglass_amulet': ('amulet', 'blender', 'chain and teardrop stone'),
    'hes_jammer': ('amulet', 'blender', 'egg pendant on a loop'),
    'hes_gatekeepers_gorget': ('amulet', 'meshy', 'a sculpted collar'),
    # Implants: small devices; a tier II whose silhouette repeats its tier I repaints that mesh.
    'hes_dermal_1': ('implant', 'flat', 'woven square plate, clawed corners'),
    'hes_dermal_2': ('implant', 'variant', 'of:hes_dermal_1'),
    'hes_capacitor_1': ('implant', 'blender', 'lathed lozenge, blue core'),
    'hes_capacitor_2': ('implant', 'variant', 'of:hes_capacitor_1'),
    'hes_ablative_1': ('implant', 'meshy', 'cracked rounded plates'),
    'hes_ablative_2': ('implant', 'meshy', 'hexagonal plates: a different silhouette'),
    'hes_vital_1': ('implant', 'meshy', 'gem in a claw cage'),
    'hes_vital_2': ('implant', 'variant', 'of:hes_vital_1'),
    'hes_optic_1': ('implant', 'meshy', 'lens in a curved housing'),
    'hes_optic_2': ('implant', 'variant', 'of:hes_optic_1'),
    'hes_reflex_1': ('implant', 'meshy', 'three-armed node'),
    'hes_reflex_2': ('implant', 'variant', 'of:hes_reflex_1'),
    'hes_damping_1': ('implant', 'flat', 'woven square panel'),
    'hes_damping_2': ('implant', 'variant', 'of:hes_damping_1'),
    'hes_regulator_1': ('implant', 'blender', 'ring disc, blue core'),
    'hes_regulator_2': ('implant', 'blender', 'open ring disc'),
    'hes_damper_1': ('implant', 'meshy', 'U clamp'),
    'hes_damper_2': ('implant', 'variant', 'of:hes_damper_1'),
    'hes_resonator_1': ('implant', 'blender', 'triangular frame, purple crystal'),
    'hes_resonator_2': ('implant', 'variant', 'of:hes_resonator_1'),
    'hes_resonator_3': ('implant', 'variant', 'of:hes_resonator_1'),
    'hes_coupler_1': ('implant', 'blender', 'zigzag conduit, swept'),
    'hes_coupler_2': ('implant', 'variant', 'of:hes_coupler_1'),
    'hes_coupler_3': ('implant', 'variant', 'of:hes_coupler_1'),
    'hes_trigger_graft': ('implant', 'meshy', 'bent clawed arm'),
    'hes_striking_lattice': ('implant', 'flat', 'diamond plate with a green stone'),
    'hes_reflex_booster': ('implant', 'meshy', 'crescent with an orange stone'),
    'hes_kreegan_gland': ('implant', 'meshy', 'organic pod'),
    'hes_asters_lens': ('implant', 'meshy', 'lens in a curled shell'),
    'hes_voice_splinter': ('implant', 'meshy', 'crystal in a claw'),
    # Supplies.
    'hes_shield_cell': ('supply', 'blender', 'canister'),
    'hes_shield_burst_cell': ('supply', 'blender', 'triple canister'),
    'hes_ion_cell': ('supply', 'blender', 'canister'),
    'hes_stim': ('supply', 'blender', 'injector'),
    'hes_emp_grenade': ('supply', 'blender', 'sphere with studs'),
    'hes_breach_charge': ('supply', 'blender', 'strapped box charge'),
    'hes_hesper_ration': ('supply', 'blender', 'wrapped block'),
    'hes_kreegan_alloy': ('supply', 'meshy', 'rough resin-metal chunk'),
    'hes_engram_shard': ('engram', 'blender', 'cut crystal (jewellery session crystals)'),
    'hes_engram': ('engram', 'meshy', 'crystal in a gold claw mount'),
    'hes_engram_core': ('engram', 'meshy', 'crystal in a cage'),
    # Quest items.
    'hes_hive_navigation_crystal': ('quest', 'meshy', 'crystal in claws'),
    'hes_zod_brood_record': ('quest', 'meshy', 'organic pod'),
    'hes_glassback_heart': ('quest', 'meshy', 'organic heart'),
    'hes_founders_head': ('quest', 'meshy', 'a statue head'),
    'hes_ghulkats_collar_key': ('quest', 'meshy', 'organic two-pronged key'),
    'hes_thrixs_token': ('quest', 'meshy', 'carved bone token'),
    'hes_aster_shard_1': ('quest', 'blender', 'a slab in its icon\'s outline; its Meshy block (batch 4) went unused'),
    'hes_aster_shard_2': ('quest', 'blender', 'crystal shard'),
    'hes_aster_shard_3': ('quest', 'blender', 'crescent crystal'),
    'hes_aster_shard_4': ('quest', 'blender', 'crystal shard'),
    'hes_ion_coil': ('quest', 'blender', 'coil torus'),
    'hes_nav_matrix': ('quest', 'blender', 'boxed crystal grid'),
    'hes_lander_log_core': ('quest', 'blender', 'lathed cylinder'),
    'hes_pilots_core': ('quest', 'blender', 'lathed cylinder'),
    'hes_court_seal': ('quest', 'flat', 'medallion disc'),
    'hes_archive_armoury_key': ('quest', 'flat', 'key card'),
    'hes_militia_warrant': ('readable', 'flat', 'sealed envelope (letters batch construction)'),
    'hes_colony_log_tablet': ('readable', 'flat', 'tablet slab: twelve tablets share it'),
    'hes_data_slate': ('readable', 'flat', 'slate slab: six readables share it'),
}


def selected_masters():
    """icon -> its selected 1254 px Codex original (relative to art/item_icons)."""
    masters = {}
    for name in ('generation_runs.json', 'generation_runs_p4.json', 'generation_runs_expansion.json'):
        for run in json.load(open(os.path.join(ART, name))):
            if not run.get('selected'):
                continue
            stem = os.path.basename(run['file'])[:-4]
            if run['file'].startswith('raw/'):
                icon = stem.rsplit('_', 1)[0]
                masters[icon] = run['file']
            else:
                masters[stem] = f'raw/{stem}_1.png'
    # Icons cut from another project's reference (Vreth's warglaives, items_warglaives.json): their 1024 px masters.
    for entry in json.load(open(os.path.join(ART, 'items_warglaives.json'))):
        masters[entry['file'][:-4]] = 'masters/' + entry['file']
    return masters


def main():
    with open(ITEMS, newline='') as stream:
        rows = [row for row in csv.reader(stream, delimiter='\t') if row][1:]
    staged = open(STAGE_ITEMS).read()
    masters = selected_masters()
    designs = {}
    for row in rows:
        item_id, icon, name = int(row[0]), row[1], row[2]
        icon = SHARED_ICONS.get(icon, icon)
        if not os.path.exists(os.path.join(ART, 'x2', icon + '.png')):
            entry = designs.setdefault(icon, {'family': 'quest', 'route': 'blocked', 'credits': 0,
                                              'note': 'no icon of its own yet (visual_status needs_art)'})
        else:
            family, route, note = ROUTES[icon]
            entry = designs.setdefault(icon, {'family': family, 'route': route, 'credits': 0, 'note': note})
            if route == 'variant':
                entry['of'] = note[3:]
                entry['note'] = ''
            entry['credits'] = MESHY_CREDITS if route == 'meshy' else 0
            master = masters.get(icon)
            assert master and os.path.exists(os.path.join(ART, master)), icon
            entry['master'] = master
        entry.setdefault('items', []).append({'id': item_id, 'name': name, 'staged': f'id: {item_id},' in staged})
    assert set(ROUTES) <= set(designs), set(ROUTES) - set(designs)
    with open(os.path.join(HERE, 'classification.json'), 'w') as handle:
        json.dump(designs, handle, indent=1)
        handle.write('\n')
    counts = {}
    for entry in designs.values():
        counts[entry['route']] = counts.get(entry['route'], 0) + 1
    print(len(rows), 'items,', len(designs), 'designs', counts,
          sum(entry['credits'] for entry in designs.values()), 'credits')


main()
