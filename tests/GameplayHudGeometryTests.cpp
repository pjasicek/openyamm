#include "doctest/doctest.h"
#include "game/ui/GameplayHudArcMesh.h"
#include "game/ui/GameplayHudGeometry.h"
#include "game/ui/GameplayHudCommon.h"
#include "game/ui/GameplayBuffHud.h"
#include "game/ui/GameplayUiSkin.h"
#include "game/ui/GameplayClock.h"
#include "game/ui/GameplayPortraitGems.h"
#include "game/ui/RestHourglassAnimation.h"

#include <limits>

using namespace OpenYAMM::Game;

TEST_CASE("creature inspect crops native sprite coordinates without fitting the canvas")
{
    const HudSpritePreviewQuad bitmap = actorInspectSpriteQuad(100, 50, 128, 1, 200, 300, 0, 0, 300, -60);
    CHECK(bitmap.x == 100);
    CHECK(bitmap.y == 50);
    CHECK(bitmap.width == 128);
    CHECK(bitmap.height == 128);
    CHECK(bitmap.u0 == doctest::Approx(36.0 / 200));
    CHECK(bitmap.v0 == doctest::Approx(60.0 / 300));
    CHECK(bitmap.u1 == doctest::Approx(164.0 / 200));
    CHECK(bitmap.v1 == doctest::Approx(188.0 / 300));

    // A cropped atlas retains native canvas placement: occupied origin (20,80), size (160,180).
    const HudSpritePreviewQuad atlas = actorInspectSpriteQuad(100, 50, 128, 1, 160, 180, 0, 40, 300, -60);
    CHECK(atlas.x == bitmap.x);
    CHECK(atlas.y == 70);
    CHECK(atlas.width == bitmap.width);
    CHECK(atlas.height == 108);
    CHECK(atlas.u0 == doctest::Approx((36.0 - 20) / 160));
    CHECK(atlas.v0 == 0);
    CHECK(atlas.v1 == doctest::Approx((188.0 - 80) / 180));

    const HudSpritePreviewQuad doubledUi = actorInspectSpriteQuad(200, 100, 256, 2, 160, 180, 0, 40, 300, -60);
    CHECK(doubledUi.x == atlas.x * 2);
    CHECK(doubledUi.y == atlas.y * 2);
    CHECK(doubledUi.width == atlas.width * 2);
    CHECK(doubledUi.height == atlas.height * 2);
    CHECK(doubledUi.u0 == atlas.u0);
    CHECK(doubledUi.v1 == atlas.v1);
    CHECK(actorInspectSpriteQuad(0, 0, 128, 1, 20, 20, 0, 0, 20, -60).height == 0);
}

TEST_CASE("creature inspect clock excludes closed intervals and caps stalls")
{
    GameplayActorInspectClock clock;
    CHECK(clock.update(true, 1000) == 1);
    CHECK(clock.update(true, 1016) == 17);
    CHECK(clock.update(false, 1032) == 17);
    CHECK(clock.update(true, 5000) == 17);
    CHECK(clock.update(true, 5016) == 33);
    CHECK(clock.update(true, 6000) == 65);
    clock.lastUpdateTicks = std::numeric_limits<uint32_t>::max() - 7;
    CHECK(clock.update(true, 8) == 81);
}

TEST_CASE("HUD arc mesh cache reuses unchanged meters and responds to geometry changes")
{
    HudArcMeshCache cache;
    const HudArcMeshInput full{10, 20, 100, 150, 6, 100, 160, 0, 1};
    const HudArcMesh &fullMesh = cache.get(full);
    REQUIRE_FALSE(fullMesh.vertices.empty());
    const HudArcMeshVertex *pVertices = fullMesh.vertices.data();
    CHECK(cache.get(full).vertices.data() == pVertices);

    HudArcMeshInput changed = full;
    changed.end = 0.25f;
    const HudArcMesh &partial = cache.get(changed);
    CHECK(partial.vertices.size() < fullMesh.vertices.size());
    CHECK(partial.vertices.back().u == 1);
    CHECK(partial.vertices.back().x != fullMesh.vertices.back().x);
    CHECK(cache.get(full).vertices.data() == pVertices);

    // Every field can change independently: fill, moving/resized portraits, stroke and arc direction.
    const std::array<float HudArcMeshInput::*, 9> fields = {&HudArcMeshInput::x, &HudArcMeshInput::y,
        &HudArcMeshInput::width, &HudArcMeshInput::height, &HudArcMeshInput::strokeWidth,
        &HudArcMeshInput::startDegrees, &HudArcMeshInput::sweepDegrees, &HudArcMeshInput::begin,
        &HudArcMeshInput::end};
    for (float HudArcMeshInput::*field : fields)
    {
        changed = full;
        changed.*field += field == &HudArcMeshInput::end ? -0.1f : 0.1f;
        const HudArcMesh &mesh = cache.get(changed);
        CHECK(&mesh != &fullMesh);
        CHECK(cache.get(changed).vertices.data() == mesh.vertices.data());
    }
}

TEST_CASE("HUD arc mesh cache handles animated values eviction clearing and closed rims")
{
    HudArcMeshCache cache;
    HudArcMeshInput input{10, 20, 100, 150, 6, 100, 360, 0, 1};
    const HudArcMeshVertex first = cache.get(input).vertices.front();
    CHECK(cache.get(input).vertices.front().u == 0.5f);
    CHECK(cache.get(input).vertices.back().u == 0.5f);
    for (int i = 0; i < 200; ++i)
    {
        input.x = 10 + float(i);
        const HudArcMesh &mesh = cache.get(input);
        REQUIRE_FALSE(mesh.vertices.empty());
        CHECK(mesh.vertices.front().x == doctest::Approx(first.x + i));
    }
    input.x = 10;
    CHECK(cache.get(input).vertices.front().x == first.x);
    input.end = 0;
    CHECK(cache.get(input).vertices.empty());
    CHECK(cache.get(input).indices.empty());
    cache.clear();
    input.end = 1;
    CHECK(cache.get(input).vertices.front().x == first.x);
    input.sweepDegrees = -160;
    CHECK(cache.get(input).vertices.front().u == 0);
    CHECK(cache.get(input).vertices.back().u == 1);
}

TEST_CASE("Obsidian thumb controls retain bottom placement until the party frame occupies their lane")
{
    const GameplayResolvedHudLayoutElement group{740, 360, 220, 104, 1};
    const GameplayResolvedHudLayoutElement narrowParty{340, 376, 200, 104, 1};
    CHECK(GameplayHudCommon::touchPanelVerticalOffset(group, narrowParty) == 0);
    const GameplayResolvedHudLayoutElement fullParty{340, 376, 446, 104, 1};
    const float offset = GameplayHudCommon::touchPanelVerticalOffset(group, fullParty);
    CHECK(offset < 0);
    CHECK(group.y + offset + group.height == doctest::Approx(fullParty.y - 12));
    const GameplayResolvedHudLayoutElement ornamentOverlap{790, 360, 104, 104, 1};
    CHECK(GameplayHudCommon::touchPanelVerticalOffset(ornamentOverlap, fullParty) < 0);
    GameplayResolvedHudLayoutElement alreadyClear = group;
    alreadyClear.y += offset;
    CHECK(GameplayHudCommon::touchPanelVerticalOffset(alreadyClear, fullParty) == 0);
}

TEST_CASE("Obsidian rest hourglass drains then turns without resetting its painted orientation")
{
    namespace Atlas = RestHourglassAtlas;
    CHECK(restHourglassFrame(0).sandFrame == 0);
    CHECK(restHourglassFrame(4).sandFrame == (Atlas::framesPerOrientation - 1) / 2);
    CHECK(restHourglassFrame(8).sandFrame == Atlas::framesPerOrientation - 1);
    CHECK(restHourglassFrame(8.5f).sandFrame == Atlas::framesPerOrientation - 1);
    CHECK(restHourglassFrame(8.5f).frameRotationRadians == doctest::Approx(std::numbers::pi_v<float> / 2));
    CHECK(restHourglassFrame(9).sandFrame == Atlas::framesPerOrientation);
    CHECK(restHourglassFrame(9).frameRotationRadians == doctest::Approx(std::numbers::pi_v<float>));
    CHECK(restHourglassFrame(9).sandRotationRadians == 0);
    CHECK(restHourglassFrame(17).sandFrame == 2 * Atlas::framesPerOrientation - 1);
    CHECK(restHourglassFrame(18).sandFrame == 0);
    CHECK(restHourglassFrame(18).frameRotationRadians == 0);
    for (int i = 0; i <= 360; ++i)
    {
        const float seconds = float(i) / 20.0f;
        const RestHourglassFrame pose = restHourglassFrame(seconds);
        REQUIRE(pose.sandFrame >= 0);
        REQUIRE(pose.sandFrame < 2 * Atlas::framesPerOrientation);
        CHECK(pose.sandFrame == restHourglassFrame(seconds + 180).sandFrame);
    }
    CHECK(restHourglassFrame(-1).sandFrame == 0);
    CHECK(restHourglassFrame(std::numeric_limits<float>::quiet_NaN()).sandFrame == 0);
    // The crop has the same pivot as the frame; padded cells stay inside the atlas.
    CHECK(2 * Atlas::cropX + Atlas::cropWidth == Atlas::canvasWidth);
    CHECK(2 * Atlas::cropY + Atlas::cropHeight == Atlas::canvasHeight);
    CHECK(2 * Atlas::framesPerOrientation <= Atlas::columns * Atlas::rows);
}

TEST_CASE("Obsidian portrait arcs fill upward on opposite sides and preserve stroke thickness")
{
    for (const float amount : {0.0f, 0.001f, 0.25f, 0.5f, 0.75f, 1.0f})
    {
        const auto left = hudArcCrossSection(30.2f, 38.4f, 100 + 160 * amount, 4.6f);
        const auto right = hudArcCrossSection(30.2f, 38.4f, 80 - 160 * amount, 4.6f);
        CHECK(left.innerX == doctest::Approx(-right.innerX));
        CHECK(left.outerX == doctest::Approx(-right.outerX));
        CHECK(left.innerY == doctest::Approx(right.innerY));
        CHECK(left.outerY == doctest::Approx(right.outerY));
        CHECK(std::hypot(left.outerX - left.innerX, left.outerY - left.innerY) == doctest::Approx(4.6f));
        CHECK(left.innerX < 0);
        CHECK(right.innerX > 0);
    }
    const auto emptyEnd = hudArcCrossSection(30.2f, 38.4f, 100, 4.6f);
    const auto fullEnd = hudArcCrossSection(30.2f, 38.4f, 260, 4.6f);
    CHECK(emptyEnd.innerY > 0);
    CHECK(fullEnd.innerY < 0);
}

TEST_CASE("Obsidian arc ranges handle empty tiny full and damage-only intervals")
{
    CHECK(hudArcRange(160, 0, 0).segments == 0);
    CHECK(hudArcRange(160, 0, -1).segments == 0);
    CHECK(hudArcRange(160, 0.8f, 0.2f).segments == 0);
    CHECK(hudArcRange(160, 0, 0.001f).segments == 1);
    CHECK(hudArcRange(-160, 0, 1).segments == 48);
    CHECK(hudArcRange(360, 0, 1).segments == 108);
    const auto full = hudArcRange(160, -1, 2);
    CHECK(full.begin == 0);
    CHECK(full.end == 1);
    CHECK(full.segments == 48);
    const auto damage = hudArcRange(160, 0.25f, 0.5f);
    CHECK(damage.begin == 0.25f);
    CHECK(damage.end == 0.5f);
    CHECK(damage.segments == 12);
    CHECK(hudArcRange(std::numeric_limits<float>::quiet_NaN(), 0, 1).segments == 0);
}

TEST_CASE("Obsidian arc antialiasing retains stroke coverage with a screen pixel fringe")
{
    for (const float stroke : {0.0f, 0.25f, 0.425f, 0.85f, 1.0f, 1.5f, 2.8f, 4.6f, 9.2f, 36.8f})
    {
        const HudArcEdgeProfile edge = hudArcEdgeProfile(stroke);
        CAPTURE(stroke);
        CHECK(edge.outerWidth - edge.coreWidth == doctest::Approx(2.0f));
        // Core coverage plus the two triangular edge ramps equals the requested stroke width.
        CHECK((edge.coreWidth + 1) * edge.coreOpacity == doctest::Approx(stroke));
        CHECK(edge.coreWidth >= 0);
        for (const float angle : {0.0f, 45.0f, 90.0f, 145.0f, 180.0f, 260.0f, 360.0f})
        {
            const HudArcCrossSection outer = hudArcCrossSection(30.2f, 38.4f, angle, edge.outerWidth);
            const HudArcCrossSection core = hudArcCrossSection(30.2f, 38.4f, angle, edge.coreWidth);
            CHECK(std::hypot(outer.outerX - core.outerX, outer.outerY - core.outerY) == doctest::Approx(1.0f));
            CHECK(std::hypot(outer.innerX - core.innerX, outer.innerY - core.innerY) == doctest::Approx(1.0f));
        }
    }
}

TEST_CASE("Obsidian minimap and rest clocks share midnight noon and rounding rules")
{
    CHECK(formatGameplayClock(0) == "12:00 am");
    CHECK(formatGameplayClock(-1) == "12:00 am");
    CHECK(formatGameplayClock(570) == "9:30 am");
    CHECK(formatGameplayClock(719) == "11:59 am");
    CHECK(formatGameplayClock(720) == "12:00 pm");
    CHECK(formatGameplayClock(1439) == "11:59 pm");
    CHECK(formatGameplayClock(1439.6f) == "12:00 am");
    CHECK(formatGameplayClock(1440 + 570) == "9:30 am");
}

TEST_CASE("circular minimap clips crossing lines with both endpoints outside")
{
    float x0 = -20, y0 = 3, x1 = 20, y1 = 3;
    REQUIRE(clipHudLineToCircle(0, 0, 5, x0, y0, x1, y1));
    CHECK(x0 == doctest::Approx(-4));
    CHECK(x1 == doctest::Approx(4));
    CHECK(y0 == 3);
    CHECK(y1 == 3);
    CHECK_FALSE(clipHudLineToCircle(0, 20, 5, x0, y0, x1, y1));
}

TEST_CASE("circular minimap retains interior and degenerate lines and rejects tangents")
{
    float x0 = 1, y0 = 2, x1 = 3, y1 = 2;
    REQUIRE(clipHudLineToCircle(0, 0, 5, x0, y0, x1, y1));
    CHECK(x0 == 1);
    CHECK(x1 == 3);
    x1 = x0;
    CHECK(clipHudLineToCircle(0, 0, 5, x0, y0, x1, y1));
    x0 = -6; x1 = 6; y0 = y1 = 5;
    CHECK_FALSE(clipHudLineToCircle(0, 0, 5, x0, y0, x1, y1));
}

TEST_CASE("Obsidian buffs sort all active effects by expiry with stable ties")
{
    Party party;
    Party::Snapshot snapshot = party.snapshot();
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        snapshot.partyBuffs[i].remainingSeconds = 100 + float(PartyBuffCount - i);
    }
    party.restoreSnapshot(snapshot);
    const auto buffs = sortedGameplayBuffs(party);
    REQUIRE(buffs.size() == PartyBuffCount);
    CHECK(buffs.front() == PartyBuffId::FleetFoot);
    CHECK(buffs.back() == PartyBuffId::TorchLight);
    snapshot.partyBuffs[0].remainingSeconds = 1;
    snapshot.partyBuffs[1].remainingSeconds = 1;
    snapshot.partyBuffs[2].remainingSeconds = 0;
    party.restoreSnapshot(snapshot);
    const auto updated = sortedGameplayBuffs(party);
    REQUIRE(updated.size() == PartyBuffCount - 1);
    CHECK(updated[0] == PartyBuffId::TorchLight);
    CHECK(updated[1] == PartyBuffId::WizardEye);
    CHECK(std::find(updated.begin(), updated.end(), PartyBuffId::FeatherFall) == updated.end());
}

TEST_CASE("Obsidian ordinary party buffs keep their panels or movement indicators even near expiry")
{
    Party party;
    Party::Snapshot snapshot = party.snapshot();
    for (size_t i = 0; i < PartyBuffCount; ++i)
    {
        snapshot.partyBuffs[i].remainingSeconds = 1;
        const GameplayBuffHudDefinition &definition = GameplayBuffHudDefinitions[i];
        if (i == size_t(PartyBuffId::Fly) || i == size_t(PartyBuffId::WaterWalk) || i == size_t(PartyBuffId::Levitate)
            || i == size_t(PartyBuffId::FleetFoot))
        {
            CHECK(definition.presentation == GameplayBuffPresentation::Movement);
            CHECK(gameplayBuffPanelLayoutId(definition.presentation) == nullptr);
        }
        else
        {
            CHECK(gameplayBuffPanelLayoutId(definition.presentation) != nullptr);
        }
        CHECK(definition.pIcon != nullptr);
    }
    party.restoreSnapshot(snapshot);
    CHECK(sortedGameplayBuffs(party).size() == PartyBuffCount);
    CHECK(sortedGameplaySpecialBuffs(party).empty());
    CHECK(gameplayBuffPanelLayoutId(GameplayBuffPresentation::Special) == nullptr);
}

TEST_CASE("Obsidian movement indicators line up Fly, Levitate, Water Walk and Fleet Foot")
{
    const auto buffs = [](const Party &party)
    {
        std::vector<PartyBuffId> result;
        for (const GameplayMovementIndicator &indicator : gameplayMovementIndicators(party))
        {
            result.push_back(indicator.buff);
        }
        return result;
    };
    Party party;
    CHECK(buffs(party).empty());
    Party::Snapshot snapshot = party.snapshot();
    snapshot.partyBuffs[size_t(PartyBuffId::Levitate)].remainingSeconds = 60;
    snapshot.partyBuffs[size_t(PartyBuffId::WaterWalk)].remainingSeconds = 60;
    snapshot.partyBuffs[size_t(PartyBuffId::WaterWalk)].spellId = spellIdValue(SpellId::Levitate);
    party.restoreSnapshot(snapshot);
    // Levitate's own Water Walk shows only as Levitate.
    CHECK(buffs(party) == std::vector<PartyBuffId>{PartyBuffId::Levitate});
    snapshot.partyBuffs[size_t(PartyBuffId::Fly)].remainingSeconds = 60;
    snapshot.partyBuffs[size_t(PartyBuffId::WaterWalk)].spellId = spellIdValue(SpellId::WaterWalk);
    snapshot.partyBuffs[size_t(PartyBuffId::FleetFoot)].remainingSeconds = 60;
    party.restoreSnapshot(snapshot);
    CHECK(buffs(party) == std::vector<PartyBuffId>{
        PartyBuffId::Fly, PartyBuffId::Levitate, PartyBuffId::WaterWalk, PartyBuffId::FleetFoot});
}

TEST_CASE("Obsidian vertical meters and damage trails remain anchored at the bottom")
{
    const GameplayResolvedHudLayoutElement track = {10, 20, 5, 60, 1};
    const auto half = GameplayUiSkin::meterSegment(track, 0, 0.5f, true);
    CHECK(half.x == 10);
    CHECK(half.y == 50);
    CHECK(half.width == 5);
    CHECK(half.height == 30);
    const auto trail = GameplayUiSkin::meterSegment(track, 0.25f, 0.5f, true);
    CHECK(trail.y == half.y);
    CHECK(trail.height == 15);
    CHECK(GameplayUiSkin::meterSegment(track, 0, 0, true).height == 0);
    CHECK(GameplayUiSkin::meterSegment(track, 0, 2, true).y == track.y);
    CHECK(GameplayUiSkin::meterSegment(track, 0.8f, 0.1f, true).height == 0);
    const auto horizontal = GameplayUiSkin::meterSegment({10, 20, 60, 5, 1}, 0, 0.5f, false);
    CHECK(horizontal.x == 10);
    CHECK(horizontal.width == 30);
    CHECK(horizontal.height == 5);
}

TEST_CASE("Obsidian skull effects retain the legacy desktop spell meanings")
{
    const auto definition = [](PartyBuffId id) -> const GameplayBuffHudDefinition &
    {
        return GameplayBuffHudDefinitions[size_t(id)];
    };
    CHECK(definition(PartyBuffId::TorchLight).pLayer == &GameplayBuffHudTorch);
    CHECK(definition(PartyBuffId::WizardEye).pLayer == &GameplayBuffHudNearEye);
    CHECK(definition(PartyBuffId::FeatherFall).pLayer == &GameplayBuffHudClouds);
    CHECK(definition(PartyBuffId::Stoneskin).pLayer == &GameplayBuffHudStone);
    CHECK(definition(PartyBuffId::DayOfGods).pLayer == &GameplayBuffHudHalo);
    CHECK(definition(PartyBuffId::ProtectionFromMagic).pLayer == &GameplayBuffHudGarland);
    CHECK(definition(PartyBuffId::Stoneskin).presentation == GameplayBuffPresentation::Skull);
    CHECK(GameplayBuffHudTorch.pass == GameplayBuffHudLayerPass::Underlay);
    CHECK(GameplayBuffHudClouds.pass == GameplayBuffHudLayerPass::Underlay);
    CHECK(GameplayBuffHudStone.pass == GameplayBuffHudLayerPass::Base);
    CHECK(definition(PartyBuffId::Fly).pLayer == nullptr);
    CHECK(definition(PartyBuffId::WaterWalk).pLayer == nullptr);
    CHECK(definition(PartyBuffId::Invisibility).pLayer == nullptr);
    CHECK_FALSE(definition(PartyBuffId::Invisibility).cornerBadge);
    CHECK(definition(PartyBuffId::DetectLife).pLayer == &GameplayBuffHudFarEye);
}

TEST_CASE("Obsidian atlas regions and corner badges stay inside their panels")
{
    for (const GameplayBuffHudDefinition &definition : GameplayBuffHudDefinitions)
    {
        CAPTURE(definition.pName);
        if (definition.pLayer != nullptr)
        {
            const GameplayBuffHudLayer &layer = *definition.pLayer;
            CHECK(layer.uv.x >= 0);
            CHECK(layer.uv.y >= 0);
            CHECK(layer.uv.width > 0);
            CHECK(layer.uv.height > 0);
            CHECK(layer.uv.x + layer.uv.width <= 1);
            CHECK(layer.uv.y + layer.uv.height <= 1);
            CHECK(layer.placement.x >= 0);
            CHECK(layer.placement.y >= 0);
            CHECK(layer.placement.width > 0);
            CHECK(layer.placement.height > 0);
            CHECK(layer.placement.x + layer.placement.width <= 128);
            CHECK(layer.placement.y + layer.placement.height <= 128);
        }
        else
        {
            CHECK(definition.badgeX >= 0);
            CHECK(definition.badgeY >= 0);
            CHECK(definition.badgeX + 12 <= 60);
            CHECK(definition.badgeY + 12 <= 60);
        }
    }
}

TEST_CASE("Obsidian health bands follow the 66 and 33 percent thresholds")
{
    using GameplayUiSkin::HealthBand;
    CHECK(GameplayUiSkin::healthBand(1.0f) == HealthBand::High);
    CHECK(GameplayUiSkin::healthBand(0.66f) == HealthBand::High);
    CHECK(GameplayUiSkin::healthBand(0.659f) == HealthBand::Middle);
    CHECK(GameplayUiSkin::healthBand(0.5f) == HealthBand::Middle);
    CHECK(GameplayUiSkin::healthBand(0.331f) == HealthBand::Middle);
    CHECK(GameplayUiSkin::healthBand(0.33f) == HealthBand::Low);
    CHECK(GameplayUiSkin::healthBand(0.2f) == HealthBand::Low);
    CHECK(GameplayUiSkin::healthBand(0.0f) == HealthBand::Low);
}

TEST_CASE("Portrait counter gems light per point, half for half a point, and lap past their count")
{
    using OpenYAMM::Game::PortraitCounter;
    using OpenYAMM::Game::PortraitCounterKind;
    using OpenYAMM::Game::PortraitGemFill;
    using OpenYAMM::Game::portraitGemFills;

    PortraitCounter combo;
    combo.kind = PortraitCounterKind::ComboPoints;
    combo.pips = 5;
    combo.amount = 3.5;
    const std::vector<PortraitGemFill> half = portraitGemFills(combo);
    REQUIRE_EQ(half.size(), 5);
    CHECK_EQ(half[2], PortraitGemFill{1, false});
    CHECK_EQ(half[3], PortraitGemFill{0.5f, false});
    CHECK_EQ(half[4], PortraitGemFill{0, false});
    combo.amount = 5;
    CHECK_EQ(portraitGemFills(combo)[4], PortraitGemFill{1, false});

    PortraitCounter stacks;
    stacks.kind = PortraitCounterKind::Stacks;
    stacks.pips = 10;
    stacks.amount = 7;
    CHECK_EQ(portraitGemFills(stacks)[6], PortraitGemFill{1, false});
    CHECK_EQ(portraitGemFills(stacks)[7], PortraitGemFill{0, false});
    stacks.amount = 10;
    CHECK_EQ(portraitGemFills(stacks)[9], PortraitGemFill{1, false});
    // Past ten every gem stays lit and the first four turn pale gold.
    stacks.amount = 14;
    const std::vector<PortraitGemFill> lap = portraitGemFills(stacks);
    CHECK_EQ(lap[3], PortraitGemFill{1, true});
    CHECK_EQ(lap[4], PortraitGemFill{1, false});
    CHECK_EQ(lap[9], PortraitGemFill{1, false});
    stacks.amount = 25;
    CHECK_EQ(portraitGemFills(stacks)[9], PortraitGemFill{1, true});

    CHECK(portraitGemFills(PortraitCounter{}).empty());
}

TEST_CASE("Portrait counter gems hug the HP arc and stay on their own side of the gap between portraits")
{
    // ObsidianPcN: the HP arc's centre line is 60.4 x 76.8 around the slot's x 39, stroke 4.6; slots are 80 apart,
    // so this HP arc's outer edge is at x -32.5 from this centre and the left neighbour's mana arc ends at
    // -80 + 30.2 + 2.3 = -47.5: the gems stay right of the middle, -40.
    for (int pips : {5, 10})
    {
        const std::vector<OpenYAMM::Game::PortraitGemPlace> places =
            OpenYAMM::Game::portraitGemPlaces(pips, 0, 0, 30.2f, 38.4f, 4.6f);
        REQUIRE_EQ(places.size(), size_t(pips));
        for (const OpenYAMM::Game::PortraitGemPlace &place : places)
        {
            CHECK_GT(place.x - place.radius, -40.0f);
            CHECK_LT(place.x + place.radius, 0.0f);
            // Clear of the HP arc's outer edge: outside the ellipse grown by half the stroke.
            const float inner = std::hypot(place.x / (30.2f + 2.3f), place.y / (38.4f + 2.3f));
            const float reach = 1 + place.radius / 40.7f;
            CHECK_GT(inner, reach * 0.99f);
        }
        CHECK_GT(places.front().y, places.back().y);
    }
}
