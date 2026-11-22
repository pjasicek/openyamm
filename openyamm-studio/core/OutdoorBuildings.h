#pragma once

#include "core/Project.h"

#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The buildings of an outdoor map. A plot of the sketch becomes one building model made of parts: each part is a
// prism over an outline (a box, a convex outline or a many-sided round) with walls of bays and a roof. The forms
// and their numbers are measured on the shipped towns (Ravenshore, Harmondale, New Sorpigal, Dagger Wound) and
// told at the top of OutdoorBuildings.cpp.

struct OutdoorRoofPlan
{
    // flat, hip, gable, lean_to, cone or none.
    std::string form = "hip";
    // From the roof's foot (the top of the fascia) to the ridge or the tip, map units.
    double rise = 96.0;
    // How far the roof reaches out past the walls.
    double eaves = 0.0;
    // The upright band between the walls' top and the roof's foot.
    double fascia = 0.0;
    // Hip: how far the ridge is drawn in from each end; 0: half the shorter side.
    double hipRun = 0.0;
    // A beam along the ridge of a hip or gable roof, this wide and high; 0: none.
    double ridge = 0.0;
    // Which way the ridge runs on a box: 'x' along the part's first side, 'y' across it, 0 along the longer side.
    char along = 0;
    // Flat: the walls stand this far above the roof as a parapet, 0 for none; `battlements` cuts it into merlons.
    double parapet = 0.0;
    bool battlements = false;
    // A gable roof on a part that is no box: the way its ridge runs, a unit vector in world units.
    std::array<double, 2> ridgeDirection = {1.0, 0.0};
    // Hip: the slopes stop this high above the roof's foot and a flat top closes them; 0: they meet.
    double cap = 0.0;
    // `tiers` (cone and hip): the roof in rings from its foot, each drawn in by [0] and up by [1] (a thatched hall's
    // roof that flattens toward its top); a ring that reaches the middle ends in a tip (cone only), else a flat top
    // closes the last. Empty: one slope to the tip or ridge, `rise` high.
    std::vector<std::array<double, 2>> tiers;
    // `dome_rings` (dome): the rings of the dome's quarter circle from its foot to its tip, 2 to 8; each ring is the
    // outline drawn in toward its middle (a round part's dome, Ravenshore's d28 mushroom cap with `eaves`).
    int domeRings = 4;
    // S8d: `vault_segments` (vault without `tiers`): the segments of each half of the vault's half ellipse, 2 to 8.
    // A vault is a gable whose two slopes are a curved section (`tiers` from each eaves side, a flat crown
    // between when they do not meet, or that half ellipse `rise` high), its end walls closed up to it.
    int vaultSegments = 4;
    // S8d: `half_hip` (a box's gable): each end hipped from its eaves up to this height over the roof's foot and
    // gabled above, the hip reaching `halfHipRun` in from the end; 0: a plain gable.
    double halfHip = 0.0;
    double halfHipRun = 0.0;
    // `eaves_walls`: the walls the eaves reach out over (the rest end flush with their wall, where the part meets
    // another and their eaves would overlap); empty: every wall.
    std::vector<bool> eavesWalls;
    // `eaves_walls` entries {wall, from, to} (batch S4R): per wall the stretches [from, to] along it (from its left
    // end seen from outside) the eaves reach out over; a wall named whole has [0, its length]. Empty when no entry
    // names a stretch; `eavesPartial` when one stops short of its wall's ends (Ravenshore's wings: the soffit begins
    // at the body's wall).
    std::vector<std::vector<std::array<double, 2>>> eavesStretches;
    bool eavesPartial = false;
    // An `eaves_walls` entry's own `eaves` (batch S4R): how far the roof reaches out over that wall; empty, or
    // negative for a wall: `eaves` (Keen Edge's upper storey: 192 over its north wall, where the roof covers the
    // roof walk's corner, 64 elsewhere).
    std::vector<double> eavesAmounts;
    // `parapet_walls` (batch S4R): per wall the stretches the parapet stands on; empty: round every wall.
    std::vector<std::vector<std::array<double, 2>>> parapetStretches;
    // The slope of a roof given by `roof_pitch` (rise over run), for a roof over an outline that bends in; 0: from
    // `rise` over the deepest point.
    double slope = 0.0;
};

// Buttresses on a part's walls: `count` piers on each wall named, evenly spaced, standing `depth` out and `height`
// high at the wall, their tops sloping down to the front by `depth` (a tapered top).
struct OutdoorButtressPlan
{
    int count = 0;
    double width = 64.0;
    double depth = 64.0;
    double height = 0.0;
    std::vector<bool> walls;
};

// A flight cut into a stepped or battered part from the foot of one wall up to its top (Dragonsand's pyramid,
// Dagger Wound's): `width` wide between two cheeks `cheek` wide standing `cheekHeight` over the flight's nosing line;
// the flight runs `run` from where it starts to where the part's top begins (left out: from the wall's foot), in
// steps of `rise` (or one sloping face with `ramp`). The steps and cheeks replace the part's faces over their span.
struct OutdoorStairPlan
{
    bool given = false;
    size_t wall = 0;
    // The middle of the flight along the wall from its left end, map units; negative: the wall's middle.
    double along = -1.0;
    double width = 256.0;
    double cheek = 64.0;
    double cheekHeight = 64.0;
    double run = 0.0;
    double rise = 32.0;
    bool ramp = false;
};

// A ruined part (`ruin`): each bay of the walls standing to its own height between `low` and `high` over the
// floor, a share `gaps` of the bays gone, walls `thickness` thick with their tops, and the roof gone or left as bare
// rafters (`roof: frame`, a ridge beam and a rafter at each end and every `every` between).
struct OutdoorRuinPlan
{
    bool given = false;
    double low = 128.0;
    double high = 256.0;
    double gaps = 0.0;
    double thickness = 8.0;
    std::string roof = "none";
    double every = 0.0;
    double rafter = 16.0;
    uint32_t seed = 1;
};

// A porch along a stretch of a part's wall: a sloping roof standing out from the wall (on posts, or hanging: a
// canopy over a door), or, with `recess`, the stretch set back into the part under the part's own roof.
struct OutdoorPorchPlan
{
    size_t wall = 0;
    // The bays of the wall's lowest row it spans, first and last.
    size_t fromBay = 0;
    size_t toBay = 0;
    // How far out from the wall (in, for a recess), map units.
    double depth = 128.0;
    // The roof's front edge above the part's foot, and how much higher it is at the wall.
    double height = 256.0;
    double rise = 64.0;
    // The roof's thickness at its front edge (its fascia).
    double thickness = 16.0;
    // How far the roof reaches past the stretch at each end.
    double overhang = 0.0;
    // Posts at the porch's front corners, this wide; 0: none (a canopy).
    double posts = 0.0;
    // A slab under the porch, this high over the part's foot (`floorFromLand`: over the land round the building,
    // under its `plinth`); 0: none.
    double floor = 0.0;
    bool floorFromLand = false;
    bool recess = false;
    // Batch O-H: a recess's head arched, round, pointed or segment, `archSides` segments, its top at the recess's
    // `height` over the floor (left out: the walls' top); empty: square to the walls' top.
    std::string arch;
    int archSides = 6;
    double archHeight = 0.0;
    // S8d: `open_corner: true`: a recess that runs to its wall's left (right) end is open there; the wall across it,
    // the one before (after) on the outline, stands back from the corner by the recess's depth (Castle Ironfist's
    // HouseR2S porch, Erathia's magic shop between its corner posts).
    bool openLeft = false;
    bool openRight = false;
    // Batch O-F: `form: portico` (a flat ceiling, an entablature band `thickness` high, `columns` round columns
    // with bases and capitals along its front, a gable `pediment` this high over it; 0 none), `posts_shape: round`.
    bool portico = false;
    bool roundPosts = false;
    size_t columns = 0;
    // 2: a second row of columns against the wall.
    size_t rows = 1;
    double pediment = 0.0;
};

// A board on a part's wall: a shop's sign over its door.
struct OutdoorWallSignPlan
{
    size_t wall = 0;
    // The middle of the board along the wall, map units from its left end seen from outside.
    double along = 0.0;
    double bottom = 160.0;
    double width = 128.0;
    double height = 64.0;
    // How far the board's face stands out from the wall (a board that hangs: from the wall to its near edge).
    double out = 8.0;
    std::string texture;
    // Batch O-H: a board with an event of its own (Castle Ironfist's STABLES board, the guild sign's boards): what it
    // says, and the house it enters (0 none). `event` is filled by the build; 0: the part's.
    std::string title;
    int house = 0;
    std::string path;
    uint16_t event = 0;
    // `hang`: the board stands across the wall under an arm from it, its picture on both faces (the shops' signs of
    // Ravenshore and Harmondale); else it lies flat on the wall.
    bool hang = false;
};

// A railing round the top of a flat part: posts and a rail along the walls named, open between.
struct OutdoorRailingPlan
{
    double height = 0.0;
    double posts = 16.0;
    double rail = 16.0;
    double every = 128.0;
    // The posts' and the rail's depth across the wall.
    double depth = 32.0;
    std::vector<bool> walls;
};

// A hole in a part's flat top, with a pit under it (a hatch's pit on a dais).
struct OutdoorHolePlan
{
    // Its corners in world units, counter-clockwise seen from above.
    std::vector<std::array<double, 2>> outline;
    double depth = 64.0;
};

struct OutdoorPartPlan
{
    std::string id;
    // box, outline or round.
    std::string shape = "box";
    // The outline in world units, counter-clockwise seen from above (x east, y north). Wall i runs from point i
    // (its left end seen from outside) to point i + 1. A box's walls are south, east, north, west in the plot's
    // own frame before it is turned.
    std::vector<std::array<double, 2>> outline;
    // An outline part whose outline bends in (an L, a notched front; batch S4R): its walls as any part's, one roof
    // over the whole (core/OutdoorRoofCover), its tops and undersides in convex pieces.
    bool concave = false;
    // The foot of the walls above the building's floor, and their height.
    double bottom = 0.0;
    double wallHeight = 256.0;
    // How wide the top of the walls is against their foot, about the outline's middle: 1 upright walls, less a
    // part that draws in (a spire), more one that flares (a cap).
    double taper = 1.0;
    // `climb`: the part is a step the party walks up (a dais's ring): each wall that stands over a lower floor
    // gets the hidden slope of the shipped maps' flights, from its foot up to the part's top this far in, and the
    // wall lets the party through. 0: none.
    double climb = 0.0;
    // Filled when reading: per wall, the floor in front of it above the building's floor where the party climbs it
    // (the ground, or a lower part's flat top); none where the wall is not climbed (it faces a higher part).
    std::vector<std::optional<double>> climbFrom;
    // `posts`: the part is open: no walls, a post this wide at each corner of its outline (a pavilion, a shrine on
    // pillars), more along a wall where `post_every` says, a ceiling under its roof; 0: walls.
    double posts = 0.0;
    // `posts_shape: round` (batch O-F): each post a round column on a base under a capital.
    bool roundPosts = false;
    double postEvery = 0.0;
    // `post_walls`: the walls that have posts (each with the posts at its two corners); every wall when left out.
    // An open part against a house's wall (a porch on posts, an upper storey reaching out) has none on that wall.
    std::vector<bool> postWalls;
    // An open part's low wall between its posts, this high over its foot, on the walls `sillWalls` marks; 0: none.
    double sill = 0.0;
    std::vector<bool> sillWalls;
    std::vector<OutdoorPorchPlan> porches;
    std::vector<OutdoorWallSignPlan> signs;
    OutdoorRailingPlan railing;
    std::vector<OutdoorHolePlan> holes;
    // `court` (batch O-H): an open court through a box part, its corners in world units counter-clockwise, each
    // paired with the part's corner nearest it; the part has walls round the court too and its roof (hip or flat)
    // runs round it, a hip's ridge ring midway between the outer walls and the court's (Erathia's Castle
    // Gryphonheart keep). `courtEaves`: how far the roof reaches out over the court's walls. Empty: none.
    std::vector<std::array<double, 2>> court;
    double courtEaves = 0.0;
    // `batter`: the walls draw in this far from their foot up to `batterHeight` over it (0: the whole wall), on the
    // walls `batterWalls` marks (every wall when empty); doors stand upright at the foot, set into the slope
    // (Ironsand's ogre forts, the Plane of Fire's guard towers). 0: upright walls.
    double batter = 0.0;
    double batterHeight = 0.0;
    std::vector<bool> batterWalls;
    // S8d: `pent`: a skirt roof round the walls (Erathia's House 10E/W, 128 out at the first floor): from the wall
    // at `pentHeight` + `pentRise` over the foot down to `pentOut` out from it, `pentThickness` thick at its edge.
    // 0 high: none.
    double pentHeight = 0.0;
    double pentOut = 128.0;
    double pentRise = 64.0;
    double pentThickness = 16.0;
    OutdoorButtressPlan buttresses;
    // `door_height`: how high a door stands; a door higher than the walls is cut into the roof over them (a tent's,
    // a hut's whose roof reaches the ground). 0 (left out): 256, and cut into the roof only over walls lower than 128.
    double doorHeight = 0.0;
    // `steps`: terraces over the walls' top, each the outline drawn in by [0] and raised by [1] with an upright riser;
    // the roof sits on the last (Dragonsand's pyramid: [[256, 256], ...]).
    std::vector<std::array<double, 2>> steps;
    OutdoorStairPlan stair;
    OutdoorRuinPlan ruin;
    OutdoorRoofPlan roof;
    // Per wall: the roles of its bays from left to right on the lowest row of 256, and on the rows above. An
    // empty list is one plain stretch of the `wall` role.
    std::vector<std::vector<std::string>> bays;
    std::vector<std::vector<std::string>> upperBays;
    // Per wall and bay, the width a listed bay is given (`[t14a01, 64]`); 0 (or none): an equal share of what the
    // given ones leave of the wall.
    std::vector<std::vector<double>> bayWidths;
    std::vector<std::vector<double>> upperBayWidths;
    // `window_arch`: the window bays' heads arched, round or pointed (their picture's top corners cut away, the wall
    // round them); empty: square.
    std::string windowArch;
    // `band`: an upright band this high between the lowest row and the rows above (the floor beam of an upper
    // storey), so the rows above begin at 256 + band; 0: none.
    double band = 0.0;
    // Role to texture: wall, window, door, post_left, post_right, upper, roof, trim, ridge, gable, base and
    // whatever more the bays name.
    std::map<std::string, std::string> textures;
    // Textures of the part that are liquids (`textures.<role>: {texture, liquid, flow}`): their face bits.
    std::map<std::string, uint32_t> liquids;
    // Roles laid once per bay (`textures.<role>: {texture, fit: true, size: [w, h]}`): the picture's size in texels,
    // stretched once over each bay of the lowest row (a window bay wider than the picture shows it once, not 1.5
    // times); the rows above lay such a bay as plain wall unless `upper_walls` names the role.
    std::map<std::string, std::array<double, 2>> fitted;
    // What this part says when looked at, when it has a name of its own (a shop of a joined block); empty: the
    // building's.
    std::string title;
    // Where the sketch draws the part ("districts[0].plots[3].parts[1]"), for what a click on it does
    // (core/OutdoorEvents).
    std::string path;
    // Filled by the build: the event of this part's faces that are no door (its own title, or what a click on the
    // part does); 0: the building's `nameEvent`.
    uint16_t event = 0;
};

struct OutdoorDoorPlan
{
    // Where the door is: the part, its wall, the bay of that wall's row, and the row (0 the ground floor, 1 the row
    // of `upper_walls` above it, each 256 higher).
    size_t part = 0;
    size_t wall = 0;
    size_t bay = 0;
    size_t storey = 0;
    // The house the door enters (a row of the house table), 0 for none.
    int house = 0;
    // The map the door leads into instead, with the place the party arrives at; empty for none.
    std::string toMap;
    int arrival[3] = {0, 0, 0};
    int arrivalFacing = 0;
    // `into.arrival`: a named arrival of that map (D-4), which the build looks up in its <stem>.studio.yml; empty for
    // `at` or the map's start. `arrivalFacingGiven`: `into.facing` was given, and wins over the arrival's.
    std::string arrivalName;
    bool arrivalFacingGiven = false;
    // The entrance window of `into.screen` (readMoveScreen): the standard window into a dungeon unless `none`.
    MoveScreen screen;
    // What the door says when looked at.
    std::string title;
    // `step`: a slab before the door, this deep and high, reaching `stepOverhang` past the door at each side; 0
    // deep: none.
    double stepDepth = 0.0;
    double stepHeight = 16.0;
    double stepOverhang = 32.0;
    // The step's height over the floor at its front edge: its top slopes from there up to `stepHeight` at the wall
    // (Ravenshore's lanes: a stoop up to a door that stands 80 over the street); `stepHeight` when the step is flat.
    double stepFront = 0.0;
    // The texture the door's bay names in the wall's list when that is a texture's own name and no role (a door
    // of the upper row's own panels); empty: the part's `door` role.
    std::string texture;
    // Where the sketch says what the door does (the plot, or the entry of its `doors`), for its condition and
    // effects (core/OutdoorEvents).
    std::string path;
    // `same_event_as`: the door carries another door's event (the original's one event on several doors of a
    // building: Buccaneers' Lair's three), as a key of the buildings' events: "building:<id>" (its own door, else
    // its name), "building:<id>/door:<n>" (the n-th of its `doors`, 0 its own door). Empty: its own.
    std::string sameEventAs;
    // Door dressing (Mount Nighon's keep, Ironsand's dungeon doors, the Shadow Guild's hood). `arch`: the head round
    // or pointed, `archSides` segments; empty: square.
    std::string arch;
    int archSides = 6;
    // Two leaves side by side, the second the first's picture mirrored; 1: one. `leavesGiven`: the sketch said
    // `leaves`; else a door whose picture is one wing of a double door (the texture classes) becomes a pair (F2).
    int leaves = 1;
    bool leavesGiven = false;
    // Each leaf of a pair shows its picture once at this many texels across (the picture's own width, from the
    // texture classes: a 256-wide `egydrlgl` or `swdoora` whole on each leaf); 0: 128, a wing's width.
    double pictureWidth = 0.0;
    // A hood over the door: a slab at the door's top reaching this far out, on a cheek at each side; 0: none.
    double hood = 0.0;
    // Nested frames round the door: `frameSteps` rings, each `frameStep` wider and standing `frameStep` / 2 further
    // out than the one inside it, in `frameTexture` (the part's trim when empty); a portcullis of bars before it.
    int frameSteps = 0;
    double frameStep = 32.0;
    std::string frameTexture;
    bool portcullis = false;
    // S8d: `sill`: the door stands this high over its row's foot, the wall under it (Castle Ironfist's King's
    // Library door, 128 over the forecourt; Snergle's Caverns, 64); 0: on the floor.
    double sill = 0.0;
    // Filled by the build: the event number (0: the door opens nothing), the face of the model that is the door,
    // the middle of the door at the floor and the way it looks (world units; a unit vector).
    uint16_t event = 0;
    int face = -1;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double normalX = 0.0;
    double normalY = 0.0;
};

struct OutdoorBuildingPlan
{
    // The plan building, with "#<index>" for a member of a group.
    std::string id;
    // The plot in sketch cells: x runs east, y south. The ground under it is made level.
    double west = 0.0;
    double north = 0.0;
    double east = 0.0;
    double south = 0.0;
    // The side the front is on: 'n', 'e', 's' or 'w' (before the plot is turned).
    char facing = 's';
    // How far the walls go down below the floor, so that sloping ground beside the plot shows no gap.
    double foundation = 128.0;
    // `plinth`: the floor stands this far over the land made level under the plot (a house on a base course over
    // the street, its door slab showing); 0: the land is made level at the floor.
    double plinth = 0.0;
    // `against: slope`: the building stands against a slope or cliff behind it: the walls facing its back are left
    // out and the land under the plot is not made level but for the front row of nodes (core/OutdoorLowering).
    bool against = false;
    // Filled when reading: the way the back faces, a unit vector in world units (x east, y north).
    std::array<double, 2> back = {0.0, 1.0};
    // `skirt`: the base course of the parts on the ground goes down into the land in this texture (the ground's
    // own), as deep as the lowering finds the land falls round the plot; the plot is not made level. Empty: none.
    std::string skirt;
    // `on`: the id of a `kind: deck` structure the building stands on (batch O-F, Pierpont's houses on decks): its
    // floor is the deck's top, its walls reach down through the deck, and the land under the plot is left alone.
    std::string onDeck;
    // What the building says when looked at.
    std::string title;
    // `hint` (batch O-H): what the building's faces that are no door say instead of its title (Erathia's homes:
    // "House" on the walls, the door its own name); with `hintShared` one event for every thing whose shared hint
    // says the same (the original's event 51 on 22 homes).
    std::string hint;
    bool hintShared = false;
    // Where the sketch draws it ("districts[0].plots[3]", "structures[12]").
    std::string path;
    std::vector<OutdoorPartPlan> parts;
    // The doors; the first is the plot's own (`house`, `into`), also when it opens nothing.
    std::vector<OutdoorDoorPlan> doors;
    // The floor's height when the sketch says it (`floor`): the ground under the plot is made level there.
    bool floorGiven = false;
    double floor = 0.0;
    // Filled by the lowering: the floor's height (the ground under the plot is made level at it), map units.
    double base = 0.0;
    // Filled by the build: the event of the faces that are no door (it only says the title), 0 for none.
    uint16_t nameEvent = 0;
    // The ground the building covers, in sketch cells [west, north, east, south]: the bounds of its parts with
    // their eaves. Scattered things keep off it.
    std::array<double, 4> covered = {0.0, 0.0, 0.0, 0.0};
    // Filled by the build: per face of the model, the part it belongs to ("part:<id>", or "part:<index>" for a
    // part without an id), for messages (core/Coplanar).
    std::vector<std::string> faceParts;
};

// What the texture classes say of a door picture (texture_classes.yml, written by tools/xeen/texture_classes.py;
// devdocs/xeen/formats/DOORS.md): its door role, its size in texels and a wing's twin.
struct OutdoorDoorPicture
{
    // single, wing, pair or tile.
    std::string door;
    std::array<int, 2> size = {0, 0};
    // The other wing of a double door (`twin`); empty: none known.
    std::string twin;
};

// By texture name in lower case; only the pictures with a door role.
using OutdoorDoorPictures = std::map<std::string, OutdoorDoorPicture>;

// The door pictures of texture_classes.yml texts (the engine's first, then the world's: a later row wins).
OutdoorDoorPictures parseOutdoorDoorPictures(const std::vector<std::string> &texts);

// The door pictures of an asset root: engine/models/texture_classes.yml and worlds/<world>/models/'s. Empty without.
OutdoorDoorPictures readOutdoorDoorPictures(const std::filesystem::path &assetRoot, const std::string &world);

// The sketch's plots as buildings to raise, in the sketch's order. Plots with `form: none` and buildings without a
// footprint in the plan are left out. `world` chooses the textures and the roof a plot does not name. With
// `pDoorPictures` (the build's asset root's texture classes) a door whose picture is a wing becomes a double door and
// each leaf of a pair shows its picture at its own width (F2, D-91).
std::vector<OutdoorBuildingPlan> readOutdoorBuildings(
    const Project &project,
    const std::string &world,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings,
    const OutdoorDoorPictures *pDoorPictures = nullptr);

// Where the bays of a wall of a part begin and end, as fractions of the wall from its left end (seen from outside):
// one more than the bays of that row (`upper`: the rows above the lowest).
std::vector<double> outdoorBayEdges(const OutdoorPartPlan &part, size_t wall, bool upper);

// The building model of a plan with its `base` set. Sets each door's `face` and place (and gives that face the
// door's event, if any; the other faces get `nameEvent`).
Game::OutdoorBModel raiseOutdoorBuilding(OutdoorBuildingPlan &plan);

// The names of the face textures a world has under an asset root (lower case, without extension): the files of
// worlds/<world>/textures* and of engine/textures*. Empty when the root has neither. With a mount folder read in front
// of the root (`--mount`), its own textures* folders and those of its engine/ and worlds/<world>/ count too.
std::set<std::string> outdoorTextureNames(const std::filesystem::path &assetRoot, const std::string &world,
    const std::filesystem::path &mountRoot = {});

// Every texture the buildings name that `known` does not hold, as issues that say which plot names it.
void checkOutdoorBuildingTextures(
    const std::vector<OutdoorBuildingPlan> &buildings,
    const std::set<std::string> &known,
    const std::string &world,
    std::vector<ProjectIssue> &issues);

// The same for finished models (the structures'): every face's texture. Liquids (water, lava: drawn by the game
// without a picture) pass.
void checkOutdoorModelTextures(
    const std::vector<Game::OutdoorBModel> &models,
    const std::set<std::string> &known,
    const std::string &world,
    std::vector<ProjectIssue> &issues);

// The kits of a world: named sets of role textures a plot or a part takes with `kit`. For `oymap schema` texts and
// messages.
std::vector<std::string> outdoorKitNames(const std::string &world);
}
