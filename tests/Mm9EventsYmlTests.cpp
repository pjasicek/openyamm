#include "doctest/doctest.h"

#include "game/maps/Mm9EventsYml.h"

#include <optional>
#include <string>

TEST_CASE("MM9 events YAML loader reads source object registry without touching legacy event data")
{
    const std::string yamlText = R"(
format_version: 1
kind: mm9_events
source_dat: TEST.dat
source_raw_objects: test.raw_objects.yml
generated:
  lua: ../events/test.lua
  script_ir: ../events/test.script_ir.yml
objects:
  - object_id: mm9:test:object:0
    source_object_index: 0
    source_class: Door
    source_name: DoorA
    classifications: [mechanism, interaction]
    raw_property_count: 8
    raw_object_ref: test.raw_objects.yml#objects[0]
    raw_properties:
      - property_index: 0
        name: Filename
        decoded: true
        code: 0
        flags: 0
        raw_ref: properties[0]
      - property_index: 1
        name: Visible
        decoded: true
        code: 5
        flags: 0
        raw_ref: properties[1]
    normalized_properties:
      Filename: models\Guard.ABC
      Skin: skins\guard3.dtx
      ScriptName: guard.scr
      ScriptParams: patrol=1
      Visible: 1
      Solid: 1
      Rayhit: 1
      NeedsTick: 0
      Scale: 1.25
mechanisms:
  - mechanism_id: mm9:test:object:0:mechanism
    object_id: mm9:test:object:0
    source_object_index: 0
    source_class: Door
    source_name: DoorA
    mechanism:
      kind: linear_door
      linear:
        move_dir_lt: [1.0, 0.0, 0.0]
        move_dist_lt: 64.0
        open_speed_lt_per_sec: 32.0
      rotation:
        rotation_point_lt: [184.0, 80.0, 1632.0]
        rotation_angles_deg: [0.0, 90.0, 0.0]
      source_units: lithtech_mm9
    activation:
      start_open: false
      locked: true
    trigger_outputs:
      - phase: open
        slot: 0
        target_name: DoorController
        message_name: unlock
        resolution: resolved
      - phase: close
        slot: 1
        target_name: MissingController
        message_name: lock
        resolution: unresolved
triggers:
  - trigger_id: mm9:test:object:1:trigger
interactions:
  - interaction_id: mm9:test:object:0:interaction
bindings:
  - object_id: mm9:test:object:0
    source_object_index: 0
    targets:
      - target_kind: odm_bmodel
        target_id: odm:bmodel:12
        confidence: exact_source_model_name
        bmodel_index: 12
        bmodel_name: DoorA
        source_model_name: DoorA
        source_polygon_group:
          source_model_index: 12
          source_model_name: DoorA
          source_poly_count: 8
          source_surface_count: 3
          bounds_min_lt: [100.0, 60.0, 1500.0]
          bounds_max_lt: [220.0, 100.0, 1700.0]
          roles:
            movable: true
        nearest_movable_world_models_by_rotation_point:
          - source_model_index: 12
            source_name: DoorA
            movable: true
            world_translation_lt: [184.0, 80.0, 1600.0]
            distance_from_rotation_point_lt: 32.0
            claimed_by_exact_bindings:
              - source_object_index: 6
                source_name: NearDoor
                confidence: exact_source_model_name
        nearest_movable_world_models_by_position:
          - source_model_index: 14
            source_name: DoorCandidate
            movable: true
            world_translation_lt: [200.0, 80.0, 1632.0]
            distance_from_position_lt: 16.0
scripts:
  - script_id: doorlock.scr
    source_path: DOORLOCK.scr
    registered_triggers:
      - line: 10
        message: use
        callback: OnUse
        arguments_raw: '"use", OnUse'
    trigger_edges:
      - line: 12
        target_expression: DoorA
        message_expression: close
        arguments_raw: DoorA, close
    movement_commands:
      - line: 14
        command: MoveObject
        arguments_raw: DoorA, 64
    unknown_commands:
      - line: 11
        command: CustomCommand
        arguments_raw: Something, 1
    command_count: 7
unresolved:
  - kind: unresolved_binding
    source_object_index: 9
    source_name: ScriptObject0
    source_class: ScriptObject
    severity: warning
    evidence:
      nearest_movable_world_models_by_position:
        - source_model_index: 14
          source_name: DoorCandidate
          movable: true
          world_translation_lt: [200.0, 80.0, 1632.0]
          distance_from_position_lt: 16.0
)";

    OpenYAMM::Game::Mm9EventsYmlLoader loader = {};
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        loader.loadFromText(yamlText, errorMessage);

    REQUIRE_MESSAGE(eventsData.has_value(), errorMessage.c_str());
    CHECK(eventsData->formatVersion == 1);
    CHECK(eventsData->kind == "mm9_events");
    CHECK(eventsData->sourceRawObjects == "test.raw_objects.yml");
    CHECK(eventsData->generatedLua == "../events/test.lua");
    CHECK(eventsData->generatedScriptIr == "../events/test.script_ir.yml");
    REQUIRE(eventsData->objects.size() == 1);
    CHECK(eventsData->objects[0].sourceObjectIndex == 0);
    CHECK(eventsData->objects[0].sourceClass == "Door");
    CHECK(eventsData->objects[0].sourceName == "DoorA");
    CHECK(eventsData->objects[0].rawObjectRef == "test.raw_objects.yml#objects[0]");
    CHECK(eventsData->objects[0].rawPropertyCount == 8);
    REQUIRE(eventsData->objects[0].rawProperties.size() == 2);
    CHECK(eventsData->objects[0].rawProperties[0].name == "Filename");
    CHECK(eventsData->objects[0].rawProperties[0].rawRef == "properties[0]");
    CHECK(eventsData->objects[0].normalizedProperties.at("Filename") == "models\\Guard.ABC");
    CHECK(eventsData->objects[0].normalizedProperties.at("ScriptName") == "guard.scr");
    CHECK(eventsData->objects[0].normalizedProperties.at("Rayhit") == "1");
    REQUIRE(eventsData->objects[0].classifications.size() == 2);
    CHECK(eventsData->objects[0].classifications[0] == "mechanism");
    CHECK(eventsData->objects[0].classifications[1] == "interaction");
    CHECK(eventsData->mechanismCount == 1);
    REQUIRE(eventsData->mechanisms.size() == 1);
    CHECK(eventsData->mechanisms[0].kind == "linear_door");
    CHECK(eventsData->mechanisms[0].activation.hasLocked);
    CHECK(eventsData->mechanisms[0].activation.locked);
    CHECK(eventsData->mechanisms[0].linear.hasMoveDist);
    CHECK(eventsData->mechanisms[0].linear.moveDistLt == doctest::Approx(64.0f));
    REQUIRE(eventsData->mechanisms[0].linear.moveDirLt.size() == 3);
    CHECK(eventsData->mechanisms[0].linear.moveDirLt[0] == doctest::Approx(1.0f));
    CHECK(eventsData->mechanisms[0].rotation.hasRotationPoint);
    REQUIRE(eventsData->mechanisms[0].rotation.rotationPointLt.size() == 3);
    CHECK(eventsData->mechanisms[0].rotation.rotationPointLt[2] == doctest::Approx(1632.0f));
    CHECK(eventsData->mechanisms[0].rotation.hasRotationAngles);
    REQUIRE(eventsData->mechanisms[0].rotation.rotationAnglesDeg.size() == 3);
    CHECK(eventsData->mechanisms[0].rotation.rotationAnglesDeg[1] == doctest::Approx(90.0f));
    REQUIRE(eventsData->mechanisms[0].triggerOutputs.size() == 2);
    CHECK(eventsData->mechanisms[0].triggerOutputs[0].phase == "open");
    CHECK(eventsData->mechanisms[0].triggerOutputs[0].slot == 0);
    CHECK(eventsData->mechanisms[0].triggerOutputs[0].targetName == "DoorController");
    CHECK(eventsData->mechanisms[0].triggerOutputs[0].messageName == "unlock");
    CHECK(eventsData->mechanisms[0].triggerOutputs[0].resolution == "resolved");
    CHECK(eventsData->mechanisms[0].triggerOutputs[1].resolution == "unresolved");
    REQUIRE(eventsData->bindings.size() == 1);
    REQUIRE(eventsData->bindings[0].targets.size() == 1);
    CHECK(eventsData->bindings[0].targets[0].targetKind == "odm_bmodel");
    REQUIRE(eventsData->bindings[0].targets[0].bmodelIndex.has_value());
    CHECK(*eventsData->bindings[0].targets[0].bmodelIndex == 12);
    CHECK(eventsData->bindings[0].targets[0].bmodelName == "DoorA");
    CHECK(eventsData->bindings[0].targets[0].sourceModelName == "DoorA");
    REQUIRE(eventsData->bindings[0].targets[0].sourcePolygonGroup.has_value());
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->sourceModelIndex == 12);
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->sourceModelName == "DoorA");
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->sourcePolyCount == 8);
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->sourceSurfaceCount == 3);
    REQUIRE(eventsData->bindings[0].targets[0].sourcePolygonGroup->boundsMinLt.size() == 3);
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->boundsMinLt[0] == doctest::Approx(100.0f));
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->hasMovable);
    CHECK(eventsData->bindings[0].targets[0].sourcePolygonGroup->movable);
    REQUIRE(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint.size() == 1);
    CHECK(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].sourceModelIndex == 12);
    CHECK(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].sourceName == "DoorA");
    CHECK(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].movable);
    REQUIRE(
        eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].worldTranslationLt.size() == 3);
    CHECK(
        eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].worldTranslationLt[2]
        == doctest::Approx(1600.0f));
    CHECK(
        eventsData->bindings[0].targets[0].nearestMovableWorldModelsByRotationPoint[0].distanceLt
        == doctest::Approx(32.0f));
    REQUIRE(
        eventsData->bindings[0]
            .targets[0]
            .nearestMovableWorldModelsByRotationPoint[0]
            .claimedByExactBindings.size()
        == 1);
    CHECK(
        eventsData->bindings[0]
            .targets[0]
            .nearestMovableWorldModelsByRotationPoint[0]
            .claimedByExactBindings[0]
            .sourceObjectIndex
        == 6);
    CHECK(
        eventsData->bindings[0]
            .targets[0]
            .nearestMovableWorldModelsByRotationPoint[0]
            .claimedByExactBindings[0]
            .sourceName
        == "NearDoor");
    CHECK(
        eventsData->bindings[0]
            .targets[0]
            .nearestMovableWorldModelsByRotationPoint[0]
            .claimedByExactBindings[0]
            .confidence
        == "exact_source_model_name");
    REQUIRE(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByPosition.size() == 1);
    CHECK(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByPosition[0].sourceModelIndex == 14);
    CHECK(eventsData->bindings[0].targets[0].nearestMovableWorldModelsByPosition[0].distanceLt
        == doctest::Approx(16.0f));
    CHECK(eventsData->triggerCount == 1);
    CHECK(eventsData->interactionCount == 1);
    CHECK(eventsData->unresolvedCount == 1);
    REQUIRE(eventsData->unresolved.size() == 1);
    CHECK(eventsData->unresolved[0].kind == "unresolved_binding");
    CHECK(eventsData->unresolved[0].sourceObjectIndex == 9);
    CHECK(eventsData->unresolved[0].sourceName == "ScriptObject0");
    CHECK(eventsData->unresolved[0].sourceClass == "ScriptObject");
    CHECK(eventsData->unresolved[0].severity == "warning");
    REQUIRE(eventsData->unresolved[0].nearestMovableWorldModelsByPosition.size() == 1);
    CHECK(eventsData->unresolved[0].nearestMovableWorldModelsByPosition[0].sourceModelIndex == 14);
    CHECK(eventsData->unresolved[0].nearestMovableWorldModelsByPosition[0].sourceName == "DoorCandidate");
    CHECK(eventsData->unresolved[0].nearestMovableWorldModelsByPosition[0].distanceLt == doctest::Approx(16.0f));
    REQUIRE(eventsData->scripts.size() == 1);
    CHECK(eventsData->scripts[0].scriptId == "doorlock.scr");
    CHECK(eventsData->scripts[0].commandCount == 7);
    CHECK(eventsData->scripts[0].registeredTriggerCount == 1);
    REQUIRE(eventsData->scripts[0].registeredTriggers.size() == 1);
    CHECK(eventsData->scripts[0].registeredTriggers[0].line == 10);
    CHECK(eventsData->scripts[0].registeredTriggers[0].message == "use");
    CHECK(eventsData->scripts[0].registeredTriggers[0].callback == "OnUse");
    CHECK(eventsData->scripts[0].registeredTriggers[0].argumentsRaw == "\"use\", OnUse");
    REQUIRE(eventsData->scripts[0].triggerEdges.size() == 1);
    CHECK(eventsData->scripts[0].triggerEdges[0].line == 12);
    CHECK(eventsData->scripts[0].triggerEdges[0].targetExpression == "DoorA");
    CHECK(eventsData->scripts[0].triggerEdges[0].messageExpression == "close");
    CHECK(eventsData->scripts[0].triggerEdges[0].argumentsRaw == "DoorA, close");
    CHECK(eventsData->scripts[0].movementCommandCount == 1);
    REQUIRE(eventsData->scripts[0].movementCommands.size() == 1);
    CHECK(eventsData->scripts[0].movementCommands[0].line == 14);
    CHECK(eventsData->scripts[0].movementCommands[0].command == "MoveObject");
    CHECK(eventsData->scripts[0].movementCommands[0].argumentsRaw == "DoorA, 64");
    CHECK(eventsData->scripts[0].unknownCommandCount == 1);
    REQUIRE(eventsData->scripts[0].unknownCommands.size() == 1);
    CHECK(eventsData->scripts[0].unknownCommands[0].line == 11);
    CHECK(eventsData->scripts[0].unknownCommands[0].command == "CustomCommand");
    CHECK(eventsData->scripts[0].unknownCommands[0].argumentsRaw == "Something, 1");
}

TEST_CASE("MM9 events YAML loader rejects non-MM9 sidecars")
{
    OpenYAMM::Game::Mm9EventsYmlLoader loader = {};
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::Mm9EventsData> eventsData =
        loader.loadFromText(
            "format_version: 1\n"
            "kind: legacy_events\n"
            "source_raw_objects: test.raw_objects.yml\n"
            "objects: []\n",
            errorMessage);

    CHECK(!eventsData.has_value());
    CHECK(errorMessage == "kind must be mm9_events");
}
