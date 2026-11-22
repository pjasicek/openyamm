#pragma once

#include "core/GlbWriter.h"
#include "core/HeightMesh.h"
#include "core/MonsterRelations.h"
#include "core/Project.h"

#include "core/compile/IndoorGeometryMetadata.h"

#include <array>
#include <filesystem>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The engine numbers behind a project's stable ids (ids.lock.yml, PLAN.md section 4). Numbers already in the lock are
// kept; new ids take the lowest free number.
struct IdsLock
{
    std::map<std::string, int> sectors;
    std::map<std::string, int> events;
    std::map<std::string, int> doors;
    std::map<std::string, int> containers;
    std::map<std::string, int> cogs;
    std::map<std::string, int> mapVars;
    // Lights that an event switches (wiring `lights_on`, `lights_off`) or that start dark (`on: false`): the
    // number `evt.SetLight` names each by (the BLV light's id), from 1.
    std::map<std::string, int> lights;
    // Placed ambient sounds (objects.yml `sounds`): the scene's key of each, from 1 (a script switches a sound by
    // the map variable `AmbientSound<key>`).
    std::map<std::string, int> sounds;
    // Decorations by their number in the built map (the BLV entity index `evt.SetSprite` takes): written anew by
    // each build in the order of objects.yml `decorations`, so a Lua text can look a number up (the wiring effect
    // `set_sprite` needs none).
    std::map<std::string, int> decorations;
    // The scene's destructibles: the id `evt.DestroyDestructible` takes (S6). An overlay project's base ones are the
    // base map's own (`destructible:k<id>`).
    std::map<std::string, int> destructibles;
    // An overlay project's base water volumes, by their place in the base scene's list, and base spawn points, by
    // their index in the base map (S6, `oymap import`).
    std::map<std::string, int> water;
    std::map<std::string, int> spawns;
    // An overlay project's base ladders, by their place in the base scene's list (`ladder:<name>`), and the base map's
    // cinematics, by their place in its cinematics file (`cinematic:<name>`; S8a, `oymap import`).
    std::map<std::string, int> ladders;
    std::map<std::string, int> cinematics;

    static IdsLock fromDocument(const YAML::Node &document);
    YAML::Node toDocument() const;
    // The id's number in `table`, allocating the lowest free one from `first` upward when it has none.
    static int number(std::map<std::string, int> &table, const std::string &id, int first);
};

// The entries of an indoor project's lock whose ids the project no longer has ("events: evt:gone 3"), by the rule of
// what is live (core/IndoorLowering.cpp). Builds keep them, so a number once given stays through undo; `drop` removes
// them from `lock` (`oymap lock prune`).
std::vector<std::string> retiredLockEntries(const Project &project, IdsLock &lock, bool drop);

struct LoweredSurface
{
    std::string texture;
    int width = 128;
    int height = 128;
    double scale = 1.0;
    bool fit = false;
    // Texels added to every corner's texture coordinates (`offset: [u, v]`), as a shipped map's face delta moves its
    // picture: the texture is laid as without it and then shifted by u to one side and v down.
    double offsetU = 0.0;
    double offsetV = 0.0;
    // `uneven: true`: the picture is meant squashed or far from its own size where it lies (no warning).
    bool uneven = false;
    // Engine face attribute bits of every face laid with this surface: `liquid` (the fluid bit, and lava's burning
    // bit) and `flow` (the picture flows one way), as the shipped maps' water, slime and lava faces carry them.
    uint32_t faceBits = 0;
    // `translucent`: every face laid with it goes into the scene's `translucent_faces`.
    std::optional<GlbFaceTranslucency> translucency;
};

// The textures the game draws as liquids on faces (engine/liquids/liquids.yml, those of every world and of
// `world`): by name and by the start of the name, lower case.
struct LiquidTextures
{
    std::set<std::string> names;
    std::vector<std::string> prefixes;

    bool matches(const std::string &texture) const;
};

// Empty when the table cannot be read.
LiquidTextures readLiquidTextures(const std::string &tableText, const std::string &world);

// A part of an uneven floor or ceiling (`floor_surfaces`, `ceiling_surfaces` entry) as an object: its `id`, and
// `secret: true` (its faces carry the engine's secret flag).
struct LoweredMeshPart
{
    std::string id;
    bool secret = false;
};

// A panel on a wall: a rectangle of the wall with a surface of its own, cut into the wall's faces.
struct LoweredWallPanel
{
    // The outline edge of the wall, and the panel's stretch along it (distance from the edge's first corner).
    size_t edge = 0;
    double low = 0.0;
    double high = 0.0;
    // Absolute heights; without a value the panel begins at the wall's foot or ends at its top.
    std::optional<double> bottom;
    std::optional<double> top;
    LoweredSurface surface;
    // Where the project says it, for messages.
    std::string path;
    // Its `id`, when it has one: what a click event names as its source.
    std::string id;
    // `cover: true`: the panel hangs 2 in front of a wall built whole behind it (a hide, a tapestry, a board), so a
    // destructible of it burns away to the wall.
    bool cover = false;
};

// A point of a climbing path room's centre line: the two outline corners across it and the heights there.
struct LoweredClimbStation
{
    std::array<double, 2> right = {};
    std::array<double, 2> left = {};
    double floor = 0.0;
    double ceiling = 0.0;
    // How the stretch from this station to the next is cut into two triangles: by the line from this station's
    // right corner to the next one's left corner, or the other way.
    bool diagonalFromRight = true;
};

struct LoweredRoom
{
    std::string id;
    // The id without its "room:" prefix: the ROOM_ node's suffix.
    std::string name;
    std::vector<std::array<double, 2>> outline;
    double floor = 0.0;
    double ceiling = 0.0;
    int ambient = 0;
    LoweredSurface wall;
    LoweredSurface floorSurface;
    LoweredSurface ceilingSurface;
    LoweredSurface reveal;
    LoweredSurface door;
    int sector = 0;
    // A floor that rises or falls: from `floor` at the side away from the wall `towardEdge` to `floorTo` at that
    // wall. `steps` 0 is a ramp; otherwise that many steps, the last riser standing in the wall itself (the
    // doorway there starts at `floorTo`).
    bool sloped = false;
    double floorTo = 0.0;
    size_t towardEdge = 0;
    int steps = 0;
    // Bands of the walls, from the floor up: each reaches `first` above the floor and has its own surface; above the
    // last band the wall has its own surface.
    std::vector<std::pair<double, LoweredSurface>> wallBands;
    // Parts of the floor that stand at another height (levels, platforms, the treads of a flight): outline and
    // height. Objects stand on them; the last one that holds a point decides.
    std::vector<std::pair<std::vector<std::array<double, 2>>, double>> floorRegions;
    // Rough walls (a cave): solid stretches are broken every `roughStep` units and their joints pushed up to
    // `roughDepth` into the room. 0: flat walls.
    double roughStep = 0.0;
    double roughDepth = 0.0;
    // The surface of the risers of a stepped floor; the wall's when not given.
    std::optional<LoweredSurface> riser;
    // Surfaces of single walls (by outline edge) that differ from the theme's: above the room's bands, if any.
    std::map<size_t, LoweredSurface> wallSurfaces;
    // Walls (by outline edge) that take none of the room's bands (`walls[].bands: false`, S8g): their surface runs
    // from the floor to the ceiling.
    std::set<size_t> wallsWithoutBands;
    // A ceiling that is one sloping plane: from `ceiling` at the side away from the wall `ceilingTowardEdge` to
    // `ceilingTo` at that wall. The walls' tops rake with it.
    bool ceilingSloped = false;
    double ceilingTo = 0.0;
    size_t ceilingTowardEdge = 0;
    // Panels of the walls (`walls[].panels`, `ends`), in the order they were read.
    std::vector<LoweredWallPanel> wallPanels;
    // A `path` room that climbs: one station for each point of its centre line, floor and ceiling level across the
    // room at each and running straight between them. `sloped` and `ceilingSloped` are then set too (walls rake),
    // `floorTo` is the floor at the last station, and `towardEdge` and `ceilingTowardEdge` are not used.
    std::vector<LoweredClimbStation> climb;
    // An uneven floor (`floor_points`, `floor_plane`): flat triangles between points with heights, over the whole
    // outline. `sloped` is then set too (walls follow the floor); `floor` stays the height the room's other parts
    // are measured from, and `floorTo`, `towardEdge` and `steps` are not used.
    HeightMesh floorMesh;
    // Parts of an uneven floor or ceiling with a surface of their own (`floor_surfaces`, `ceiling_surfaces`): the
    // surfaces, and for each triangle of the mesh the place of its surface among them (-1: the room's own).
    std::vector<LoweredSurface> floorMeshSurfaces;
    std::vector<int> floorTriangleSurfaces;
    std::vector<LoweredSurface> ceilingMeshSurfaces;
    std::vector<int> ceilingTriangleSurfaces;
    // Beside each of those surfaces: the part's `id` (what an effect names its faces by) and whether its faces carry
    // the engine's secret flag (`secret`). A part with either is a node of its own.
    std::vector<LoweredMeshPart> floorMeshParts;
    std::vector<LoweredMeshPart> ceilingMeshParts;
    // The same for the ceiling (`ceiling_points`, `ceiling_plane`); `ceilingSloped` is then set too.
    HeightMesh ceilingMesh;
    // `steep_floor: true`: floors of this room too steep to walk (rock banks) are meant, not refused.
    bool steepFloor = false;
    // Sloping floors standing in the room beside its own: the banks of levels and the sloping tops of blocks, as
    // triangles of [x, y, height]. What stands over one stands on it.
    std::vector<std::array<std::array<double, 3>, 3>> floorFacets;
    // Surfaces of small parts: the treads of a stepped floor (default: the floor's).
    std::optional<LoweredSurface> tread;
    // A `path` room with a `section` (a tunnel): the cross-section as points [across, up], counter-clockwise with
    // `across` to the right of the way and `up` upward, the first side being the flat floor; one surface for each side (side i runs
    // from point i to the next); and the section's points in the map at each point of the path (`sectionRings`,
    // on whole units). `outline` is then the plan of the section's widest part, and the room has no walls, floor
    // or ceiling of the usual kind: its faces run from ring to ring.
    std::vector<std::array<double, 2>> section;
    std::vector<LoweredSurface> sectionSurfaces;
    std::vector<std::vector<std::array<double, 3>>> sectionRings;
    // A tunnel's end that is a plain upright rectangle instead of the section (`section.start`, `section.end`): its
    // width at the path's first and at its last point; 0: the section's own shape there. The ring at such an end
    // holds the rectangle's corners, each as often as section points run to it, and a point of the section that
    // runs to two corners (the single widest point of a side) stands twice in `section`.
    std::array<double, 2> sectionSquare = {0.0, 0.0};
};

// An opening resolved against its two rooms: which walls it joins and where.
struct LoweredOpening
{
    std::string id;
    std::string name;
    size_t fromRoom = 0;
    size_t toRoom = 0;
    size_t fromEdge = 0;
    size_t toEdge = 0;
    // The hole's interval along each wall (distance from the edge's first corner).
    double fromLow = 0.0;
    double fromHigh = 0.0;
    double toLow = 0.0;
    double toHigh = 0.0;
    double bottom = 0.0;
    double top = 0.0;
    // A pointed (gabled) opening: the height of its point, above `top` (where its sides end). Equal to `top` for a
    // rectangular opening.
    double apex = 0.0;
    // A pointed arch with shoulders (steep from the sides, then shallower to the point) instead of a plain gable.
    bool arched = false;
    // The arch's shoulders, from a side toward the point: each is how far in from the side (a share of the width)
    // and how far up from the sides' end toward the point (a share of that rise). Empty: one shoulder a quarter in
    // and two thirds up.
    std::vector<std::array<double, 2>> shoulders;
    // Wall thickness between the two rooms (for an opening in a floor: the floor's thickness).
    double depth = 0.0;
    // An opening in the floor of the `from` room onto the `to` room below it: a hole with this outline
    // (counter-clockwise) from `top` (the upper floor) down to `bottom` (the lower ceiling). The wall fields above
    // are not used. `wholeCeiling`: the hole is the lower room's whole ceiling (a stairwell or shaft open above).
    bool inFloor = false;
    bool wholeCeiling = false;
    std::vector<std::array<double, 2>> outline;
    // The surface of the doorway's floor through the wall's thickness; without one, the doorway's reveal.
    std::optional<LoweredSurface> threshold;
    // The doorway's top through the wall (`lintel`), its undersides under a gable or an arch; default the reveal.
    std::optional<LoweredSurface> lintel;
    // The surface of the doorway's sides and top through the wall's thickness (`reveal`; default the owning room's
    // theme reveal), and of the half of them toward the `to` room, beyond the middle of the wall where a door's leaf
    // stands (`back_reveal`; without it the whole way through is `reveal`).
    LoweredSurface reveal;
    std::optional<LoweredSurface> backReveal;
    // An opening shaped like the section of the tunnel that ends in it (`shape: section`): the hole's corners in
    // the `from` wall's own plane (place along the wall, height), counter-clockwise seen from inside the `from`
    // room. `fromLow` to `fromHigh` and `bottom` to `top` are then its extent.
    std::vector<std::array<double, 2>> section;
    // A mouth that follows uneven floors or roofs is built as strips side by side, each an opening with a `section`
    // of its own: for each side of that outline, whether the next strip of the same mouth begins there (no reveal is
    // built on such a side).
    std::vector<bool> sectionJoints;
    // Such a mouth through a wall with thickness: whether its sill is an uneven floor running on (and takes that
    // floor's surface) and whether its top is a roof given by points running on (`height: full`: that roof's
    // surface). Otherwise the way through takes the reveal's surface there, as a plain doorway's does.
    bool followsFloor = false;
    bool followsRoof = false;
};

struct LoweredDoor
{
    std::string id;
    std::string name;
    size_t opening = 0;
    int doorId = 0;
    // 0 when no wiring event uses the door.
    int eventId = 0;
    // Events bound to one side each (wiring `side`): `eventId` is then the event of the leaf's faces toward the
    // opening's `from` room (its edges too) and `backEventId` that of the faces toward its `to` room; 0 on a side
    // leaves that side unclickable.
    bool sided = false;
    int backEventId = 0;
    // The cog number of its leaves' faces when an effect changes them (set_texture, passable, solid, show, hide).
    int cog = 0;
    // A hinged leaf: it turns about a vertical line at one side of the doorway instead of sliding.
    bool hinged = false;
    std::array<double, 3> pivot = {};
    double openDegrees = 90.0;
    // Degrees per second.
    double turnSpeed = 60.0;
    // Seconds after which an opened leaf closes by itself; 0: it stays open.
    double autoCloseSeconds = 0.0;
    // A door of two leaves (`leaves: 2`): the second leaf's door number; events move both. 0: one leaf.
    int secondDoorId = 0;
    // A hinged pair (`kind: hinged, leaves: 2`): the second (right) leaf's hinge line and swing; `pivot` and
    // `openDegrees` are the first (left) leaf's.
    std::array<double, 3> secondPivot = {};
    double secondOpenDegrees = 90.0;
    // `fold: true`: of each leaf only the free edge moves (the corners farthest in the closing direction), and the
    // leaf shrinks against its jamb.
    bool fold = false;
    // A trapdoor: a hinged leaf lying in a hole of a floor (an opening `in: floor`), turning about a level hinge line
    // along one side of the hole (`axis`, a unit vector; positive `openDegrees` turn it right-handed about it), down
    // into the room below or up into the room above, the same way whoever opens it.
    bool hatch = false;
    std::array<double, 3> axis = {0.0, 0.0, 1.0};
};

// A lift: a block of floor that an event raises and lowers. To the engine it is a door whose faces are walked on.
struct LoweredLift
{
    std::string id;
    std::string name;
    int doorId = 0;
    int eventId = 0;
    // A mover of objects.yml (`movers`): a block that travels along a line, also a door to the engine.
    bool mover = false;
    // Mover: seconds after which it returns from its end to its start by itself; 0: it stays.
    double autoReturnSeconds = 0.0;
    // Mover: only the end face in the direction of travel moves, so the block grows and shrinks.
    bool stretch = false;
    // Mover with `turn`: it turns about a line instead of travelling (the engine's rotating mover): a point of the
    // line (absolute), its unit axis, the signed angle from start to end (right-handed about the axis) and the
    // speed in degrees per second.
    bool turning = false;
    std::array<double, 3> pivot = {};
    std::array<double, 3> axis = {};
    double degrees = 0.0;
    double turnSpeed = 90.0;
};

struct LoweredChest
{
    std::string id;
    std::string name;
    std::array<double, 3> position = {};
    int containerId = 0;
    int eventId = 0;
    int treasureLevel = 1;
    int randomItems = 3;
    int gold = 0;
    int trapLevel = 0;
    std::vector<int> items;
    // One more roll for each of these treasure levels (`random_levels`). A chest that has any is written as the
    // game's own chest record (the scene's `initial_state.chests`) instead of a loot container.
    std::vector<int> randomLevels;
};

// A monster of objects.yml `monsters`: one actor of the scene's starting state, standing at its place.
struct LoweredMonster
{
    std::string id;
    std::string name;
    // Its row of monster_data.txt and monster_descriptors.txt, and what those rows give it.
    int monsterId = 0;
    // The row's experience (column EXP): the shipped MM6-MM8 actor records hold it in the field the scene calls
    // `monster_id` (the game reads the kind from `monster_info_id`).
    int experience = 0;
    // An item it carries (`carries`): dropped with it or left in its corpse (the record's carried item).
    int carriedItemId = 0;
    int hitPoints = 0;
    int radius = 0;
    int height = 0;
    int moveSpeed = 0;
    std::array<double, 3> position = {};
    // The facing in the engine's units (2048 to the full turn, 0 east, counter-clockwise).
    int yawUnits = 0;
    // The actor's attribute bits: 0x80000 for one that is hostile whatever the monster table says, 0x10000 for one
    // that starts invisible (`hidden`).
    uint32_t attributes = 0;
    int group = 0;
    int sector = 0;
    // Keeps its place (the scene's `immobile`): it neither wanders nor walks after anyone.
    bool immobile = false;
    // Its home radius (`leash`, the scene's leash_radius): it holds its place and fights within this distance of it;
    // 0 for none.
    int leash = 0;
    // Its own name (`name`): the record's name, which the game shows on its corpse, and the row of the engine's
    // place_mon.txt that bears it, which the game shows while it lives (0: no such row).
    std::string displayName;
    int uniqueNameIndex = 0;
    // `npc`: the row of the world's npc table it is (the scene's npc_id): clicked while peaceful, it talks as that NPC.
    int npc = 0;
};

// An item of objects.yml `items`: one sprite object of the scene's starting state, lying on the floor.
struct LoweredItem
{
    std::string id;
    std::string name;
    int itemId = 0;
    // The row of object_list.txt that draws it (by the item's sprite index) and that row's sprite number.
    int objectDescriptionId = 0;
    int spriteId = 0;
    std::array<double, 3> position = {};
    int sector = 0;
    // A heap of gold (an item whose Equip Stat is Gold): the amount the party picks up (`gold`), which the game reads
    // from the item record's fourth word.
    int gold = 0;
};

struct LoweredEvent
{
    int eventId = 0;
    // The handler takes the step it is continued at (`continueStep`): an event that asks a question, which the game
    // runs again with the step of the answer.
    bool continues = false;
    std::string id;
    std::string title;
    // Lua statements of the handler body, one per line, without indentation.
    std::vector<std::string> body;
    // For a chest event: the container it opens.
    std::optional<int> opensContainer;
    // What runs the handler: "click" (a face the player uses), "step" (floor faces the party walks onto), "timer"
    // (the map's clock, every `everySeconds` seconds) or "load" (entering the map). Timer and load events are bound
    // to no face.
    std::string trigger = "click";
    int everySeconds = 0;
    // trigger "monster_damage" (the map's MonsterDamage hook, run before each hit on a monster lands): the monster ids
    // (monster_data rows) it acts on; empty: every monster.
    std::vector<int> hookMonsters;
    // ... and the placed monsters (objects.yml `monsters` ids, by their actor index in the scene) it acts on.
    std::vector<int> hookActors;
};

// A ladder of objects.yml `ladders`: the scene's climbable strip (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md).
struct LoweredLadder
{
    std::string name;
    std::array<double, 3> bottom = {};
    std::array<double, 3> top = {};
    double facingDegrees = 0.0;
    double width = 96.0;
    double reach = 48.0;
    std::array<double, 3> topExit = {};
    bool grabAtTop = true;
    // A body in the air takes hold too (S6: MM9's climbing poles).
    bool grabInAir = false;
};

// A light of objects.yml with `pulse`: the scene's pulsing light (devdocs/INDOOR_PULSING_LIGHTS.md) instead of a
// light record of the map.
struct LoweredPulsingLight
{
    int key = 0;
    std::array<double, 3> position = {};
    std::array<int, 3> color = {255, 255, 255};
    // Lowest, highest, cycles per second, phase in cycles.
    std::array<double, 4> intensity = {0.3, 1.0, 1.0, 0.0};
    std::array<double, 4> radius = {512.0, 512.0, 1.0, 0.0};
    bool startOn = true;
};

// A sound of objects.yml `sounds`: the scene's placed ambient sound (devdocs/AMBIENT_SOUNDS.md).
// The sound names a placed sound may give for a world (the game's audio folders of the world and the engine, in the
// asset root and the mount; lower case, with and without `.wav`); empty when none is there.
std::set<std::string> knownWorldSoundNames(
    const std::filesystem::path &assetRoot, const std::filesystem::path &mountRoot, const std::string &world);

struct LoweredAmbientSound
{
    int key = 0;
    std::string sound;
    std::array<double, 3> position = {};
    double innerRadius = 0.0;
    double outerRadius = 0.0;
    double volume = 1.0;
    bool loop = true;
    std::optional<std::array<double, 2>> wait;
    bool startOn = true;
    // Heard only by day, or only by night (the world's day hours; S6).
    bool dayOnly = false;
    bool nightOnly = false;
    // false: heard centred, with its falloff (D-48).
    bool pan = true;
};

// objects.yml `destructibles` (S6): the scene's destructible entries. The faces of a cog, or a decoration whose
// sprite key (its BLV entity's first event field) is the decoration cog; the centre is found from them in the build.
struct LoweredDestructible
{
    std::string id;
    int number = 0;
    int cog = 0;
    int decorationCog = 0;
    int hp = 1;
    bool damage = true;
    bool triggerOnly = false;
    std::string material;
    std::string sound;
    double effectScale = 1.0;
    int destroyedEvent = 0;
    int damagedEvent = 0;
};

// objects.yml `water` (S6): one of the scene's water volumes, one upright prism.
struct LoweredWater
{
    std::string id;
    std::string liquid = "water";
    std::vector<std::array<double, 2>> outline;
    double bottom = 0.0;
    double top = 0.0;
    std::optional<std::array<double, 3>> tint;
    std::optional<std::array<double, 3>> current;
    // The view's fog while the eye is inside: the scene's `fog` block of a water volume, as given (checked by the
    // game's parser); undefined for the map's own fog.
    YAML::Node fog;
};

// A thing the build places as a marker (a decoration, a light, a spawn point), by its project id: where it stands,
// for the studio's view (view.layout). Switches and exits too: the middle of their face (on a wall, a block's side or
// a block's top), with the way the face looks.
struct LoweredPlaced
{
    std::string id;
    // decoration, light, spawn, switch, exit.
    std::string kind;
    // A decoration's name in decoration_data.txt; a switch's kind (plate, lever, button).
    std::string name;
    std::array<double, 3> position = {};
    // A switch's or an exit's face: degrees counter-clockwise from east of the way it looks (into the room); none
    // for a plate on a block's top.
    std::optional<int> facing;
};

struct LoweredStart
{
    std::array<double, 3> position = {};
    int directionDegrees = 0;
};

// objects.yml `arena` (XD-20): the scene's `arena` block as MM7's 7d05 carries it (its opponents' monster ids, where
// the party stands, where each opponent appears), and the map's runtime restrictions of an arena.
struct LoweredArena
{
    int minimumMonsterId = 0;
    int maximumMonsterId = 0;
    LoweredStart party;
    std::vector<std::array<double, 3>> marks;
};

// Everything the build needs from a project, derived and checked: the mesh for the indoor compiler, its metadata, and
// what goes into the scene file and the Lua.
struct LoweredIndoorMap
{
    std::string mapStem;
    std::vector<LoweredRoom> rooms;
    std::vector<LoweredOpening> openings;
    std::vector<LoweredDoor> doors;
    std::vector<LoweredLift> lifts;
    std::vector<LoweredChest> chests;
    std::vector<LoweredMonster> monsters;
    std::vector<LoweredItem> items;
    std::vector<LoweredEvent> events;
    std::optional<LoweredStart> start;
    // Where a party arrives by each plan entrance of kind arrival or both (D-4), by entrance id: objects.yml
    // `arrivals`, else the start where its room realises the entrance's space, else the middle of such a room.
    std::vector<std::pair<std::string, LoweredStart>> arrivals;
    std::optional<LoweredArena> arena;
    std::vector<GlbNode> nodes;
    Editor::EditorIndoorGeometryMetadata metadata;
    IdsLock ids;
    // Placeholders of objects.yml, as "<id>: <what it stands for>": not built, reported by the build.
    std::vector<std::string> placeholders;
    // Things that build but will not look right, for the build to report.
    std::vector<std::string> warnings;
    // The numbers (BLV light ids) of the lights that start dark (objects.yml lights[].on: false).
    std::vector<int> darkLights;
    // What goes into the scene file beside the map: ladders, pulsing lights and placed sounds.
    std::vector<LoweredLadder> ladders;
    std::vector<LoweredPulsingLight> pulsingLights;
    std::vector<LoweredAmbientSound> ambientSounds;
    std::vector<LoweredDestructible> destructibles;
    std::vector<LoweredWater> water;
    // Decorations, lights and spawn points as placed (their markers' places), for the view.
    std::vector<LoweredPlaced> placed;
    int sceneCeiling = 1024;
    // An event runs when walked into (wiring `touch: true`): the scene's `party_movement: {touch_faces: run}`.
    bool touchFaces = false;
    int fogWeakDistance = 4096;
    int fogStrongDistance = 8192;
    // The actor number of the first of `monsters`: 0 for a new map. An overlay project's monsters (objects.yml
    // scene.monsters, S8a) stand after the base scene's actors and those of the scene overlays applied before its own,
    // whose numbers the game keeps (LoweringOptions::overlayFirstActor).
    size_t firstActor = 0;
    // Lowered by lowerOverlayProject: the wiring may name the base map's events and cinematics by their lock ids.
    bool overlay = false;
};

struct LoweringTables;

struct LoweringOptions
{
    // The asset root's engine/data_tables/decoration_data.txt contents, to resolve decoration names; empty when no
    // asset root is known (a project with decorations then fails with an issue saying so).
    std::string decorationTableText;
    // The same folder's monster_data.txt and monster_descriptors.txt (placed monsters) and items.txt and
    // object_list.txt (items on the floor); empty without an asset root, and a project that places a monster or an
    // item then fails with an issue saying so.
    std::string monsterTableText;
    std::string monsterDescriptorTableText;
    std::string itemTableText;
    std::string objectTableText;
    // engine/data_tables/english/place_mon.txt: the names a placed monster may bear while it lives.
    std::string uniqueNameTableText;
    // engine/data_tables/hostile.txt (the monster kinds' relations to the party and to each other) and map_stats.txt
    // (a reference row's encounter slots): what the hostility check reads (core/MonsterRelations.h); empty: no check.
    std::string relationTableText;
    std::string mapStatsTableText;
    // The project's world's relations.yml (factions and their relations, consulted before hostile.txt); empty: none.
    std::string worldRelationsText;
    // The asset root, to check that a placed sound's file is there (worlds/<world>/audio, engine/audio); empty: not
    // checked.
    std::filesystem::path assetRoot;
    // A mount folder read in front of the asset root (`oymap validate|build --mount`, the game's --extra-mount): its
    // sounds count too. Empty: none.
    std::filesystem::path mountRoot;
    // engine/liquids/liquids.yml: the texture names the game draws as liquids, which need no `size`; empty: a
    // surface without a size is not checked.
    std::string liquidTableText;
    // engine/models/indoor_decorations.yml: the 3D models dungeons draw decorations with (`height`, `z_offset`,
    // `swing` for one that hangs, `maps`); empty: decorations are measured by decoration_data.txt's height.
    std::string indoorModelBindingsText;
    // The tables above, parsed with their lookups (parseLoweringTables). A service keeps them once per asset root
    // (S5_BROWSER_EDITOR.md 2.4.3); without them the lowering parses the texts itself, once per lowering.
    std::shared_ptr<const LoweringTables> tables;
    // An overlay project's base map (S8a), read from the asset root by the build: the actor number its first added
    // monster gets (the base scene's actors and those the scene overlays applied before its own add), and the groups
    // the base map's actors and spawn points have (wiring may name them in `kills`, `show_actors`, `hide_actors`).
    size_t overlayFirstActor = 0;
    std::set<int> overlayBaseGroups;
};

// The asset tables as the lowering looks names up in them: each table's rows parsed once, and the decoration lookups
// by name (each the first matching row, as a scan of the table would find it).
struct LoweringTables
{
    struct DecorationShape
    {
        double radius = 0.0;
        double top = 0.0;
    };

    // By decoration name in lower case: the first row with six cells (radius, height), the first with three (the
    // hint), and the first whose number is above 0 (the row number less one: the BLV's decoration list id).
    std::map<std::string, DecorationShape> decorationShapes;
    std::map<std::string, std::string> decorationHints;
    std::map<std::string, int> decorationListIds;
    // Rows of tab-separated tables, cells trimmed, empty rows and `//` rows left out (the game's readers do the same).
    std::vector<std::vector<std::string>> monsterRows;
    std::vector<std::vector<std::string>> monsterDescriptorRows;
    std::vector<std::vector<std::string>> itemRows;
    std::vector<std::vector<std::string>> objectRows;
    std::vector<std::vector<std::string>> uniqueNameRows;
    std::vector<std::vector<std::string>> relationRows;
    std::vector<std::vector<std::string>> mapStatsRows;
    WorldMonsterRelations worldRelations;
    // engine/models/indoor_decorations.yml, read once; an empty node when absent or unreadable.
    YAML::Node modelBindings;
    // What a decoration draws with where no model binds it (the lowering's decorationWithoutArt), read once from the
    // asset root: each decoration's sprite (decoration_data.txt's thirteenth column, by name in lower case), each
    // sprite's pictures (rendering/sprite_frame_data_common.yml, lower case), the picture names (lower case, without
    // extension) of engine/sprites and engine/effects under "" and of worlds/<world>/sprites under the world, and the
    // worlds' own worlds/<world>/models/indoor_decorations.yml. Empty without an asset root.
    std::map<std::string, int> decorationSprites;
    std::map<int, std::vector<std::string>> spritePictures;
    std::map<std::string, std::set<std::string>> spriteFiles;
    std::map<std::string, YAML::Node> worldModelBindings;
};

std::shared_ptr<const LoweringTables> parseLoweringTables(const LoweringOptions &options);

// The rows of a tab-separated data table, each cell without the blanks round it; rows that are empty or begin with
// `//` are left out, as the game's table readers leave them out.
std::vector<std::vector<std::string>> parseTableRows(const std::string &text);

// What draws an item lying on the ground (indoors objects.yml `items`, outdoors sketch.yml `items`): the row of
// object_list.txt whose object number (column 2) is the item's sprite index (items.txt column 11), into `item`'s
// objectDescriptionId and spriteId, with its number. False when no row draws it.
bool groundItemObjectOf(
    const std::vector<std::string> &itemRow,
    const std::vector<std::vector<std::string>> &objectRows,
    LoweredItem &item);

// The degrees of a facing word (objects.schema.json $defs/facing): a compass side (n, e, ne, north ...) or a number
// (0 east, 90 north); none for anything else.
std::optional<double> facingWordDegrees(const YAML::Node &node);

// Lowers an indoor project to the indoor compiler's inputs. Problems are reported as issues with the file and path
// they come from; the result is usable only when no issue was added.
// Lowers the wiring of an overlay project (a project with a `base` map): each event that `replaces` one of the base
// map's becomes a handler under that event's number. `lowered.events` and `lowered.mapStem` (the base map's stem)
// are filled; there is no geometry. With `options` (the asset root's tables and the base map's numbers), also the
// monsters, items and ladders the overlay adds (objects.yml scene.monsters, items, ladders; S8a) into `monsters`,
// `items` and `ladders`, at their absolute places (their sectors are the base map's, found by the scene overlay's
// writer).
bool lowerOverlayProject(const Project &project, LoweredIndoorMap &lowered, std::vector<ProjectIssue> &issues);
bool lowerOverlayProject(
    const Project &project,
    const LoweringOptions &options,
    LoweredIndoorMap &lowered,
    std::vector<ProjectIssue> &issues);

bool lowerIndoorProject(
    const Project &project,
    const LoweringOptions &options,
    LoweredIndoorMap &lowered,
    std::vector<ProjectIssue> &issues);
}
