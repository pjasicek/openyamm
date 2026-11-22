#pragma once

#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A family of chest textures (`chests[].kind` indoors, `kind` on an outdoor chest), as the shipped chests are laid
// (measured on 2026-11-13 in Gharik's Forge and Castle Darkmoor for MM6, the Temple of the Moon, Celeste and the
// Tularean caves for MM7, the Abandoned Temple and others for MM8; outdoors MM7's 7out01 `chest_N`, 2026-11-22). The
// long sides show a left end 16 wide, a middle and a right end 16 wide (the end as seen from in front of that side on
// its left); the top the same, its left-end piece at the right as seen from in front of the chest (the picture runs
// on from the front over the top edge); the two short ends one picture. MM6's chests are a box 96 by 64 and 64 high
// with a flat lid, their ends their own textures 16 wide. MM7's and MM8's are a box 96 by 64 and 64 high with a lid
// 16 high whose front and back slope at 45 degrees up to a top 32 deep; their ends are the first and the last 16
// columns of one texture 64 wide.
struct ChestKind
{
    std::string frontLeft;
    std::string frontMiddle;
    std::string frontRight;
    std::string side;
    std::string topLeft;
    std::string topMiddle;
    std::string topRight;
    // A sloping lid: the front slope's middle and the upper strip of the short ends (the back slope and the top
    // take the front's middle and ends).
    bool sloped = false;
    std::string slopeMiddle;
    std::string sideTop;
    std::array<double, 3> size = {96.0, 64.0, 64.0};
    // MM6's "v" lid (`lid: v`): pictures turned a quarter, laid as the shipped chests lay them (the Forge's chest at
    // (-1440, 6704), faces 1910 to 1913): across the lid from the front (u 0) to the back, and along it from the left
    // end seen from the front (the +width end: the left end strip, the middle, the right end strip, each picture's
    // rows starting at its +width edge), the end strips 64 across and 16 along.
    bool lidAcross = false;
};

std::optional<ChestKind> chestKindOf(const std::string &name);

// The kinds, for messages.
std::string chestKindList();

// A world's plain chest kind: mm8 `gt002`, mm7 `7gt002` (also Xeen's, built in MM7's style), else MM6's `ch1`.
std::string defaultChestKind(const std::string &styleWorld);

// The kind whose front middle a texture is (`ch3frntB` is ch3's): a surface that names one stretches it over the
// whole chest.
std::string chestFamilyOfMiddle(const std::string &texture);

// Whether a texture is one of the shipped chests' pictures (a chest kind's family: ch1 to ch5, 7gt002, gt002, ch001
// to ch006), which the player reads as a chest.
bool isChestTexture(const std::string &texture);

// Which part of a chest a face is.
enum class ChestPart
{
    Side,
    End,
    EndTop,
    Slope,
    Top
};

// One face of a chest of a kind, in the chest's own frame: `across` along its width (its `facing` indoors), `deep`
// along its depth (the front is +deep), z up. `sign` is +1 for the front, the +width end and the front slope, -1 for
// the back, the -width end and the back slope, 0 for the top. Texels per corner at the picture's own size (`width`
// texels across, 64 high), `normal` outward in the same frame.
struct ChestFace
{
    ChestPart part = ChestPart::Side;
    double sign = 0.0;
    std::string texture;
    int width = 64;
    std::vector<std::array<double, 3>> corners;
    std::vector<std::array<double, 2>> texels;
    std::array<double, 3> normal = {0.0, 0.0, 0.0};
};

// Every face of a chest of a kind `size` (width, depth, height) between `bottom` and `top`, in the order indoor
// builds have laid them: the front and the back (left end, middle, right end each), the +width end (and its strip
// under the lid), the -width end, the front and the back slope, the top. No bottom. A sloping kind 96 x 64 x 80 is
// the shipped chest of 19 faces (7gt002: a 4, b 10, c 2, e 1, g 2).
std::vector<ChestFace> chestKindFaces(const ChestKind &kind, const std::array<double, 3> &size, double bottom,
    double top);

// D-99 (devdocs/xeen/DECISIONS.md): how a chest stands. A chest against a wall stands with its back to it and its
// front (the lock, the sloping lid's own picture) to the room; in a niche or an alcove it faces out of it; standing
// free it faces the doorway the party enters its room by. Measured on MM7's Castle Harmondale, the Barrow Downs and
// four other dungeons, and fifteen MM8 dungeons (2026-11-22): of 81 chests 60 stand with their back on a wall (gap 0),
// none end-on to their nearest wall, and every free-standing MM8 chest shows its front to its room's nearest doorway.
namespace ChestFacing
{
// A side of a chest within this of a wall stands against it.
constexpr double Reach = 64.0;
// A free chest whose front turns further than this from its room's entrance shows the entrance its back.
constexpr double EntranceDegrees = 100.0;
}

// A stretch of solid wall seen from above (a doorway is not one).
struct ChestWall
{
    std::array<double, 2> from = {};
    std::array<double, 2> to = {};
};

// How far each side of a chest is from the nearest wall straight out from its middle (1e9: none), its sides 90 degrees
// apart from `front`: the front, the back and the two ends.
struct ChestGaps
{
    double front = 1.0e9;
    double back = 1.0e9;
    double endLeft = 1.0e9;
    double endRight = 1.0e9;

    double nearest() const;
};

// The gaps of a chest `width` wide (along its ends' axis) and `depth` deep standing at `centre` with its front toward
// `frontRadians` (counter-clockwise from east).
ChestGaps chestGaps(const std::vector<ChestWall> &walls, const std::array<double, 2> &centre, double frontRadians,
    double width, double depth);

// D-99's fault of a chest standing so, or empty: its front to a wall, an end to the wall with its back to the room, or
// (free-standing) its back to the room's entrance (`entranceDegrees`, the turn from its front to its room's entrance,
// when known). `frontKnown` false: a chest whose front and back look alike (MM6's), whose either long side may be its
// back.
std::string chestFacingFault(const ChestGaps &gaps, bool frontKnown, std::optional<double> entranceDegrees);

// D-99 (b): where a chest may stand. Never in a doorway, at a stair's end or on the walking line between its room's
// ways: its footprint keeps a party's width and a margin (128) clear of a doorway or a door, in front of it or beside
// it along its wall, and 64 from the straight line between the middles of two ways of its room.
namespace ChestPlacement
{
constexpr double DoorwayFront = 128.0;
constexpr double DoorwayBeside = 128.0;
constexpr double SideMargin = 64.0;
constexpr double WalkingLine = 64.0;
}

// A way into a chest's room, seen from above: a doorway's or a door's opening along its wall (`from` to `to`), or a
// stair's end; `name` for messages.
struct ChestDoorway
{
    std::array<double, 2> from = {};
    std::array<double, 2> to = {};
    std::string name;
};

// The corners of a chest's footprint `width` by `depth` at `centre` with its front toward `frontRadians`.
std::array<std::array<double, 2>, 4> chestFootprint(const std::array<double, 2> &centre, double frontRadians,
    double width, double depth);

// D-99 (b)'s fault of a chest with this footprint, or empty: too near a doorway (in front or beside), or on the
// walking line between two of `doorways` (each pair, by their middles; `lines` false checks the doorways alone).
std::string chestPlacementFault(const std::array<std::array<double, 2>, 4> &footprint,
    const std::vector<ChestDoorway> &doorways, bool lines);
}
