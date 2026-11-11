#include "game/scenario/ScenarioYamlLoader.h"

#include <sstream>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using KeyList = std::vector<std::string_view>;

// The payload keys a step may carry. Each list names the keys the runner reads, then (after "recorded:") the fields a
// recorded trace export writes for context that the runner keeps but does not check. Any other key is a load error:
// a typo or a check the runner does not have would otherwise pass silently.
const KeyList CommonStepKeys = {"note", "reason", "source_note", "game_minutes"};

const KeyList PoseKeys = {"map", "x", "y", "z", "yaw", "yaw_degrees", "pitch", "pitch_degrees"};

const KeyList MechanismKeys = {
    "id", "state", "new_state", "moving", "spinning", "spin_rate_min",
    // recorded:
    "kind", "action", "raw_action", "previous_state", "was_moving", "door_slot", "move_length", "open_speed",
    "close_speed"};

const KeyList InteractionReplayKeys = {
    "pose", "expect", "kind", "name", "hit", "distance", "scene_kind", "target_kind", "target_index", "face_index",
    "triggered_event", "trigger", "attributes", "world_item_index", "item_id", "sprite_id",
    // recorded:
    "map", "method", "has_hit", "can_activate"};

// Top-level keys of an assert step.
const KeyList AssertKeys = {
    "map", "inventory_any_member", "inventory", "equipped_item", "item_set_bonus", "held_item", "item_visible",
    "world_item_state",
    "item_received", "world_item_spawned", "chest_contains_quest_item", "corpse_contains_quest_item",
    "award_acquired", "award_cleared", "map_arrived", "map_loaded", "map_var_changed", "decor_var_changed",
    "state_dump_map_var", "named_map_var_changed", "state_dump_named_map_var", "named_global_var_changed",
    "state_dump_named_global_var", "runtime_event_variable", "actor_visible", "projectiles", "party_health",
    "homing_ends", "actor_count", "buff", "condition", "map_transition_requested", "map_transition_confirmed",
    "map_transition_canceled",
    "chest_opened", "actor_dialog_started", "pressure_plate_triggered", "dialogue_canceled", "dialog",
    "input_prompt", "new_game_party_member", "new_game_party_skill", "qbit_set", "qbit_clear", "ruleset",
    "mechanism", "gold", "food", "game_hour", "charges", "dimension_door", "combat_log", "journal_map_note",
    "quick_item_ring", "quick_item_popup", "water", "ai_trace", "autonote", "teacher_ledger", "sprite_hidden",
    "sprite_shown",
    "chest_view", "party_position", "turn_based", "member_points", "light", "scripted_fog", "recovering_members",
    // recorded:
    "scene_kind", "new_game_starting", "new_game_started", "state_dump_party", "state_dump_party_member",
    "state_dump_party_skill", "follower_hired", "follower_left", "gold_received", "starting_items"};

// Keys inside the assert blocks the runner checks field by field.
struct NestedKeys
{
    std::string_view block;
    KeyList keys;
};

const std::vector<NestedKeys> AssertBlockKeys = {
    {"projectiles", {"source", "source_monster_id", "min_count", "max_count", "homing", "toward_party_within_degrees",
        "report"}},
    {"homing_ends", {"source_monster_id", "hit", "min_count", "max_count", "report"}},
    {"party_health", {"full"}},
    {"item_set_bonus", {"member_index", "set_id", "active"}},
    {"actor_count", {"name", "monster_id", "boss", "shrunk", "hurt", "hostile", "near", "min", "max"}},
    {"buff", {"spell_id", "present", "member_index", "remaining_min", "remaining_max"}},
    {"turn_based", {"active", "stage", "front_member", "actor_index", "actor_queued", "actor_effect", "effect_min",
        "effect_max", "report"}},
    {"member_points", {"member_index", "spell_points_min", "spell_points_max", "health_min", "health_max"}},
    {"condition", {"name", "present", "member_index"}},
    {"charges", {"started", "hits", "misses", "frenzies", "min_started", "min_hits", "min_misses", "min_frenzies"}},
    {"journal_map_note", {"map", "id", "text", "present"}},
    {"autonote", {"id", "present"}},
    {"teacher_ledger", {"continent", "bought"}},
    {"quick_item_ring", {"open", "member_index"}},
    {"chest_view", {"open", "chest_id"}},
    {"party_position", {"x", "y", "radius", "z_min", "z_max"}},
    {"quick_item_popup", {"kind", "member_index"}},
    {"dimension_door", {"pending", "without_quest"}},
    {"light", {"key", "on"}},
    {"scripted_fog", {"active", "near", "far"}},
    {"water", {"state", "eye_under", "breath_min", "breath_max", "drowning_ticks_min", "drowning_ticks_max",
        "foot_z_min", "foot_z_max"}},
    {"actor_visible", {"actor_index", "map", "name", "monster_id", "current_hp", "max_hp", "dead", "hidden",
        "hostile_to_party", "report_state", "near", "far", "faces", "has_aim_target", "has_detected_party",
        "combat_targeting_party", "shield_raised", "shield_fraction", "hp", "hp_below",
        // recorded:
        "world", "party", "yaw", "pitch", "actor_pos"}},
    {"ai_trace", {"actor_index", "arena_monster", "decision", "event", "target", "detail", "min_count", "max_count",
        "max_in_window", "within_seconds", "after", "before", "report"}},
    {"mechanism", MechanismKeys},
    {"runtime_event_variable", {"id", "value", "min", "max", "member_index"}},
    {"combat_log", {"min_entries", "dealt_min", "taken_min", "with_stages_min", "loot_min", "critical_min"}},
    {"ruleset", {"id", "difficulty", "progression", "challenge_mode", "rolled_items_min", "report_items",
        "crafted_items_min", "potion_effects_min", "potion_effects_max", "member_classes", "dimension_run",
        "dimension_quest", "madness_pending", "madness_deaths", "map_cleared", "map_slain_min",
        "bow_disabled"}},
};

struct StepKeys
{
    ScenarioStepKind kind;
    KeyList keys;
    // A free-form record (note, todo, trace_observation): any keys.
    bool anyKeys = false;
};

KeyList concatKeys(std::initializer_list<KeyList> lists)
{
    KeyList result;

    for (const KeyList &list : lists)
    {
        result.insert(result.end(), list.begin(), list.end());
    }

    return result;
}

const std::vector<StepKeys> &stepKeyTable()
{
    static const std::vector<StepKeys> table = {
        {ScenarioStepKind::NewGameFlow, {"start_map", "continent", "member_count", "party", "ruleset",
            // recorded:
            "continent_id", "continent_key", "continent_name", "source"}},
        {ScenarioStepKind::LoadMap, {"map", "pos", "direction_degrees",
            // recorded:
            "target", "map_id", "scene_kind", "start_override", "method"}},
        {ScenarioStepKind::Travel, {"map", "days", "travel_days",
            // recorded:
            "target", "method", "shortcut"}},
        {ScenarioStepKind::SetPose, concatKeys({PoseKeys, {"pose"}})},
        {ScenarioStepKind::PressAction, {"action", "member_index", "seconds", "expect_before", "expect"}},
        {ScenarioStepKind::PressInteract, InteractionReplayKeys},
        {ScenarioStepKind::SpeakNpc, {"source_id",
            // recorded:
            "map", "title"}},
        {ScenarioStepKind::SelectTopic, {"kind", "source_id", "action_id", "label", "match_label",
            "selection_index", "expect_before",
            // recorded:
            "secondary_id", "house_dialog", "enabled"}},
        {ScenarioStepKind::AnswerInput, {"text", "expect", "expect_before", "input_prompt"}},
        {ScenarioStepKind::InteractTarget, concatKeys({InteractionReplayKeys, {"source_id"}})},
        {ScenarioStepKind::InteractActor, {"actor_index", "map", "pose", "expect", "name", "hit", "npc_id",
            "group", "friendly", "scene_kind", "activated",
            // recorded:
            "method", "kind", "distance", "has_hit", "can_activate"}},
        {ScenarioStepKind::MovementSegment, {"input", "duration_ms", "seconds", "delta_game_minutes", "start",
            "expect_stop", "tolerance_xy", "tolerance_z", "loose_tolerance", "actor_collision", "actor_ai",
            "raw_start", "jump", "fly_up", "fly_down",
            // recorded:
            "raw_stop"}},
        {ScenarioStepKind::EnterDoorAt, {"map", "source_id", "target",
            // recorded:
            "action_id", "label", "destination_map", "destination_name", "destination_map_id", "required_qbit",
            "pos", "method"}},
        {ScenarioStepKind::AdvanceRuntime, {"seconds", "milliseconds", "present_dialogs", "follow_map_move"}},
        {ScenarioStepKind::AdvanceGameTime, {"minutes", "hours", "days", "after_game_minutes",
            "before_game_minutes"}},
        {ScenarioStepKind::WaitUntil, {"timeout_runtime_seconds", "seconds", "assert"}},
        {ScenarioStepKind::Assert, AssertKeys},
        {ScenarioStepKind::AssertMechanism, MechanismKeys},
        {ScenarioStepKind::CombatLoot, {"actor_index", "map", "name", "target", "item_id", "expected_item_id",
            // recorded:
            "scene_kind", "monster_id", "delivery", "pos", "item_name", "quest_like", "method"}},
        {ScenarioStepKind::DamageActor, {"actor_index", "amount", "tier", "skip_dead", "all", "expect"}},
        {ScenarioStepKind::PartyAttack, {"actor_index", "member_index", "count", "conditions", "record", "ratio_to",
            "damage_ratio", "applied_ratio", "recovery_ratio", "min_hit_rate", "max_hit_rate", "min_average",
            "max_average", "report", "attack_spell", "min_weapon_attacks", "max_weapon_attacks"}},
        {ScenarioStepKind::SetRuleset, {"options"}},
        {ScenarioStepKind::RulesetBanks, {"mm8", "mm7", "mm6", "mm9", "completed_maps", "dimension_quest_done"}},
        {ScenarioStepKind::ConsoleCommand, {"line", "expect_contains"}},
        {ScenarioStepKind::WalkTo, concatKeys({PoseKeys, {"to", "via", "radius", "timeout_seconds", "clear_hostiles",
            "expect_map", "plan", "node_limit", "close_dialogs", "expect", "z_tolerance"}})},
        {ScenarioStepKind::ClearHostiles, {"radius", "min"}},
        {ScenarioStepKind::PlayLua, {"source", "max_seconds"}},
        {ScenarioStepKind::PartyDefeat, {"wait_seconds", "knock_out", "expect_map", "expect_game_over"}},
        {ScenarioStepKind::Reload, {"name", "expect_blocked"}},
        {ScenarioStepKind::PickUp, {"item_id", "reach"}},
        {ScenarioStepKind::Climb, {"ladder", "down", "timeout_seconds"}},
        {ScenarioStepKind::QuickLoad, {"save", "expect", "expect_status"}},
        {ScenarioStepKind::GrantItem, {"item_id", "count", "member_index", "power", "state", "enchant",
            "second_enchant", "special", "rarity", "drop_level", "item_power", "charges", "identified", "equip",
            "roll_level", "boss", "seed", "dimension_map", "legendary"}},
        {ScenarioStepKind::UseItem, {"item_id", "member_index", "expect"}},
        {ScenarioStepKind::TurnBasedTurns, {"count", "max_seconds"}},
        {ScenarioStepKind::RightClickPortrait, {"item_id", "carrier_index", "member_index", "inventory", "release",
            "expect"}},
        {ScenarioStepKind::CastSpell, {"member_index", "spell_id", "skill", "mastery", "actor_index", "target_member",
            "target_point", "scroll", "expect", "expect_status"}},
        {ScenarioStepKind::PartyCharge, {"actor_index", "status", "advance_seconds", "min_moved"}},
        {ScenarioStepKind::Craft, {"member_index", "target_item_id", "worn_slot", "material_item_id", "all",
            "choice", "expect"}},
        {ScenarioStepKind::CombineGems, {"item_id", "all", "expect"}},
        {ScenarioStepKind::SpawnActor, {"monster_id", "count", "x", "y", "z", "group", "near_party", "boss_affix",
            "party_ally"}},
        {ScenarioStepKind::FireActorProjectile, {"actor_index", "ability", "damage"}},
        {ScenarioStepKind::BlinkActor, {"actor_index"}},
        {ScenarioStepKind::ExecuteEvent, {"id"}},
        {ScenarioStepKind::LuaEvent, {"source"}},
        {ScenarioStepKind::ChargeActor, {"actor_index"}},
        {ScenarioStepKind::FrenzyActor, {"actor_index"}},
        {ScenarioStepKind::AiArena, {"path", "log"}},
        {ScenarioStepKind::AiTraceDump, {"actor_index", "arena_monster", "decisions_only", "last"}},
        {ScenarioStepKind::SetupShortcut,
            {"kind", "id", "value", "item_id", "source_id", "name", "member_index", "slot", "strongest", "condition",
                "health", "spell_points"}},
        {ScenarioStepKind::SaveCheckpoint, {"name"}},
        {ScenarioStepKind::LoadCheckpoint, {"name"}},
        {ScenarioStepKind::SaveGame, {"name", "path", "required_package_schema", "rebuilt_maps", "expect_failure",
            "block_with_directory"}},
        {ScenarioStepKind::LoadGame, {"name", "path", "expect_failure"}},
        {ScenarioStepKind::Note, {"text"}},
        {ScenarioStepKind::Todo, {}, true},
        {ScenarioStepKind::TraceObservation, {}, true},
    };
    return table;
}

bool keyListContains(const KeyList &keys, std::string_view key)
{
    for (std::string_view candidate : keys)
    {
        if (candidate == key)
        {
            return true;
        }
    }

    return false;
}

std::string joinedKeys(const KeyList &keys)
{
    std::string text;

    for (std::string_view key : keys)
    {
        text += text.empty() ? "" : ", ";
        text += key;
    }

    return text;
}

void checkMapKeys(
    const YAML::Node &node,
    const KeyList &allowedKeys,
    const KeyList *pCommonKeys,
    const std::string &location,
    const std::string &context,
    std::vector<std::string> &errors)
{
    if (!node || !node.IsMap())
    {
        return;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (!iterator->first.IsScalar())
        {
            continue;
        }

        const std::string key = iterator->first.as<std::string>();

        if (keyListContains(allowedKeys, key) || (pCommonKeys != nullptr && keyListContains(*pCommonKeys, key)))
        {
            continue;
        }

        errors.push_back(location + ": unknown " + context + " key '" + key + "' (known: " + joinedKeys(allowedKeys)
            + ")");
    }
}

// Every key of a step's payload, and of the assert blocks checked field by field, must be one the runner knows.
void validateScenarioStepKeys(
    const ScenarioStep &step,
    const std::string &location,
    std::vector<std::string> &errors)
{
    const std::string stepContext = step.kindName;

    for (const StepKeys &entry : stepKeyTable())
    {
        if (entry.kind != step.kind)
        {
            continue;
        }

        if (entry.anyKeys)
        {
            return;
        }

        checkMapKeys(step.payload, entry.keys, &CommonStepKeys, location, stepContext, errors);
        break;
    }

    if (!step.payload || !step.payload.IsMap())
    {
        return;
    }

    if (step.kind == ScenarioStepKind::Assert)
    {
        for (const NestedKeys &block : AssertBlockKeys)
        {
            checkMapKeys(step.payload[std::string(block.block)], block.keys, nullptr, location,
                "assert " + std::string(block.block), errors);
        }
    }

    if (step.kind == ScenarioStepKind::WaitUntil)
    {
        const YAML::Node assertNode = step.payload["assert"];
        checkMapKeys(assertNode, {"mechanism"}, nullptr, location, "wait_until assert", errors);
        checkMapKeys(assertNode ? assertNode["mechanism"] : YAML::Node(), MechanismKeys, nullptr, location,
            "wait_until assert mechanism", errors);
    }

    if (step.kind == ScenarioStepKind::PressAction)
    {
        checkMapKeys(step.payload["expect"], {"dialogue_canceled"}, nullptr, location, "press_action expect", errors);
        checkMapKeys(step.payload["expect_before"], {"dialog"}, nullptr, location, "press_action expect_before",
            errors);
    }
}
}

std::string ScenarioYamlLoader::formatLocation(const std::filesystem::path &path, int line)
{
    std::ostringstream stream;
    stream << path.string();

    if (line > 0)
    {
        stream << ':' << line;
    }

    return stream.str();
}

bool ScenarioYamlLoader::parseMode(const std::string &value, ScenarioMode &mode)
{
    if (value == "faithful")
    {
        mode = ScenarioMode::Faithful;
        return true;
    }

    if (value == "hybrid")
    {
        mode = ScenarioMode::Hybrid;
        return true;
    }

    if (value == "unitized")
    {
        mode = ScenarioMode::Unitized;
        return true;
    }

    return false;
}

bool ScenarioYamlLoader::parseStepKind(const std::string &value, ScenarioStepKind &kind)
{
    if (value == "new_game_flow")
    {
        kind = ScenarioStepKind::NewGameFlow;
        return true;
    }

    if (value == "load_map")
    {
        kind = ScenarioStepKind::LoadMap;
        return true;
    }

    if (value == "travel")
    {
        kind = ScenarioStepKind::Travel;
        return true;
    }

    if (value == "set_pose")
    {
        kind = ScenarioStepKind::SetPose;
        return true;
    }

    if (value == "press_action")
    {
        kind = ScenarioStepKind::PressAction;
        return true;
    }

    if (value == "press_interact")
    {
        kind = ScenarioStepKind::PressInteract;
        return true;
    }

    if (value == "speak_npc")
    {
        kind = ScenarioStepKind::SpeakNpc;
        return true;
    }

    if (value == "select_topic")
    {
        kind = ScenarioStepKind::SelectTopic;
        return true;
    }

    if (value == "answer_input")
    {
        kind = ScenarioStepKind::AnswerInput;
        return true;
    }

    if (value == "interact_target")
    {
        kind = ScenarioStepKind::InteractTarget;
        return true;
    }

    if (value == "interact_actor")
    {
        kind = ScenarioStepKind::InteractActor;
        return true;
    }

    if (value == "movement_segment")
    {
        kind = ScenarioStepKind::MovementSegment;
        return true;
    }

    if (value == "enter_door_at")
    {
        kind = ScenarioStepKind::EnterDoorAt;
        return true;
    }

    if (value == "advance_runtime")
    {
        kind = ScenarioStepKind::AdvanceRuntime;
        return true;
    }

    if (value == "advance_game_time")
    {
        kind = ScenarioStepKind::AdvanceGameTime;
        return true;
    }

    if (value == "wait_until")
    {
        kind = ScenarioStepKind::WaitUntil;
        return true;
    }

    if (value == "assert")
    {
        kind = ScenarioStepKind::Assert;
        return true;
    }

    if (value == "assert_mechanism")
    {
        kind = ScenarioStepKind::AssertMechanism;
        return true;
    }

    if (value == "combat_loot")
    {
        kind = ScenarioStepKind::CombatLoot;
        return true;
    }

    if (value == "setup_shortcut")
    {
        kind = ScenarioStepKind::SetupShortcut;
        return true;
    }

    if (value == "save_checkpoint")
    {
        kind = ScenarioStepKind::SaveCheckpoint;
        return true;
    }

    if (value == "load_checkpoint")
    {
        kind = ScenarioStepKind::LoadCheckpoint;
        return true;
    }

    if (value == "save_game")
    {
        kind = ScenarioStepKind::SaveGame;
        return true;
    }

    if (value == "load_game")
    {
        kind = ScenarioStepKind::LoadGame;
        return true;
    }

    if (value == "damage_actor")
    {
        kind = ScenarioStepKind::DamageActor;
        return true;
    }

    if (value == "party_attack")
    {
        kind = ScenarioStepKind::PartyAttack;
        return true;
    }

    if (value == "grant_item")
    {
        kind = ScenarioStepKind::GrantItem;
        return true;
    }

    if (value == "ruleset_banks")
    {
        kind = ScenarioStepKind::RulesetBanks;
        return true;
    }

    if (value == "walk_to")
    {
        kind = ScenarioStepKind::WalkTo;
        return true;
    }

    if (value == "climb")
    {
        kind = ScenarioStepKind::Climb;
        return true;
    }

    if (value == "pick_up")
    {
        kind = ScenarioStepKind::PickUp;
        return true;
    }

    if (value == "reload")
    {
        kind = ScenarioStepKind::Reload;
        return true;
    }

    if (value == "party_defeat")
    {
        kind = ScenarioStepKind::PartyDefeat;
        return true;
    }

    if (value == "play_lua")
    {
        kind = ScenarioStepKind::PlayLua;
        return true;
    }

    if (value == "clear_hostiles")
    {
        kind = ScenarioStepKind::ClearHostiles;
        return true;
    }

    if (value == "console")
    {
        kind = ScenarioStepKind::ConsoleCommand;
        return true;
    }

    if (value == "quick_load")
    {
        kind = ScenarioStepKind::QuickLoad;
        return true;
    }

    if (value == "use_item")
    {
        kind = ScenarioStepKind::UseItem;
        return true;
    }

    if (value == "turn_based_turns")
    {
        kind = ScenarioStepKind::TurnBasedTurns;
        return true;
    }

    if (value == "right_click_portrait")
    {
        kind = ScenarioStepKind::RightClickPortrait;
        return true;
    }

    if (value == "cast_spell")
    {
        kind = ScenarioStepKind::CastSpell;
        return true;
    }

    if (value == "party_charge")
    {
        kind = ScenarioStepKind::PartyCharge;
        return true;
    }

    if (value == "craft")
    {
        kind = ScenarioStepKind::Craft;
        return true;
    }

    if (value == "combine_gems")
    {
        kind = ScenarioStepKind::CombineGems;
        return true;
    }

    if (value == "set_ruleset")
    {
        kind = ScenarioStepKind::SetRuleset;
        return true;
    }

    if (value == "spawn_actor")
    {
        kind = ScenarioStepKind::SpawnActor;
        return true;
    }

    if (value == "fire_actor_projectile")
    {
        kind = ScenarioStepKind::FireActorProjectile;
        return true;
    }

    if (value == "execute_event")
    {
        kind = ScenarioStepKind::ExecuteEvent;
        return true;
    }

    if (value == "lua_event")
    {
        kind = ScenarioStepKind::LuaEvent;
        return true;
    }

    if (value == "blink_actor")
    {
        kind = ScenarioStepKind::BlinkActor;
        return true;
    }

    if (value == "charge_actor")
    {
        kind = ScenarioStepKind::ChargeActor;
        return true;
    }

    if (value == "frenzy_actor")
    {
        kind = ScenarioStepKind::FrenzyActor;
        return true;
    }

    if (value == "ai_arena")
    {
        kind = ScenarioStepKind::AiArena;
        return true;
    }

    if (value == "ai_trace_dump")
    {
        kind = ScenarioStepKind::AiTraceDump;
        return true;
    }

    if (value == "note")
    {
        kind = ScenarioStepKind::Note;
        return true;
    }

    if (value == "todo")
    {
        kind = ScenarioStepKind::Todo;
        return true;
    }

    if (value == "trace_observation")
    {
        kind = ScenarioStepKind::TraceObservation;
        return true;
    }

    return false;
}

ScenarioLoadResult ScenarioYamlLoader::load(const std::filesystem::path &path) const
{
    ScenarioLoadResult result = {};
    YAML::Node root;

    try
    {
        root = YAML::LoadFile(path.string());
    }
    catch (const YAML::Exception &exception)
    {
        result.errors.push_back("failed to load scenario YAML from " + path.string() + ": " + exception.what());
        return result;
    }

    if (!root.IsMap())
    {
        result.errors.push_back(formatLocation(path, 1) + ": scenario root must be a mapping");
        return result;
    }

    if (!root["id"] || !root["id"].IsScalar())
    {
        result.errors.push_back(formatLocation(path, 1) + ": missing scalar field 'id'");
    }
    else
    {
        result.document.id = root["id"].as<std::string>();
    }

    if (root["title"])
    {
        if (!root["title"].IsScalar())
        {
            result.errors.push_back(formatLocation(path, root["title"].Mark().line + 1)
                + ": field 'title' must be scalar");
        }
        else
        {
            result.document.title = root["title"].as<std::string>();
        }
    }

    if (!root["world"] || !root["world"].IsScalar())
    {
        result.errors.push_back(formatLocation(path, 1) + ": missing scalar field 'world'");
    }
    else
    {
        result.document.world = root["world"].as<std::string>();
    }

    if (root["mode"])
    {
        if (!root["mode"].IsScalar())
        {
            result.errors.push_back(formatLocation(path, root["mode"].Mark().line + 1)
                + ": field 'mode' must be scalar");
        }
        else if (!parseMode(root["mode"].as<std::string>(), result.document.mode))
        {
            result.errors.push_back(formatLocation(path, root["mode"].Mark().line + 1)
                + ": unknown scenario mode '" + root["mode"].as<std::string>() + "'");
        }
    }

    if (root["tags"])
    {
        if (!root["tags"].IsSequence())
        {
            result.errors.push_back(formatLocation(path, root["tags"].Mark().line + 1)
                + ": field 'tags' must be a sequence");
        }
        else
        {
            for (const YAML::Node &tagNode : root["tags"])
            {
                if (!tagNode.IsScalar())
                {
                    result.errors.push_back(formatLocation(path, tagNode.Mark().line + 1)
                        + ": tag entries must be scalar");
                    continue;
                }

                result.document.tags.push_back(tagNode.as<std::string>());
            }
        }
    }

    if (!root["steps"] || !root["steps"].IsSequence())
    {
        result.errors.push_back(formatLocation(path, 1) + ": missing sequence field 'steps'");
        return result;
    }

    const YAML::Node stepsNode = root["steps"];

    for (size_t stepIndex = 0; stepIndex < stepsNode.size(); ++stepIndex)
    {
        const YAML::Node stepNode = stepsNode[stepIndex];

        if (!stepNode.IsMap())
        {
            result.errors.push_back(formatLocation(path, stepNode.Mark().line + 1)
                + ": scenario step must be a mapping");
            continue;
        }

        std::string stepKindName;
        YAML::Node payload;
        int traceSourceLine = 0;

        for (YAML::const_iterator iterator = stepNode.begin(); iterator != stepNode.end(); ++iterator)
        {
            if (!iterator->first.IsScalar())
            {
                result.errors.push_back(formatLocation(path, iterator->first.Mark().line + 1)
                    + ": scenario step keys must be scalar");
                continue;
            }

            const std::string key = iterator->first.as<std::string>();

            if (key == "source_line")
            {
                if (iterator->second.IsScalar())
                {
                    traceSourceLine = iterator->second.as<int>();
                }
                continue;
            }

            if (key == "todo" && iterator->second.IsScalar())
            {
                continue;
            }

            if (!stepKindName.empty())
            {
                result.errors.push_back(formatLocation(path, iterator->first.Mark().line + 1)
                    + ": scenario step must contain one command key");
                continue;
            }

            stepKindName = key;
            payload = iterator->second;
        }

        if (stepKindName.empty())
        {
            result.errors.push_back(formatLocation(path, stepNode.Mark().line + 1)
                + ": scenario step is missing a command key");
            continue;
        }

        ScenarioStepKind kind = ScenarioStepKind::Assert;

        if (!parseStepKind(stepKindName, kind))
        {
            result.errors.push_back(formatLocation(path, stepNode.Mark().line + 1) + " step "
                + std::to_string(stepIndex + 1) + ": unknown scenario step '" + stepKindName + "'");
            continue;
        }

        ScenarioStep step = {};
        step.kind = kind;
        step.kindName = stepKindName;
        step.payload = payload;
        step.sourcePath = path;
        step.sourceLine = stepNode.Mark().line + 1;
        step.traceSourceLine = traceSourceLine;
        step.stepIndex = stepIndex + 1;
        validateScenarioStepKeys(step,
            formatLocation(path, step.sourceLine) + " step " + std::to_string(step.stepIndex) + " (" + stepKindName
                + ")",
            result.errors);
        result.document.steps.push_back(step);
    }

    return result;
}
}
