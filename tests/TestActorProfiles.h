#pragma once

// Actor profiles for tests, on stock MM7 monsters: a world's actor_profiles.yml (devdocs/ACTOR_PROFILES.md) that no
// shipped world needs to declare. profiletest.odm takes the species defaults; the map itself does not exist.
namespace OpenYAMM::Tests
{
inline constexpr const char *TestActorProfilesYaml = R"yaml(schema: openyamm.actorProfiles.v1
profiles:
  mm7.test_heroism_caster:
    monster: 405
    spell1: {id: 51, chance: 10, skill: 4, mastery: 2}
  mm7.test_stay_friendly:
    monster: 405
    party_damage_reaction: stay_friendly
  mm7.test_troll_clubman:
    monster: 58
    name: Test Troll Clubman
    spell1: {id: 77, chance: 5, skill: 3, mastery: 4}
  mm7.test_troll_geomancer:
    monster: 59
    name: Test Troll Geomancer
    attack1_element: Earth
    spell1: {id: 77, chance: 11, skill: 5, mastery: 4}
    spell2: {id: 37, chance: 15, skill: 10, mastery: 2}
  mm7.test_troll_emberlord:
    monster: 60
    name: Test Troll Emberlord
    attack1_element: Fire
    spell1: {id: 77, chance: 20, skill: 7, mastery: 4}
    spell2: {id: 2, chance: 15, skill: 16, mastery: 4}
  mm7.test_bogling: {monster: 88, name: Test Bogling, on_hit: none}
  mm7.test_bog_dweller: {monster: 89, name: Test Bog Dweller, on_hit: none}
  mm7.test_bog_elder: {monster: 90, name: Test Bog Elder, on_hit: poison1}
  mm7.test_freebooter: {monster: 10, name: Test Freebooter}
  mm7.test_pirate_magi: {monster: 17, name: Test Pirate Magi}
map_defaults:
  profiletest.odm: [mm7.test_bogling, mm7.test_bog_dweller, mm7.test_bog_elder, mm7.test_freebooter,
    mm7.test_pirate_magi]
)yaml";
}
