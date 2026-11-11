#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace YAML
{
class Node;
}

namespace OpenYAMM::Game
{
// MM9 monster AI data (devdocs/mm9_rework/monster_ai/PROFILE.md). Generated per MONSTERS.txt row (the `mm9_ai` monster
// modifier) and per placed actor (the scene actor's `mm9_ai` map, written by the MM9 map converters). Distances and
// speeds are in our units: MM9's LithTech units x 2.56. The walkers read it from phase 2 (MM9_MONSTER_AI_PLAN.md).

// The behaviour loop (MM9's base script family).
enum class Mm9AiArchetype : uint8_t
{
    Crawler,        // BaseCrawl.inc: chase timed to arrive as the attack is ready, attack, retarget by chance
    Skirmisher,     // BaseMelee.inc: the crawler plus strafe attacks, evades and back-off taunts
    RangedHolder,   // Range.inc type 2 (EvilSorcerer.scr): never chases, shoots or casts from where it stands
    Flier,          // BaseFly.inc: strafing passes, back-off upward, swoop; never flees
    Swimmer,        // BaseSwim.inc: a crawler that never chases a target out of the water
    Turret,         // lobber.scr, dragon.scr: rooted, scans by turning, shoots
    Civilian,       // NPCBase.inc, the animals: wander and chat, flee and call for help
    Guard,          // PoliceMan.inc: answers help calls, turns on the party after 3 hits
};

// How it moves: its native class (AISwimFly flies or swims), not the Fly column.
enum class Mm9AiMovement : uint8_t
{
    Walk,
    Fly,
    Swim,
};

// The ranged add-on of its script: none, the walkers' Range.inc or the fliers' FlyRange.inc.
enum class Mm9AiRanged : uint8_t
{
    None,
    Walker,
    Flier,
};

// MM9's wince roll: Never for `Always Wince? = 1` (the column reads as its opposite), else 20-50 % once its health is
// at most 20 %.
enum class Mm9AiWince : uint8_t
{
    LowHealth,
    Never,
};

// A dormant start: what wakes it.
enum class Mm9AiDormantUntil : uint8_t
{
    None,
    Trigger,    // a map or script trigger (MM9's AddTrigger: awaken, go, Resurrect, WakeUp, ForceBreak ...)
    Disturbed,  // damage, an alert, a help call, a nearby projectile or a target in sight
    Sighted,    // the party in sight
};

// A dormant start: how it waits.
enum class Mm9AiDormantPose : uint8_t
{
    Stand,
    Lie,
    Sleep,
    Hang,
    Underground,
    Hidden,
    Caged,
    Coffin,
};

// The placement's wander layer (BaseWander.inc).
enum class Mm9AiWanderMode : uint8_t
{
    Off,
    Aimless,
    Path,
};

// A placement's hostility gate.
enum class Mm9AiHostility : uint8_t
{
    Default,
    FriendlyUntilProvoked,  // the *Hostility.inc includes, GuardRude, GuardHelp
    HostileAfterEvent,      // DookHostility.inc: friendly until the party comes through the tunnel
};

// Which hostility include (or guard script) gates it.
enum class Mm9AiFaction : uint8_t
{
    None,
    Monk,
    Dook,
    Drangheim,
    Honk,
    Training,
    Guard,
};

// The profile of a MONSTERS.txt row (modifier mm9_ai).
struct Mm9AiProfile
{
    Mm9AiArchetype archetype = Mm9AiArchetype::Skirmisher;
    Mm9AiMovement movement = Mm9AiMovement::Walk;
    Mm9AiRanged ranged = Mm9AiRanged::None;
    Mm9AiWince wince = Mm9AiWince::LowHealth;
    // The distance at which it decides to attack: MM9's AttackRange stat = the AttackReach column + 1.25 x (the
    // horizontal radius - the half depth of its dims). The two column names are swapped in MM9.
    float attackReach = 0.0f;
    // The melee hit's sweep beyond its own radius: the AttackRange column x Scale.
    float meleeSweep = 0.0f;
    // The radius of its alerts to friends: AlertRadius x Scale.
    float alertRadius = 3072.0f;
    float walkSpeed = 0.0f;
    float runSpeed = 0.0f;
    float flySpeed = 0.0f;
    // The forward impulse of its attack's `lunge` key (LungeVelocity; MM9 applies twice it times the key's factor).
    float lungeVelocity = 0.0f;
    // Its eye below the top of its body (AIBase GetEyePos: 2 LT): its sight lines start there.
    float eyeBelowTop = 5.12f;
    // It raises dead friends (the Resurrect column).
    bool resurrecter = false;
    // Its head turns toward its target or the party talking to it (the HeadTurn column; MM9_AMBIENT_ANIMATION.md
    // section 2.4): false for the non-humanoid rows.
    bool headTurn = true;
    // Its MM9 model's clips the layers need (MM9_MONSTER_AI_PLAN.md phase 4a): Cower (BaseRun.inc cowers only with
    // one), Resurrect (a corpse rises only with one; its length) and ResurrectSpell (a resurrecter raises others only
    // with one; its length and its DoResurrection key).
    bool cower = false;
    float raiseSeconds = 0.0f;
    float resurrectSpellSeconds = 0.0f;
    float resurrectKeySeconds = 0.0f;
    // A boss row (the Dragon King, Yanmir): its fight is a Lua behaviour (plan phase 5).
    bool boss = false;
    // A cast's own recovery, counted from the cast (SPELL.txt at the row's mastery, 33 ms per game second; 0: the
    // row's Recovery), of its first and second spell.
    float spell1RecoverySeconds = 0.0f;
    float spell2RecoverySeconds = 0.0f;
    // Family hooks (MM9_AI_DATA_AND_SCRIPTS.md section 4.1).
    // SpeedThrottle: it keeps pace with a moving target while it strikes (false: the Dagrells).
    bool throttle = true;
    // It evades after every attack (the Lobber Pods), each evade lasting evadeMinSeconds-evadeMaxSeconds (0: the
    // skirmisher footwork's evade).
    bool alwaysEvade = false;
    float evadeMinSeconds = 0.0f;
    float evadeMaxSeconds = 0.0f;
    // It holds a ranged weapon prop: its Attack in reach becomes RangeAttack, a shot or a spell by Att%
    // (MM9_AI_NATIVE_RE.md section 7.2.3). Without one a monster in reach always strikes its blow.
    bool rangedWeapon = false;
    // Its script runs no AI (a placement's dialogue or set-piece script, such as Sturmguard.scr): it never takes a
    // target, answers no hit or call and never attacks; its loop still wanders and wakes as placed.
    bool passive = false;
    // A turret launches this monster every podCooldownMinSeconds-podCooldownMaxSeconds (the Lobbers); 0: none.
    int16_t podLaunchMonsterId = 0;
    float podCooldownMinSeconds = 5.0f;
    float podCooldownMaxSeconds = 10.0f;
    // During each melee pass it is undead (immune) for up to this long (the Banshees); 0: never.
    float meleeWindowSeconds = 0.0f;
    // MM9 runs these two only for monsters spawned with p0 = 1 (the 1000 Terrors spawners): it appears with its spawn
    // clip, and its corpse spawns deathSpawnMonsterId (0: none).
    bool spawnIn = false;
    int16_t deathSpawnMonsterId = 0;
    // It starts dormant (the Flying Ickies hang until disturbed).
    Mm9AiDormantUntil dormantUntil = Mm9AiDormantUntil::None;
    Mm9AiDormantPose dormantPose = Mm9AiDormantPose::Stand;
    // NPCBase.inc (MM9_MONSTER_AI_PLAN.md phase 4b): a townsperson that flees runs to a town guard
    // (BaseRunFindHidingPlace's GetObjects GuardBase).
    bool guardRefuge = false;
    // Its MM9 model's clips for a dormant start and a spawn-in (phase 4b): the clip a hanging start plays as it wakes
    // (Launch) and its hanging fidget (HangFidget); the clip a lying start (a coffin's mummy) plays as it gets up
    // (Wakeup); its Spawn clip and its Aware clip (its Taunt without one).
    float wakeSeconds = 0.0f;
    float wakeupSeconds = 0.0f;
    float dormantFidgetSeconds = 0.0f;
    float spawnSeconds = 0.0f;
    float awareSeconds = 0.0f;
};

// BaseMelee.inc's footwork a placement's script gives or takes (the skirmisher modifier's fields).
struct Mm9AiFootwork
{
    bool enabled = false;
    float strafeAttackChance = 0.8f;
    float evadeChance = 0.4f;
    float tauntSeconds = 0.0f;

    bool operator==(const Mm9AiFootwork &other) const = default;
};

// The profile fields a placement's own script decides where it runs a different loop than its row's default script
// (MM9 runs the placed ScriptName; the scene's `mm9_ai` `profile`, written by the MM9 map converters). An empty field
// keeps the row's.
struct Mm9AiPlacementProfile
{
    std::optional<Mm9AiArchetype> archetype;
    std::optional<Mm9AiRanged> ranged;
    std::optional<bool> rangedWeapon;
    std::optional<bool> guardRefuge;
    std::optional<bool> throttle;
    std::optional<bool> alwaysEvade;
    std::optional<float> evadeMinSeconds;
    std::optional<float> evadeMaxSeconds;
    std::optional<float> meleeWindowSeconds;
    std::optional<bool> spawnIn;
    std::optional<int16_t> deathSpawnMonsterId;
    bool passive = false;
    // The skirmisher footwork (ActorTacticsFacts::skirmish) the script gives or takes.
    std::optional<Mm9AiFootwork> footwork;
    // Saved before the profile (save version 149), the placement's idle clip (173) or its routines (174) existed: the
    // map's scene gives them when the map is next entered.
    bool fromScene = false;

    bool operator==(const Mm9AiPlacementProfile &other) const = default;
};

// The profile of a townsperson placed on a stand-in row that has none (a scene actor's `mm9_civilian` on an engine
// peasant row, as the MM9 cities place their people): NPCBase.inc's civilian with an MM9 peasant's speeds.
const Mm9AiProfile &mm9StandInCivilianProfile();

// A placed actor's settings (scene mm9_ai). An actor with a profile but no placement record (a summon, an old save)
// has MM9's own defaults below.
struct Mm9AiPlacement
{
    // Vision and hearing (SightDistance 1 320 LT, HearingDistance 360 LT by default); MM9 doubles both the first time
    // the monster targets the party. Sight sees a 180 degree half-space; neither goes through walls.
    float sight = 3379.0f;
    float hearing = 922.0f;
    // The chance it rolls at placement to be a runner (MM9's ShouldRunAway).
    float runawayChance = 0.25f;
    // Range.inc type: 1 chases and shoots, 2 holds its place and shoots.
    uint8_t rangedType = 1;
    bool canBeResurrected = false;
    Mm9AiWanderMode wander = Mm9AiWanderMode::Off;
    // Aimless wandering turns back beyond this distance from where it started (0: no leash; never on a path).
    float wanderLeash = 0.0f;
    float wanderWaitMinSeconds = 3.0f;
    float wanderWaitMaxSeconds = 8.0f;
    float wanderTimeMinSeconds = 3.0f;
    float wanderTimeMaxSeconds = 8.0f;
    // A path (Mm9AiPlacementRecord::pathPoints) is walked in random order instead of in turn.
    bool pathRandom = false;
    Mm9AiDormantUntil dormantUntil = Mm9AiDormantUntil::None;
    Mm9AiDormantPose dormantPose = Mm9AiDormantPose::Stand;
    Mm9AiHostility hostility = Mm9AiHostility::Default;
    Mm9AiFaction faction = Mm9AiFaction::None;
    // A summoner (Mm9AiPlacementRecord::summonClass at summonPoints).
    bool summoner = false;
    // It lies dead from the start (GreenParty.scr).
    bool startsDead = false;
    // A unique boss or set-piece placement (Njam, Ebora, Yanmir, the Isle of Ashes Sea Monster ...).
    bool boss = false;
    // The clip it loops whenever it stands idle, never fidgeting (its script's LoopAnim between walks: the Lindisfarne
    // monks' prayers and chores); a binding's script clip role or the model's own clip name. Empty: stand and fidget.
    std::string idleClip;
    // Its own script's profile fields over its row's.
    Mm9AiPlacementProfile profile;
};

// A stop of its wander path at a marker (BaseWander.inc OnWanderAtMarkerNext; scene mm9_ai.path_stops): the path
// point it belongs to, the marker's facing (UseMarkerRotation: radians in the map's frame), its own wait
// (UseMarkerWaitTime: [minimum, maximum] seconds) and its clip (AnimationName, a binding's role; looped or once).
struct Mm9AiPathStop
{
    uint16_t point = 0;
    bool faces = false;
    float faceYawRadians = 0.0f;
    bool ownWait = false;
    float waitMinSeconds = 0.0f;
    float waitMaxSeconds = 0.0f;
    std::string clip;
    bool loop = false;

    bool operator==(const Mm9AiPathStop &other) const = default;
};

// One step of a routine (scene mm9_ai.routines; MM9's scripted work and scenes: a miner's walk to the rock face and
// its hammering, a training orc's drill, a ceremony): see Mm9AiRoutine.
struct Mm9AiRoutineClip
{
    std::string clip;
    float seconds = 0.0f;

    bool operator==(const Mm9AiRoutineClip &other) const = default;
};

struct Mm9AiRoutineStep
{
    enum class Kind : uint8_t
    {
        // Walks (Run: runs) to point, by its own steering; a step it cannot finish in 40 s is given up.
        Walk,
        Run,
        // Turns to faceYawRadians (map frame) at 360 degrees a second.
        Face,
        // Plays one of clips, picked uniformly, for its seconds (looping within them), standing without fidgets.
        Clip,
        // Stands idle for waitMinSeconds-waitMaxSeconds (its idle clip or its fidgets).
        Wait,
        // With chance it goes on with the next step; otherwise it skips the next skip steps (a chance group).
        Chance,
        // Puts its held items down (hide) or takes them up again until the routine changes (MM9's DetachProp and
        // AttachProp around a miner's trip to the dump).
        HideItems,
        ShowItems,
    };

    Kind kind = Kind::Wait;
    std::array<int32_t, 3> point = {};
    float faceYawRadians = 0.0f;
    std::vector<Mm9AiRoutineClip> clips;
    float waitMinSeconds = 0.0f;
    float waitMaxSeconds = 0.0f;
    float chance = 1.0f;
    uint16_t skip = 0;

    bool operator==(const Mm9AiRoutineStep &other) const = default;
};

// A named list of steps the MM9 loop runs, round and round, while the actor holds no target: in place of its wander
// and idle. `default` runs from the start; a map script switches to another or to none (evt.SetActorRoutine).
struct Mm9AiRoutine
{
    std::string name;
    std::vector<Mm9AiRoutineStep> steps;

    bool operator==(const Mm9AiRoutine &other) const = default;
};

// The routine it runs, an index into routines (-1: none): the one a map script chose (pChosen; an empty name: none),
// else its `default`.
int16_t mm9RoutineIndex(const std::vector<Mm9AiRoutine> &routines, const std::string *pChosen);

// A placed actor's record: its settings, the points its path and summons use and its MM9 placement script.
struct Mm9AiPlacementRecord
{
    Mm9AiPlacement settings;
    std::vector<std::array<int32_t, 3>> pathPoints;
    // The stops of its path that have a marker's facing, wait or clip.
    std::vector<Mm9AiPathStop> pathStops;
    // Its routines (scene mm9_ai.routines), in the scene's order.
    std::vector<Mm9AiRoutine> routines;
    std::vector<std::array<int32_t, 3>> summonPoints;
    // Its named hiding places (HidingPlace0-2): MM9's ShouldRunAway lets only a monster with one flee by morale.
    std::vector<std::array<int32_t, 3>> hidingPlaces;
    // The MM9 class a summoner calls (empty: its spawn manager's).
    std::string summonClass;
    // The placement's own MM9 script (lower-case file name, empty for the row's) and its ScriptParams.
    std::string script;
    std::string scriptParams;

    bool operator==(const Mm9AiPlacementRecord &other) const;
};

// MM9 spawned it with ScriptParams 1 ("GreaterDemon ScriptParams 1", the 1000 Terrors spawners): a row's spawn_in and
// death_spawn run only then. A placement record that runs its row's script with p0 = 1.
bool mm9SpawnedWithParam(const Mm9AiPlacementRecord &record);

// The profile an actor runs: its row's with its placement's overrides. Its placement script's fields replace the
// row's; a placed dormant start replaces the row's; a placed ranged type 2 makes a walker with Range.inc a ranged
// holder (MM9's Range.inc reads the placement).
Mm9AiProfile placedMm9AiProfile(const Mm9AiProfile &row, const Mm9AiPlacement &placement);

// Names as the data files write them (archetype `ranged_holder`, pose `underground` ...).
const char *mm9AiArchetypeName(Mm9AiArchetype archetype);
bool parseMm9AiArchetype(const std::string &text, Mm9AiArchetype &archetype);
bool parseMm9AiMovement(const std::string &text, Mm9AiMovement &movement);
bool parseMm9AiRanged(const std::string &text, Mm9AiRanged &ranged);
bool parseMm9AiWince(const std::string &text, Mm9AiWince &wince);
bool parseMm9AiDormantUntil(const std::string &text, Mm9AiDormantUntil &until);
bool parseMm9AiDormantPose(const std::string &text, Mm9AiDormantPose &pose);

// Reads a scene actor's `mm9_ai` map (game/maps/IndoorSceneYml.cpp, OutdoorSceneYml.cpp). False with error for an
// unknown key or a bad value.
bool parseMm9AiPlacementNode(const YAML::Node &node, Mm9AiPlacementRecord &record, std::string &error);
}
