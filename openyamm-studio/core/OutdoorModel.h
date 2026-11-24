#pragma once

#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A point of a model in world units.
using OutdoorModelPoint = std::array<double, 3>;
// Logical repeat size of pictures that share a horizontal and vertical phase on outdoor walls.
using OutdoorWallTiles = std::map<std::string, std::array<double, 2>>;

// Whether the game's party walks up a model face that climbs `rise` over `run` (map units): game/outdoor slides
// it down a face whose normal points up less than 0.70767 (WalkableNormalZ, just under 45 degrees) when the face
// spans 128 or more in height (MaxSmallSlopeHeight); a lower face it walks at any slope.
bool outdoorSlopeWalkable(double rise, double run);

// The face bits of a liquid face of `world`, as the shipped outdoor maps set them (measured for batch O-C):
// `liquid` water: the fluid bit (the picture ripples; every well and fountain); lava: MM6 the fluid bit only (Hermit's
// Isle's temple pools, baaS: LAVATYL 0x110), MM7 and MM8 the burning bit without the fluid bit (the Plane of Fire's
// streams, ElemFhouse2: LavTyl 0x4200110c); `flow` up, down, left or right (the picture moves 62.5 texels a second
// that way). Either may be empty. UINT32_MAX for a word that is neither.
uint32_t outdoorLiquidBits(const std::string &liquid, const std::string &flow, const std::string &world);

// Puts faces into a building model as the game's own outdoor maps store them: flat convex polygons wound
// counter-clockwise seen from outside, each with its plane, its polygon type (1 a wall, 3 a floor, 4 between floor
// and wall, 5 a ceiling, 6 between ceiling and wall), the plane bit of its attributes and its texels per corner.
// Corners that fall on the same whole unit are one vertex.
class OutdoorModelBuilder
{
public:
    explicit OutdoorModelBuilder(Game::OutdoorBModel &model, const OutdoorWallTiles *pWallTiles = nullptr);

    // A face with its texels given per corner. `event` (0 for none) makes the face one that can be clicked and
    // runs that event. The face's number in the model, or -1 when the points span no area.
    int addFace(
        const std::vector<OutdoorModelPoint> &points,
        const std::string &texture,
        const std::vector<std::array<double, 2>> &texels,
        uint16_t event);

    // A face whose texture lies on it one texel to a unit: across the face level, down its slope (a level face:
    // east and south; a wall: along it and down).
    int addSurface(const std::vector<OutdoorModelPoint> &points, const std::string &texture, uint16_t event);

    // A box between two corners, looked at from outside, without its bottom: four walls and a top.
    void addBox(
        const OutdoorModelPoint &low,
        const OutdoorModelPoint &high,
        const std::string &sideTexture,
        const std::string &topTexture,
        uint16_t event);

    // A prism over a convex outline (counter-clockwise seen from above) between two heights: its sides, its top
    // when `top` names a texture, its underside when `bottom` names one. `leaveOut`, when not -1, is a side left out
    // (the one from that corner of the outline to the next): a side lying on another solid's face, which would lie
    // back to back with it.
    void addPrism(
        const std::vector<std::array<double, 2>> &outline,
        double low,
        double high,
        const std::string &sideTexture,
        const std::string &topTexture,
        const std::string &bottomTexture,
        uint16_t event,
        int leaveOut = -1);

    // The hidden sloping face the shipped maps lay over a flight of steps (Harmondale's Fort__1: attributes 0x3108,
    // 220 flights on the 42 MM6-MM8 outdoor maps): a face like `addSurface`'s, not drawn (Invisible) and not
    // picked, but walked on, from the foot of the lowest riser through the foot of each riser to the top's edge.
    // The risers under it are let through with `letThrough`, as the shipped maps' are (975 of 975 Untouchable), so
    // the party meets the slope and walks up it.
    int addStepSlope(const std::vector<OutdoorModelPoint> &points, const std::string &texture, uint16_t event);

    // A face the party passes through (the game's Untouchable bit): a riser under a step slope. Still drawn.
    void letThrough(int face);

    // A face not drawn but solid (the game's Invisible bit): the barrier between a railing's posts, as Ravenshore's
    // terrace has it.
    void hide(int face);

    // Hides (as `hide`) each face from `from` up to `to` that lies in the plane of a face from `coverFrom` up to
    // `coverTo`, facing the same way: a board's face under the picture drawn on it, which would flicker with it.
    void hideUnder(size_t from, size_t to, size_t coverFrom, size_t coverTo);

    // How many faces the model has so far.
    size_t faceCount() const;

    // The model's bounds, middle and radius from its vertices. Call once, after the last face.
    void finish();

private:
    uint16_t vertexOf(const OutdoorModelPoint &point);

    Game::OutdoorBModel &m_model;
    const OutdoorWallTiles *m_pWallTiles;
    std::map<std::array<int, 3>, uint16_t> m_indices;
};
}
