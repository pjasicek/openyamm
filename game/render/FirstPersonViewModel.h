#pragma once

#include "engine/models/GltfModelLoader.h"
#include "engine/models/ModelInstance.h"
#include "game/render/FirstPersonViewModelFx.h"
#include "game/render/HeldWeapons.h"

#include <bgfx/bgfx.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class ModelRenderer;
struct ModelRenderLighting;
}

namespace OpenYAMM::Game
{
// Prototype first-person view model: arms holding the active member's weapon (and shield), drawn over the finished
// world from their own eye (the model's Camera01 node) with their own projection and depth, so they never clip into
// walls (FirstPersonViewModelView). The arms are the engine's engine/view_model/arms.glb, or a self-contained GLB on
// disk named by [debug] view_model_path; the weapons are GLBs beside it (w_<name>.glb, s_<name>.glb for shields) in
// the space of the node they hang on, and
// <arms>.textkeys.json holds each clip's text keys (Hit: the blow). The bow is its own animated model (w_bow.glb:
// its string a morph, the nocked arrow on its ArrowBone) on the left hand's Torch node, playing the arms' clip of the
// same name. The clip names are those of the private Oblivion proof of concept (reference/oblivion_poc/README.md):
// <set><action>, the set from the weapon (onehand, twohand, staff, bow, handtohand; dual, crossbow and pole are baked
// into the arms by their level_generation projects).
class FirstPersonViewModel
{
public:
    enum class WeaponSet
    {
        HandToHand,
        OneHand,
        TwoHand,
        Staff,
        Bow,
        // A melee weapon in each hand (dual wielding): the dual* clips baked from the one-handed set, the right arm's
        // swings mirrored onto the left (level_generation/props/items_claude/dual_wield_20261114).
        Dual,
        // A crossbow (held.yml kind crossbow) in both hands, the stock in the right hand's Weapon node: the crossbow*
        // clips baked into the arms (level_generation/props/items_claude/crossbow_set_20261114). Shoots like the bow.
        Crossbow,
        // A dragon's clawed forelegs: their own model (engine/view_model/dragon_forelegs.glb, claws* clips), no weapon
        // or shield. Rakes right and left, the fifth blow a bite, the breath at range (devdocs/solo_action/DRAGON.md).
        Claws,
        // A pole weapon (held.yml kind spear, trident, polearm or poleaxe) in both hands, low with its head in view:
        // the pole* clips baked into the arms (level_generation/props/items_claude/pole_set_20261114). Arms without
        // them play the two-handed clips.
        Pole,
    };

    // What the arms hold: an animation set, a weapon model (empty: bare hands) and whether a shield is carried.
    struct Kit
    {
        WeaponSet set = WeaponSet::HandToHand;
        std::string weapon;
        bool shield = false;
        // Our own ground item models held instead of Oblivion's templates (a solo run): the asset path and icon of the
        // weapon (or bow) and of the shield; empty, or an icon without a grip in held.yml, keeps the template.
        std::string heldModel;
        std::string heldIcon;
        std::string shieldModel;
        std::string shieldIcon;
        // The skin tier of the weapon (or bow) template and of the shield template (heldSkinTier; 0: the template
        // itself): w_<name>_t<tier>.glb beside the template when it exists.
        uint8_t weaponTier = 0;
        uint8_t shieldTier = 0;
        // Dual wielding: the off hand's template, our model and icon, and its skin tier, held in the left hand's
        // OffHandWeapon node (the Weapon node mirrored). heavy: a two-handed weapon held in one hand (a MAW Minotaur's
        // axes), whose swings may play slower than Oblivion's own pace.
        std::string offWeapon;
        std::string offHeldModel;
        std::string offHeldIcon;
        uint8_t offTier = 0;
        bool heavy = false;

        bool operator==(const Kit &) const = default;
    };

    enum class Action
    {
        Melee,
        Shot,
        Cast,
    };

    struct Input
    {
        float deltaSeconds = 0.0f;
        float partyX = 0.0f;
        float partyY = 0.0f;
        float yawRadians = 0.0f;
        bool blockHeld = false;
        Kit kit;
        // A swing gameplay started and waits on (its blow is reported in Output), and the member's melee recovery
        // when it started: the swing plays fast enough to reach its chain point when the recovery ends.
        uint32_t swingSerial = 0;
        float swingRecoverySeconds = 0.0f;
        // Another attack action or a cast, shown when it happens.
        uint32_t actionSerial = 0;
        Action action = Action::Melee;
        uint32_t shieldBlockSerial = 0;
        // The active member's remaining recovery, for the trace only.
        float memberRecoverySeconds = 0.0f;
        // A solo run's talent to show (cleave, whirlwind, charge, volley, blink ...) and whether Shield Wall holds the
        // block pose.
        uint32_t talentSerial = 0;
        std::string talentClip;
        bool talentBlock = false;
        // The waited action (swingSerial) is a cast: a cast clip fitted to swingRecoverySeconds plays instead of a
        // swing, its release reported as the blow; castSelf picks the self clip. castColor tints the casting hand.
        bool swingIsCast = false;
        // The waited action is a dragon's breath: the breath clip fitted to swingRecoverySeconds, its Hit the blow,
        // the mouth (castHandScreen) where it leaves.
        bool swingIsBreath = false;
        bool castSelf = false;
        std::array<float, 3> castColor = {0.85f, 0.8f, 1.0f};
        // The weapon trail ([gameplay] weapon_trails) and its colour (the weapon's element, else steel).
        bool trailEnabled = true;
        std::array<float, 3> trailColor = {0.82f, 0.88f, 1.0f};
        float trailIntensity = 0.5f;
    };

    struct Output
    {
        // Arms are shown: gameplay lets attacks wait for the swing's blow (a bow's: the arrow's release).
        bool meleeSwings = false;
        // The swing gameplay waits on reached its blow this update, with the blade's direction across the screen.
        bool blowReleased = false;
        std::optional<std::array<float, 2>> blowDirection;
        // A shield is held up (block with a shield, no swing under way).
        bool shieldRaised = false;
        // While a cast gathers or leaves: its casting palm on screen (normalized device x right, y up), where gameplay
        // starts the spell's missile.
        std::optional<std::array<float, 2>> castHandScreen;
    };

    // The kit for a main-hand weapon's skill group (empty: none) and whether it is wielded two-handed.
    static Kit kitFor(const std::string &skillGroup, bool twoHanded, bool shield);
    // The kit for both hands: a melee weapon in each (both dualWieldable, the main one not wielded two-handed) is the
    // Dual kit; anything else in the off hand is kitFor's (a shield on the arm, nothing else shown). large: the item's
    // table type is two-handed (Weapon2), as a Minotaur's one-handed battle axe: the larger template, and heavy when
    // either hand holds one.
    static Kit kitForHands(const std::string &mainSkillGroup, bool mainTwoHanded, bool mainLarge,
        const std::string &offSkillGroup, bool offLarge);
    // The kit for the drawn bow by its held.yml kind: a crossbow's own two-handed set, any other bow the bow set.
    static Kit kitForBow(const std::string &heldKind);
    // A pole weapon's held.yml kind: spear, trident, polearm or poleaxe (a staff is not one).
    static bool poleKind(const std::string &heldKind);
    // kitForHands' kit by the main-hand item's held.yml kind: a pole weapon not dual wielded holds both hands on its
    // shaft (the Pole set, no shield); any other kind, or a Dual kit, is returned unchanged.
    static Kit kitForHeldKind(const Kit &kit, const std::string &mainHeldKind);
    // A dragon's kit (ClassRules::isDragon; MAW by the portrait's race): the clawed forelegs, no weapon or shield.
    static Kit dragonKit();
    // The engine's model for a kit: the dragon's forelegs for the claws, the arms for everything else.
    static std::string packagedModelPath(const Kit &kit);
    // The claws' blow for a combo step (as comboAction): right and left rakes as the chain keys hand on, the fifth
    // blow of each round the bite (the power attack's slot).
    static std::string clawsAction(uint32_t step, char side);
    // Skill groups the arms swing in either hand: swords, daggers, axes, maces and clubs (a halberd is a Spear item and
    // keeps the main hand's kit).
    static bool dualWieldable(const std::string &skillGroup);
    // The combo's action for a blow (the clip without its set prefix): step counts the blows of a round of five
    // (right, left, right chop, left chop, then a power attack by the direction of movement: forward and left are the
    // party's speed along and across the view; standing, the dual set's is the cross slash), side is where the last
    // blow handed on (its chain key). FirstPersonViewModelKit.cpp, with kitFor and kitForHands.
    static std::string comboAction(uint32_t step, char side, float forward, float left);

    // Loads the arms the first time a path is given; false (reported once) when they cannot be used. With pAssets the
    // path is a virtual one in the mounted packages (the engine's arms), else a file on disk ([debug] view_model_path).
    bool ensureLoaded(const std::string &path, const Engine::AssetFileSystem *pAssets = nullptr);
    // This view model takes over from the other one (a dragon's forelegs and the arms, as the active member changes
    // or a game loads): no action carried over, the serials read afresh, and the equip clip brings it into view.
    void resume();
    Output update(const Input &input);
    // Draws into target (invalid: the backbuffer) over a width x height world, lit by the world's light at the eye
    // (pScene: directions in world space, point lights relative to the eye; null: a fixed studio light) turned with
    // the camera (yaw, pitch), so the arms take the sun, sky, room and nearby lights as a creature there would.
    void render(Engine::ModelRenderer &renderer, bgfx::FrameBufferHandle target, uint16_t width, uint16_t height,
        const Engine::ModelRenderLighting *pScene, float yawRadians, float pitchRadians);
    void shutdown();

    // Debug console (`viewmodel`): hold one clip at one time, override the kit, list the clips.
    bool holdPose(const std::string &clip, float seconds);
    void releasePose();
    void overrideKit(std::optional<Kit> kit);
    // Where our item models and held.yml are read from; none: only Oblivion's templates are held.
    void setHeldAssets(const Engine::AssetFileSystem *pAssets);
    // Debug console (`viewmodel weapons oblivion|ours`): the templates (the default) for the kinds held_tiers.yml
    // gives them, our ground models for the rest; or our model wherever held.yml grips it.
    void useTemplateWeapons(bool templates);
    // The held.yml kind of an icon (sword, bow, crossbow ...); empty without a row.
    std::string heldKind(const std::string &icon);
    // The skin tier for an item (held_tiers.yml, read from the held assets); 0 while the rules are unreadable.
    uint8_t skinTier(const HeldSkinItem &item);
    // Debug console (`viewmodel tier <n|auto>`): every template drawn in one skin tier.
    void forceSkinTier(std::optional<uint8_t> tier);
    std::string clipList() const;
    // The screen path of one clip with the current kit: per sample its time and the blade tip, the hilt (the weapon
    // node) and the left hand in normalised device coordinates of the arms' own camera, as JSON. Leaves the pose at
    // the clip's end; the next update blends back.
    std::string pathJson(const std::string &clipName, int samples);
    // Prints each swing's clip, rate and blow time to stdout (`viewmodel trace on`).
    void setTrace(bool trace) { m_trace = trace; }
    // A held pose (holdPose) shows the casting glow in this colour on the clip's casting hands (`viewmodel fx`), and
    // its weapon trail as if the clip were playing.
    void setFxPreview(std::optional<std::array<float, 3>> castColor) { m_fxPreview = castColor; }
    // The colours of a spell school (Fire, Air ... Dark; anything else a neutral arcane) and of a weapon element
    // (MeleeWeaponElement: 0 steel, then Fire, Air, Water, Body, Light, Dark).
    static std::array<float, 3> schoolColor(const std::string &school);
    static std::array<float, 3> elementColor(uint8_t element);

private:
    // A clip and the Oblivion text keys the arms follow (-1: none).
    struct ClipInfo
    {
        uint32_t index = UINT32_MAX;
        float duration = 0.0f;
        // Hit: a swing's blow, a cast's release; a bow shot's Release.
        float hitSeconds = -1.0f;
        // a:L / a:R: from here a further attack chains into the left (or right) swing instead of returning to idle.
        float chainSeconds = -1.0f;
        char chainSide = 0;
        // Blend: N: the crossfade into the clip, N frames at 30 per second.
        float blendSeconds = -1.0f;
        // Attach: an equip clip's weapon reaches the hand.
        float attachSeconds = -1.0f;
    };

    std::optional<ClipInfo> clip(const std::string &name) const;
    std::optional<ClipInfo> setClip(const char *pAction) const;
    std::shared_ptr<const Engine::ModelAsset> attachment(const std::string &file);
    // A template in a skin tier (the forced tier first): its _t<tier> file when it exists, else the template.
    std::shared_ptr<const Engine::ModelAsset> skinAttachment(const std::string &file, uint8_t tier);
    const HeldSkinRules &skinRules();
    // Our item model by asset path, cached; null when it cannot be loaded.
    std::shared_ptr<const Engine::ModelAsset> heldAsset(const std::string &path);
    // The held.yml row of an icon (the table read on first use); null without one.
    const HeldWeaponGrip *heldGrip(const std::string &icon);
    // Our model and its placement for an icon, when the table grips it and the model loads.
    std::optional<Engine::ModelAttachment> heldAttachment(const std::string &path, const std::string &icon,
        uint32_t node, const HeldWeaponGrip **ppGrip);
    // The template an item draws: its held.yml kind's own (held_tiers.yml kind_templates: spears, tridents, halberds,
    // crossbows, wands, blasters, clubs) with that template's tier cap applied to tier, else weaponFile.
    std::string kindTemplate(const std::string &icon, const std::string &weaponFile, uint8_t &tier);
    void applyKit(const Kit &kit, bool weaponInHand);
    // One hand's weapon on its node (our model where held.yml grips it, else the template in its skin tier), and the
    // blade's tip in that node's space.
    void holdWeapon(const std::string &heldModel, const std::string &heldIcon, const std::string &weaponFile,
        uint8_t tier, uint32_t node, std::vector<Engine::ModelAttachment> &attachments, std::array<float, 3> &bladeTip);
    // The crossbow on the Weapon node: our ground model where held.yml grips it (its Crossbow mount closes on the
    // foregrip, the Torch frame, carried at m_crossbowGrip), else the template.
    void holdCrossbow(const Kit &kit, std::vector<Engine::ModelAttachment> &attachments);
    void startAction(const ClipInfo &info, bool waitsForBlow, float rate = 1.0f);
    // The next swing of the combo: the side the running swing chains to, a chop every second round, and a power
    // attack (by the movement direction) to close the round.
    std::optional<ClipInfo> nextSwing(char side, float forward, float left);
    // Starts a talent's clips (Whirlwind: two sweeps back to back).
    void startTalent(const std::string &talent, const Kit &kit);
    std::optional<std::array<float, 2>> bladeScreenPoint(bool offHand = false) const;
    // The arms have the dual clips and the OffHandWeapon node; without them a Dual kit is shown as OneHand.
    bool dualReady() const;
    // The cast clip for the kit: Oblivion casts from the free left hand (onehandcast* keep the weapon still), with a
    // bow in that hand from the right (the *alt clips).
    std::optional<ClipInfo> castClip(bool self, const Kit &kit) const;
    // Which palms a cast clip casts from: bit 0 the left, bit 1 the right, bit 2 a dragon's mouth.
    static uint8_t castHands(const std::string &clipName);
    // Where a dragon's breath shows on screen, in the arms' space: on the ray from the eye through the Mouth node (below
    // the view), brought up to the screen's bottom edge, close in front of the eye; none without the node.
    std::optional<std::array<float, 3>> breathPoint() const;
    // A palm's centre in the arms' space (between the wrist and the knuckles).
    std::optional<std::array<float, 3>> palmPoint(bool left) const;
    std::vector<std::array<float, 3>> castPalms(uint8_t hands) const;
    // The blade's hilt and tip in the arms' space (offHand: the off-hand blade); none without a weapon in that hand.
    std::optional<std::pair<std::array<float, 3>, std::array<float, 3>>> bladePoints(bool offHand = false) const;
    void startCast(const ClipInfo &info, bool waitsForBlow, float rate, const std::array<float, 3> &color);
    // Records the trail sample for this frame (and, for a held pose, the samples the clip would have left).
    void updateTrail(float delta, const Kit &kit, bool heldPose, uint32_t clipIndex, float time);
    std::optional<std::array<float, 2>> nodeScreenPoint(uint32_t node) const;
    void updateBow(uint32_t clipIndex, float time, float delta, float transition, bool restart);

    Engine::ModelLoadResult loadArmsFile(const std::filesystem::path &path) const;

    std::string m_loadedPath;
    std::filesystem::path m_directory;
    // The packages the arms and their weapons come from; null: files on disk.
    const Engine::AssetFileSystem *m_pArmsAssets = nullptr;
    bool m_failed = false;
    std::shared_ptr<const Engine::ModelAsset> m_asset;
    std::unordered_map<std::string, ClipInfo> m_clips;
    std::unordered_map<std::string, std::shared_ptr<const Engine::ModelAsset>> m_attachments;
    const Engine::AssetFileSystem *m_pHeldAssets = nullptr;
    std::optional<HeldWeaponGrips> m_heldGrips;
    std::unordered_map<std::string, std::shared_ptr<const Engine::ModelAsset>> m_heldAssets;
    bool m_templateWeapons = true;
    std::optional<HeldSkinRules> m_skinRules;
    std::optional<uint8_t> m_forcedTier;
    Engine::ModelInstanceSystem m_instances;
    Engine::ModelInstanceHandle m_handle;
    uint32_t m_cameraNode = UINT32_MAX;
    uint32_t m_weaponNode = UINT32_MAX;
    uint32_t m_shieldNode = UINT32_MAX;
    uint32_t m_leftHandNode = UINT32_MAX;
    uint32_t m_offHandNode = UINT32_MAX;
    // A dragon's talon tips (the slash direction of a rake) and mouth (the breath's start).
    uint32_t m_clawTipRightNode = UINT32_MAX;
    uint32_t m_clawTipLeftNode = UINT32_MAX;
    uint32_t m_mouthNode = UINT32_MAX;
    // The left hand's Torch frame (the crossbow's foregrip) in the Weapon node's space, as the crossbow clips keep it
    // (measured in crossbowidle); none without those clips.
    std::optional<Engine::ModelMatrix> m_crossbowGrip;
    float m_aspect = 16.0f / 9.0f;
    bool m_trace = false;
    // Game seconds since the arms were loaded: the trace's clock.
    float m_clock = 0.0f;
    float m_lastMemberRecovery = 0.0f;
    // When the active member was last ready again after a recovery (the clock): a blow soon after continues the combo.
    float m_readyClock = -100.0f;
    uint32_t m_torchNode = UINT32_MAX;
    // The drawn bow: its own instance, placed on the Torch node and sampled with the arms' clip (its "rest" clip when
    // the arms play one the bow has no keys for).
    Engine::ModelInstanceHandle m_bowHandle;
    std::shared_ptr<const Engine::ModelAsset> m_bowAsset;
    std::unordered_map<std::string, uint32_t> m_bowClips;
    bool m_bowShown = false;
    std::optional<Kit> m_kit;
    std::optional<Kit> m_kitOverride;
    // The weapon model's far end in the weapon node's space: the blade tip whose screen path gives a blow's direction.
    std::array<float, 3> m_bladeTip = {};
    std::array<float, 3> m_offBladeTip = {};
    // A running one-shot clip (swing, cast, block hit, equip) and its time.
    std::optional<ClipInfo> m_action;
    float m_actionSeconds = 0.0f;
    // Clip seconds per second for the running action: above 1 when a swing is fitted to a short recovery.
    float m_actionRate = 1.0f;
    // Swings since the arms were last at rest: picks the combo's variants.
    uint32_t m_comboStep = 0;
    // The running action is a combo swing; when the last one was still running, and the side it hands on to.
    bool m_actionIsSwing = false;
    float m_lastSwingEnd = -100.0f;
    char m_nextSwingSide = 'R';
    bool m_actionRestart = false;
    bool m_actionWaitsForBlow = false;
    bool m_actionIsBlockHit = false;
    // A swing asked for before the running one reached its chain key: it starts there.
    bool m_swingQueued = false;
    bool m_weaponHidden = false;
    float m_loopSeconds = 0.0f;
    uint32_t m_lastSwingSerial = 0;
    uint32_t m_lastActionSerial = 0;
    uint32_t m_lastShieldBlockSerial = 0;
    uint32_t m_lastTalentSerial = 0;
    // Clips queued after the running one (a talent's second sweep) and their rate.
    std::vector<std::pair<ClipInfo, float>> m_actionQueue;
    bool m_seenSerials = false;
    bool m_hasPartyPosition = false;
    float m_lastPartyX = 0.0f;
    float m_lastPartyY = 0.0f;
    std::array<float, 2> m_moveVelocity = {};
    std::optional<std::pair<std::string, float>> m_heldPose;
    std::optional<std::array<float, 2>> m_lastBladePoint;
    std::optional<std::array<float, 2>> m_lastLeftPoint;
    // Where the blade (or right fist) and the left fist were on screen as the running swing began.
    std::optional<std::array<float, 2>> m_swingStartBlade;
    std::optional<std::array<float, 2>> m_swingStartLeft;
    std::array<float, 16> m_viewProjection = {};
    bool m_hasViewProjection = false;
    bgfx::UniformHandle m_worldClipPlaneUniform = BGFX_INVALID_HANDLE;

    // The arms' effects (weapon trail, casting glow) and what drives them.
    FirstPersonViewModelFx m_fx;
    uint32_t m_rightHandNode = UINT32_MAX;
    // Each hand's knuckles (Finger1 to Finger4): the palm lies between them and the wrist.
    std::array<uint32_t, 4> m_leftKnuckles = {UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX};
    std::array<uint32_t, 4> m_rightKnuckles = {UINT32_MAX, UINT32_MAX, UINT32_MAX, UINT32_MAX};
    // The running action draws the weapon trail (a swing or a melee talent), or is a cast with its hands and colour.
    bool m_actionTrails = false;
    bool m_actionIsCast = false;
    uint8_t m_actionCastHands = 0;
    std::array<float, 3> m_actionCastColor = {};
    // A swing request that is a cast (Input::swingIsCast) or a dragon's breath, waiting like a queued swing.
    bool m_queuedIsCast = false;
    bool m_queuedIsBreath = false;
    // The running swing is a dragon's bite: its blow goes down the screen (the jaw), not along a claw.
    bool m_actionIsBite = false;
    // Taken over from the other view model (resume): the next kit is drawn with the equip clip.
    bool m_resumed = false;
    bool m_queuedCastSelf = false;
    std::array<float, 3> m_queuedCastColor = {};
    float m_queuedRecovery = 0.0f;
    bool m_trailEnabled = true;
    // Each blade's last tip (main, off hand) for the trail's speed.
    std::array<std::optional<std::array<float, 3>>, 2> m_lastTipPoints;
    std::optional<std::array<float, 3>> m_fxPreview;
};
}
