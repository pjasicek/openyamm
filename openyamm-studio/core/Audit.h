#pragma once

#include "core/Coplanar.h"

#include "core/MapLoad.h"

#include <array>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace YAML
{
class Node;
}

namespace OpenYAMM::Studio
{
// core/Reachability.h
struct SolveResult;
// core/Project.h
struct Project;

struct AuditFinding
{
    // Stable name of the check: "event.unhandled", "event.unbound", "door.missing", "door.empty" ...
    std::string code;
    // "error": the map is broken for the player there. "warning": probably a mistake. "info": worth a look.
    std::string severity;
    std::string message;
    // How to fix it, in one sentence.
    std::string hint;
};

struct MapOverview
{
    size_t sectors = 0;
    size_t faces = 0;
    size_t bmodels = 0;
    size_t doors = 0;
    size_t actors = 0;
    size_t spawns = 0;
    size_t decorations = 0;
    size_t lights = 0;
    size_t chests = 0;
    // Loot containers of the scene file (the form new maps use for chests).
    size_t containers = 0;
    size_t handlers = 0;
    size_t boundEvents = 0;
};

MapOverview overviewOf(const LoadedMap &map);

// Checks of wiring (PLAN.md section 6, tier 1): what the map's faces and decorations call against what its script
// handles, and the doors its script moves against the doors the map has.
std::vector<AuditFinding> auditWiring(const LoadedMap &map);

// How many pairs of faces in one plane a map has, and of them how many its original has at the same place.
struct CoplanarSummary
{
    size_t pairs = 0;
    size_t asOriginal = 0;
    // The original the pairs were matched against; empty when there was none to match.
    std::string original;
};

// Faces in one plane over each other (core/Coplanar.h), as the map starts, with its moving parts a quarter, half and
// three quarters of their way along and at the other end: one "geometry.coplanar" finding for each pair. With the
// original's pairs (`pOriginalPlaces`, coplanarPlaces of the original map) a pair the original has at the same place
// is "info" and says so; the others are warnings, or with `strict` errors (`oymap audit --strict` fails on them).
// Outdoors the models' faces, all models together (`outdoorParts`: the part of each face, from the build's
// build.json, for the messages); `pOriginalPlaces` then from outdoorCoplanarPlaces. Outdoors also one
// "faces.back_to_back" finding for each pair of faces in one plane facing opposite ways (findOutdoorBackToBackFaces),
// a warning, or with `strict` an error.
std::vector<AuditFinding> auditCoplanarFaces(
    const LoadedMap &map,
    const std::vector<CoplanarPlace> *pOriginalPlaces,
    bool strict,
    CoplanarSummary &summary,
    const CoplanarNames &names = {},
    const OutdoorFaceParts &outdoorParts = {});

// Walkable tops where the party's eye lies in another sector's space than the game draws from (core/EyeSector.h): one
// "geometry.eye_sector" warning for each such floor face.
std::vector<AuditFinding> auditEyeSectors(const LoadedMap &map);

// Pictures squashed one way (core/Looks.h: texels per unit across and down more than 1.6 apart), by texture: one
// "texture.squashed" note (info) for each texture, with its worst face. And decorations standing in the air (more than
// 16 over the highest floor or top under them, not hanging kinds by their hint in `decorationTableText`, the asset
// root's decoration_data.txt): "thing.floating".
// `hanging`: the decorations (by entity number) a project says hang (`hangs: true`, or on a wall), which the built
// map cannot tell (XD-04's braziers on chains from a beam).
std::vector<AuditFinding> auditLooks(
    const LoadedMap &map, const std::string &decorationTableText, const std::set<int> &hanging = {});

// The props' dressing rules (devdocs/xeen/formats/DRESSING.md, measured on Warlord's Fortress and Castle Harmondale;
// numbers by decision D-7.1). Props are the decorations of the table that block movement, in three classes:
// containers (barrel, keg, cask, sack, bag, crate, box, bucket by their row's hint or name, standing on the floor),
// set pieces (any decoration with an event, and trees, statues, pillars, altars, hearths, fires, braziers, cauldrons,
// vats, fountains and the like) and the rest (furniture, rubble, bones, heaps). Errors: a container within 192 of a
// door face (beside it no further than 64 past its ends), "dressing.door"; a container within 320 in front of an open
// doorway (a portal a party wide and at most 512; its foot no further than 64 past the opening's ends) or within 192
// beside it along the wall, "dressing.doorway"; "dressing.walking_line" for a prop of radius 24 or more on the floor
// within its radius and 64 of the straight line between two openings of its sector (openings side by side count as
// one): an error for containers and the rest, a warning for set pieces; and an error for any such prop near the line
// (within its radius and 128) that leaves under 128 free on both of its sides across the line. Warnings: a container
// further than 240 from its sector's nearest wall (320 in a storeroom), "dressing.wall"; three or more containers each
// within 200 of another outside a storeroom, "dressing.clump". A storeroom is a sector with 8 or more containers, or
// one of `storerooms` (rooms with `store: true`). `hanging` as auditLooks.
// Outdoors the same classes by the houses (a house door is a model's faces whose event enters a house, side by side
// ones merged): "dressing.door", an error for a container within 320 in front of a house door or 192 beside it, and
// for any other prop of radius 24 or more on the floor that stands before the door within its radius and 128 (a
// warning for set pieces); "dressing.wall", a warning for a container within 512 of a model's wall but further than
// 240 from it; "dressing.walking_line" as indoors for the line from before one house door (64 out) to before another,
// at most 2048 apart with no wall between; "dressing.road", a prop of radius 24 or more standing on a road cell
// (`cellKinds`: core/OutdoorGround's outdoorCellKinds, 3 a road) further than its radius and 64 from a wall (an error,
// a warning for set pieces); "dressing.clump" for three or more containers together (no storerooms outdoors).
std::vector<AuditFinding> auditDressing(const LoadedMap &map, const std::string &decorationTableText,
    const std::set<int> &hanging = {}, const std::set<int> &storerooms = {},
    const std::vector<uint8_t> &cellKinds = {});

// What props and chests stand on, what the chests look like and what they stand in front of (families F3 and F6 of the
// user's play feedback, 2026-11-21; the checks of tools/xeen/check_props_support.py, with its numbers). Props are the
// blocking decorations of the table as for auditDressing, less plants, trees and natural rocks, in three classes:
// containers, set pieces (a set piece's row, or any decoration with an event) and the rest. The ground is the game's:
// outdoors the terrain's triangles (split north-west to south-east) and the models' tops, indoors the floors; what
// stands under a prop is the highest of them no more than 24 over its base. "support.floating", an error: nothing
// within 24 under the prop's middle, unless it stands over another decoration (within that one's radius, above its
// foot: a scene overlay's orb over its pedestal), which holds it. "support.overhang": part of its footprint (85 % of
// its radius) more than 24 over the ground; "support.edge": a drop of more than 64 within 48 of its footprint (a cliff,
// a terrace, a platform or a bridge side); errors, warnings for set pieces. Indoors only a gap deeper than furniture
// (128) counts for anything but a container, outdoors only an overhang over 48 and a drop over 96 (a hillside). A point
// behind a wall from the prop's middle, or with no floor under it, is no drop. Chests are things whose click opens one,
// or clicked things built mostly of chest pieces; their footprint is their faces' box, standing on its lowest corner,
// their own faces (indoors) or model (outdoors) not counted: "support.overhang" and "support.edge" errors as for
// containers. "chest.look", an error: a chest that is none of the shipped ones (MM7's or MM8's 18 or more faces with
// the a, b, c, e and g pieces of 7gt002 or gt002, only MM6's chest pieces ch1-ch5 and ch001-ch006, only crate pictures,
// a bookcase, or furniture by its title: a sarcophagus, a coffin, a cabinet, a desk). "chest.entrance", an error: a
// chest within 320 in front of (64 past the ends of) an opening outdoors, 192 indoors: a face entering a house,
// leaving, opening a door or teleporting, or a cave mouth's dark door face (outdoors 256 further); not a cupboard's own
// door (a dead-end sector too shallow to reach). "chest.title", a warning: a hover title that names a place (a den, a
// cave, a mine) and no container. `flowJson`: exploreEventHandlers' output, for what the things do. `hanging` as
// auditLooks.
std::vector<AuditFinding> auditPropSupport(const LoadedMap &map, const std::string &decorationTableText,
    const std::string &flowJson, const std::set<int> &hanging = {});

// The tables the light check reads: the decoration rows with the world's (decoration_data.txt), the model bindings
// (engine/models/indoor_decorations.yml and the world's) and the fixture list (engine/models/light_fixtures.yml and
// the world's models/light_fixtures.yml: `fixtures: {<decoration name>: ceiling|wall|floor|free|none}`).
struct LightFixtureData
{
    std::string decorationTableText;
    std::vector<std::string> bindingTexts;
    std::vector<std::string> fixtureTexts;
};

// Light fixtures where they belong (devdocs/xeen/formats/LIGHTS.md; the user, 2026-11-20). Each decoration that is a
// light fixture has a mount: the fixture list's word, else its binding's (a swinging model hangs from the ceiling,
// `mount: wall` is on a wall), else its row's hint (chandeliers hang; sconces and torches are on walls; braziers,
// candles, fires and beacons stand; glows float free). Indoors only. Errors: "lights.in_solid" (its middle behind
// the faces round it), "lights.ceiling_on_floor" (a hung fixture standing on the floor with no ceiling within reach
// of its top), "lights.ceiling_gap" (its top under no ceiling or far under it; a warning when near), "lights.in_doorway"
// (a hung fixture whose foot is low in an opening, a wall fixture inside an opening, a standing one in it),
// "lights.wall_missing" (no wall within 64 of a wall fixture's middle: the game stands it in the air),
// "lights.on_moving_face" (its wall is a door's), "lights.floating" (a standing fixture over the floor),
// "lights.light_in_solid" (a map light, or a decoration's light at its middle, more than 32 inside the rock; 16 to
// 32: a warning). Warnings: "lights.wall_height" (a wall fixture's foot under 16 over the floor), "lights.sunk".
// "lights.unclassified" (info) names the decorations that
// give light with no mount. `hanging`: the decorations a project says hang (they are not standing fixtures).
// `measure`: one "lights.measure" info line per fixture and light with its numbers (the calibration).
std::vector<AuditFinding> auditLightFixtures(
    const LoadedMap &map, const LightFixtureData &data, const std::set<int> &hanging = {}, bool measure = false);

// What the texture checks read: the logical size (texels) of each texture by lower-case name, as the game resolves
// it, and the texts of texture_classes.yml (assets_dev/engine/models/, then the world's models/; written by
// tools/xeen/texture_classes.py: each texture's class, door role, mirror likeness, border colour and material).
struct TextureFitData
{
    std::map<std::string, std::array<int, 2>> sizes;
    std::vector<std::string> classTexts;
};

// Door leaves and their pictures (devdocs/xeen/formats/DOORS.md; the user, 2026-11-20: "double-winged doors
// displaying just as single winged or tiling the single wings across a big would-be double-winged door"). Indoors
// every door record's front, outdoors every model face with a door picture. Errors: "doors.tiled" (a door picture
// shown more than 1.3 times across its leaf), "doors.half_wing" (one wing of a double door on a single leaf 192 or
// more wide), "doors.wing_unmirrored" (both leaves of a pair showing one wing the same way round). `measure`: one
// "doors.measure" info line per leaf with its numbers (the calibration).
std::vector<AuditFinding> auditDoorTextures(const LoadedMap &map, const TextureFitData &data, bool measure = false);

// Pictures that do not fit their faces (devdocs/xeen/formats/TEXTURE_FIT.md; the user, 2026-11-20: "tiling of stuff
// which doesn't fit"), judged on surfaces: the touching faces of one texture in one plane whose pictures continue each
// other. Errors: "textures.feature_repeated" (a picture meant once shown more than 1.3 times across or down),
// "textures.feature_cut" (no unbroken 60 % of it shown on a surface 48 or more that way), "textures.trim_tiled" (a
// band repeated up its face, a strip across). Warnings: "textures.tile_seams" (a texture whose edges do not meet
// repeated twice or more that way), "textures.feature_border" (a picture set into a wall tile whose border colour is
// unlike the wall's), "textures.family_switch" (two unlike wall tiles side by side in one plane). Door pictures are
// the door check's. `measure`: one "textures.measure" info line per surface with its picture's copies across and down
// and one per pair of neighbouring surfaces (the calibration).
std::vector<AuditFinding> auditTextureFit(const LoadedMap &map, const TextureFitData &data, bool measure = false);

// What a project says of its built map that the map itself cannot: its decorations that hang (`hangs: true` or on a
// wall, by entity number) and its storerooms (rooms with `store: true`, by sector number), from the project's
// objects.yml, rooms.yml and ids.lock.yml. `oymap install` writes them into the map's <stem>.studio.yml
// (`hanging_decorations`, `storerooms`), from which the audit of an installed map reads them back.
struct DressingFacts
{
    std::set<int> hanging;
    std::set<int> storerooms;
    // The door numbers of lifts that are trapdoors (objects.yml lifts[].trap): no rides, so no switch is meant.
    std::set<int> traps;
    // project.yml `identity.shape` (D-89: cave, mine, tower, temple, castle, sewer, ship, hall), empty when not said.
    std::string identityShape;
    // The sketch's cave mouths that show a dark way in leading nowhere: no `into` and no `form` (shelter, blocked;
    // D-91), by id.
    std::vector<std::string> blindMouths;
};

DressingFacts projectDressingFacts(const Project &built);
DressingFacts studioFileDressingFacts(const YAML::Node &studioFile);

// Questions the player is asked (evt.AskQuestion) whose answer he must know: for each answer that is no yes or no,
// the handlers whose texts (messages, signs, status lines) hold it, each with its hover name and the step of
// `solveMap` (`flowJson`, core/EventFlow) at which the party first reaches it, against the question's own step (the
// user's walk through XD-04: a door asking for a word given only by a cage nobody would click). "question.answer"
// warnings where no text gives the answer, where only a thing without a hover name gives it, or only later in the
// order; an "info" note listing where each answer is given. `pSolved`: the solve of the same map and flow when the
// caller has it already (check.audit with `solve`), so it is not walked twice; a map that asks nothing is not solved.
std::vector<AuditFinding> auditQuestions(
    const LoadedMap &map, const std::string &flowJson, const SolveResult *pSolved = nullptr);

// Clicked things (faces and decorations with an event) that on some branch of their handler do nothing the player
// sees: no text, window, door or part moving, item, chest, light, picture or teleport (the user's second walk through
// XD-04: a hoist's call button held by its brake). One "click.silent" note (info) for each such branch, with the tests
// that lead to it (`flowJson`: core/EventFlow).
std::vector<AuditFinding> auditSilentClicks(const LoadedMap &map, const std::string &flowJson);

// Moves into a dungeon and their entrance windows (feedback F16, 2026-11-22: the standard MM6-MM8 window, never a
// scene's own Yes/No): "entrance.no_window" (warning) for an evt.MoveToMap into another .blv with neither a text nor a
// picture and no `{direct = true}` (the studio writes that for `screen: none`), "entrance.question" (error) for a
// handler that asks Yes or No (evt.AskQuestion, AskChoiceWithAnswerSteps) and moves into a .blv: the window asks.
std::vector<AuditFinding> auditEntranceWindows(const LoadedMap &map);

// A map whose identity is a cave or a mine (`identity: {shape: cave}`, D-89) held to the cave-shape targets
// (core/Metrics caveShapeOf, caveShapeTargets): one "identity.cave_shape" warning for each number below its target.
std::vector<AuditFinding> auditCaveShape(const LoadedMap &map, const std::string &identityShape);

// The void (U-12; the scene's terrain.void): nothing but decorations and waterfalls may stand on a void cell. An
// actor, an encounter, an item lying there or a building over it is an error ("void.occupied").
std::vector<AuditFinding> auditVoid(const LoadedMap &map);

// D-91: no dark mouth leads nowhere. One "caves.blind_mouth" error for each cave mouth of the project (its
// `blindMouths`, from the project or the installed map's <stem>.studio.yml `blind_mouths`) with no `into` that is no
// `form: shelter` or `form: blocked`.
std::vector<AuditFinding> auditBlindMouths(const std::vector<std::string> &blindMouths);

// D-99: the chests (faces of a chest kind's pictures, indoors or on the models outdoors) against the walls (upright
// faces higher than the chest) and ways round them. "chest.facing" (error) for a chest whose front faces a wall within 64, that stands end-on to the wall it
// stands by with its back to the room, or (indoors) stands free with its back to the doorway its room is entered by
// from the party's start; "chest.placement" (error) for one within a party's width and a margin of a doorway, a door
// or a house door, or on the walking line between two ways of its sector (core/ChestKinds.h).
std::vector<AuditFinding> auditChests(const LoadedMap &map);

// Moving parts that carry the party (a door record with a level top 64 or more across: a car, a cage, a lift) and are
// worked by clicked things, at each end of their way: is one of those things (other than the part's own faces) in
// reach of a rider on the deck there, within the game's 512 of his eye and facing him? (The user's walk through
// XD-02: "How am I supposed to press that lever while being on the moving platform?" Every car lever stood behind its
// gate's wall.) A ride is a part that carries the party as the game does (up and down, or a slide whose mover says
// so), travels 64 or more with its whole top and stops level with a floor beside it at both ends; a clicked thing
// counts when nothing drawn stands between the rider's eye and it. One "ride.no_switch" warning for each part with an
// end where none is, also where the part's own faces run its event (it works, but nothing tells a rider to click
// the car); a part moved only by its own faces, steps or timers is not judged, nor a trapdoor (`traps`: the door
// numbers of objects.yml lifts with `trap: true`). `names`: a project's lock names.
std::vector<AuditFinding> auditRides(const LoadedMap &map, const std::string &flowJson,
    const CoplanarNames &names = {}, const std::set<int> &traps = {});
}
