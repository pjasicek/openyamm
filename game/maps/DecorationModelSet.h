#pragma once

#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelAnimation.h"
#include "engine/render/ModelRenderer.h"
#include "game/fx/TalkPortraitFrame.h"
#include "game/maps/DecorationModelPlacement.h"

#include <cstddef>
#include <cstdint>
#include <array>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace YAML
{
class Node;
}

namespace OpenYAMM::Game
{
struct DecorationBillboard;
struct DecorationBillboardSet;

// Map decorations drawn as static 3D models, bound by decoration name in engine/models/decorations.yml (outdoor maps)
// or indoor_decorations.yml (BLV maps; apart because decorations.yml is an outdoor bake dependency), which a world
// extends with its own worlds/<world>/models/ manifests (DecorationModelManifest). A map loads the models of the
// decorations it places, their lit/unlit counterparts and its events' SetSprite targets.
// A decoration keeps its native data (collision, events, picking); the sprite it currently shows selects the model, so
// an event SetSprite to another bound decoration (a picked food tree) switches models, and a switch to an unbound
// sprite draws that sprite instead. decoration_overlays.yml adds state overlays: one more model drawn with a bound
// decoration's placement, chosen by its interactive state (the liquid of a stat barrel, gone once it is drunk).
// Animated decorations (evt.PlayDecorationClip, a binding's idle clip):
// - parts (`parts: [<model>, ...]`): moving rigid pieces drawn with the decoration (a coffin's lid, a bell's clapper),
//   each authored in the decoration's asset space on one mesh node that its own clips move;
// - a binding model with clips on its one rigid mesh node moves as a whole (a windmill's sails);
// - `animated: <model>`: a skinned copy of the model (a banner, a statue from a creature model) drawn as a model
//   instance in the binding model's place, posed by its clips (poseInstances); the binding model stays for picking.
class DecorationModelSet
{
public:
    // The wall a decoration (of the given world height) hangs on, if any; indoor maps supply it for mount: wall.
    using WallFinder = std::function<std::optional<DecorationWallContact>(const DecorationBillboard &, float height)>;

    // A map without bound decorations loads empty. False with an error for an invalid manifest or model.
    bool load(const Engine::AssetFileSystem &assets, const std::string &worldId, const std::string &mapFile,
        const DecorationBillboardSet &decorations, std::string &error, WallFinder wallFinder = {});
    void clear();
    bool empty() const
    {
        return m_bindings.empty();
    }
    // Event state of every decoration billboard: the sprite it shows now (0 = none), whether it is hidden and its
    // interactive decoration state (-1 = none). Moves placements between models when the shown sprite or state
    // changes and sets placement visibility.
    using ShownSprite = std::function<uint16_t(size_t billboardIndex, bool &hidden, int &state)>;
    void update(const std::vector<DecorationBillboard> &billboards, const ShownSprite &shownSprite);
    // True when a model draws this sprite (its billboard must not be drawn).
    bool modelsSprite(uint16_t spriteId) const
    {
        return m_bindingBySprite.contains(spriteId);
    }
    std::vector<Engine::ModelStaticGroup> &groups()
    {
        return m_groups;
    }
    const std::vector<Engine::ModelStaticGroup> &groups() const
    {
        return m_groups;
    }
    // Whether a model currently draws this billboard (hover and interaction then pick the model, not the sprite).
    bool drawsBillboard(size_t billboardIndex) const
    {
        return billboardIndex < m_slots.size() && m_slots[billboardIndex].group >= 0;
    }
    // Ray against the model a billboard currently shows (its LOD1 triangles, or LOD0 for a model without LODs).
    // distance is the ray parameter (world units for a unit direction). False when nothing is hit or no model draws
    // the billboard; alpha-tested cards count as solid, so a tree crown picks as a whole. Camera-facing cards (flames)
    // are turned toward the ray's origin, where the camera sees them.
    bool raycast(size_t billboardIndex, const std::array<float, 3> &origin, const std::array<float, 3> &direction,
        float &distance) const;
    // Swings the swinging placements (chandeliers, cages) to their pose at timeSeconds, and moves the placements
    // turning into a turn_in model's pose.
    void animate(float timeSeconds);
    // Turns a placed decoration by yawRadians about its origin from its rest pose, pulls it back `back` world units
    // along its front (asset +z) and moves it by offset: an aimed gun and its recoil, a sailing boat
    // (EventRuntimeState::decorationAims).
    void pose(size_t billboardIndex, float yawRadians, float back, const std::array<float, 3> &offset = {});
    // Poses every billboard whose sprite override key aimed answers for (its yaw, pull-back and offset).
    using Aimed = std::function<bool(uint32_t spriteOverrideKey, float &yawRadians, float &back,
        std::array<float, 3> &offset)>;
    void poseAimed(const std::vector<DecorationBillboard> &billboards, const Aimed &aimed);
    // Moves every part with its decoration and poses it by the clip `clip` answers for the decoration's sprite
    // override key (its name, time and whether it loops; past its end a clip that does not loop holds its last
    // frame; rest pose without one, or for a clip its part lacks). Call after the decorations are posed (animate,
    // poseAimed).
    // Without a scripted clip a binding's idle clip loops (timeSeconds: animate()'s clock).
    using PartClip = std::function<bool(uint32_t spriteOverrideKey, std::string &clipName, float &seconds,
        bool &loop)>;
    void poseParts(const std::vector<DecorationBillboard> &billboards, const PartClip &clip, float timeSeconds);
    // A binding's use_clips: each new use of a decoration (uses: its count by sprite override key) starts the next
    // clip of the list (a book: open, turn a page, turn back, close). Call before poseParts.
    using UseCount = std::function<uint32_t(uint32_t spriteOverrideKey)>;
    void noteUses(const std::vector<DecorationBillboard> &billboards, const UseCount &uses, float timeSeconds);
    // Draws each `animated` binding's placements as instances in models (created here, hidden with their decoration)
    // posed like the parts; their static placements stay for picking only. Call after poseParts.
    void poseInstances(const std::vector<DecorationBillboard> &billboards, const PartClip &clip, float timeSeconds,
        Engine::ModelInstanceSystem &models);
    // Billboards of wall-mounted bindings without a wall in reach or a free_model; they keep their map facing.
    const std::vector<size_t> &unmountedBillboards() const
    {
        return m_unmountedBillboards;
    }
    // Billboard index of each placement of a group.
    const std::vector<size_t> &billboardIndices(size_t group) const
    {
        return m_billboardIndices[group];
    }
    // The model the decoration with this sprite override key shows now (a posed talking prop's talk portrait,
    // ActorModelPreview::renderDecoration): its binding's model, variant, yaw and scale. None when no model draws it
    // or several decorations share the key.
    std::optional<DecorationPortraitModel> portraitModel(const std::vector<DecorationBillboard> &billboards,
        uint32_t spriteOverrideKey) const;
    // Whether a group draws state overlays (never picked or outlined; the decoration's own model is).
    bool overlayGroup(size_t group) const
    {
        return m_bindings[group].overlay;
    }

private:
    struct Binding
    {
        std::shared_ptr<const Engine::ModelAsset> asset;
        float height = 0.0f;
        float heightJitter = 0.0f;
        bool randomYaw = true;
        float yawOffset = 0.0f;
        float zOffset = 0.0f;
        std::array<float, 3> lodPixels = Engine::ModelLodPixels;
        // variant: the glTF material variant (KHR_materials_variants) it draws, one GLB serving several colours;
        // 0 is the default material.
        uint32_t materialVariant = 0;
        // mount: wall turns the model's back (asset -z) onto the nearest wall face; free_model (its own binding,
        // drawn into its own group) stands where no wall is in reach.
        bool mountWall = false;
        int32_t freeBinding = -1;
        // swing: [angle degrees, period seconds] about the asset x axis through the model's top.
        float swingRadians = 0.0f;
        float swingPeriod = 0.0f;
        // turn_in: [angle degrees, seconds]. A placement an event switches to this model during play turns into its
        // pose by that angle about the asset z axis (a valve wheel's axle) through the model's centre; one placed at
        // load, or swapped before the first update, simply stands in it.
        float turnRadians = 0.0f;
        float turnSeconds = 0.0f;
        // State overlays: the overlay binding drawn for each interactive state (-1 = none). An overlay binding is
        // authored in its decoration's asset space and takes the decoration's placement matrix.
        std::vector<int32_t> stateOverlays;
        bool overlay = false;
        // parts: the bindings of its moving parts. A part binding, or a binding whose own model moves (selfAnimated),
        // records its moving mesh node and the inverse of that node's rest matrix (asset space).
        std::vector<int32_t> parts;
        bool selfAnimated = false;
        uint32_t partNode = 0;
        Engine::ModelMatrix partRestInverse = {};
        // idle: the clip looped while no script plays one (on its parts, its own model, its animated copy).
        std::string idleClip;
        // use_clips: the clips each use steps through (held at their ends).
        std::vector<std::string> useClips;
        // animated: the skinned copy drawn as an instance.
        std::shared_ptr<const Engine::ModelAsset> animatedAsset;
        // Pick triangles in asset space (three corners each), from LOD1 or LOD0; camera-facing cards apart.
        std::vector<std::array<float, 3>> pickTriangles;
        std::vector<std::array<float, 3>> billboardPickTriangles;
        // For each corner of billboardPickTriangles, the asset point its card turns about.
        std::vector<std::array<float, 3>> billboardPickPivots;
    };
    // Where a billboard's placement lives; group -1 when no model draws it. binding is the binding its sprite
    // selects (group is that binding's free-standing group when no wall was in reach).
    struct Slot
    {
        int32_t group = -1;
        int32_t binding = -1;
        uint32_t index = 0;
        uint16_t sprite = 0;
        int32_t overlayGroup = -1;
        uint32_t overlayIndex = 0;
        int32_t state = -1;
        // Its parts' placements: (group, index) of each.
        std::vector<std::pair<int32_t, uint32_t>> parts;
        bool hidden = false;
        // Its animated copy's instance and the clip it was last posed in (empty: rest).
        std::optional<Engine::ModelInstanceHandle> instance;
        std::string instanceClip;
        // The clip time it was last posed at: a held clip (its end) or rest is not sampled again.
        float instanceSeconds = -1.0f;
        // Its use_clips: the uses seen, the clip playing (-1: none) and when it started (animate()'s clock).
        uint32_t uses = 0;
        int32_t useClip = -1;
        float useStart = 0.0f;
        // A turn in progress (turn_in): its start in animate()'s time, negative until its first animate.
        bool turning = false;
        float turnStart = -1.0f;
    };

    // Ray against the placement's rigid (not camera-facing) triangles; lowers best on a nearer hit.
    bool rigidHit(const Slot &slot, const std::array<float, 3> &origin, const std::array<float, 3> &direction,
        float &best) const;
    Engine::ModelStaticPlacement placementFor(const Binding &binding, const DecorationBillboard &billboard,
        const std::optional<DecorationWallContact> &wall) const;
    static float heightJitter(const Binding &binding, const DecorationBillboard &billboard);
    void place(size_t billboardIndex, const DecorationBillboard &billboard, uint32_t binding);
    void unplace(size_t billboardIndex);
    bool loadStateOverlays(const Engine::AssetFileSystem &assets, const std::string &worldId,
        const std::unordered_map<std::string, uint32_t> &bindingByName, std::string &error);
    // Places or removes the billboard's state overlay to match its binding and state.
    void placeOverlay(size_t billboardIndex);
    void unplaceOverlay(size_t billboardIndex);
    // Places or removes the moving part of the billboard's binding.
    void placePart(size_t billboardIndex);
    void unplacePart(size_t billboardIndex);
    bool loadParts(const Engine::AssetFileSystem &assets, const YAML::Node &entry, const std::string &name,
        uint32_t served, std::string &error);
    // Records the binding's one rigid mesh node and the inverse of its rest matrix; false (error) without one.
    static bool rigidMovingNode(Binding &binding, std::string &error);
    // The clip a placement plays now: the scripted one if its asset has it, else its use clip, else its idle clip;
    // false for rest.
    bool resolveClip(const Binding &binding, const Engine::ModelAsset &asset, const DecorationBillboard *pBillboard,
        const Slot *pSlot, const PartClip &clip, float timeSeconds, uint32_t &clipIndex, float &seconds) const;
    // A clip's pose of the moving node relative to its rest (asset space).
    Engine::ModelMatrix clipDelta(const Binding &moving, uint32_t clipIndex, float seconds);
    // Swap-removes a placement from a group; returns the billboard whose placement moved into its index, if any.
    std::optional<size_t> removePlacement(size_t group, uint32_t index);

    Engine::ModelAssetCache m_assets;
    // Binding i draws into group i.
    std::vector<Binding> m_bindings;
    std::unordered_map<uint16_t, uint32_t> m_bindingBySprite;
    std::vector<Engine::ModelStaticGroup> m_groups;
    std::vector<std::vector<size_t>> m_billboardIndices;
    // Unswung placement matrix of each placement, aligned with the group's placements.
    std::vector<std::vector<Engine::ModelMatrix>> m_restMatrices;
    std::vector<Slot> m_slots;
    WallFinder m_wallFinder;
    std::vector<size_t> m_unmountedBillboards;
    // Groups of swinging bindings, and of moving parts.
    std::vector<uint32_t> m_swingingGroups;
    std::vector<uint32_t> m_partGroups;
    // Groups of bindings whose own model moves, and of bindings drawn by animated instances.
    std::vector<uint32_t> m_selfAnimatedGroups;
    std::vector<uint32_t> m_animatedGroups;
    std::vector<uint32_t> m_useGroups;
    // Scratch pose for sampling part clips.
    Engine::ModelPose m_partPose;
    // Billboards turning into a turn_in model's pose; m_settled once the first update has placed the map's state.
    std::vector<size_t> m_turningBillboards;
    bool m_settled = false;
};
}
