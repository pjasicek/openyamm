#pragma once

#include "game/content/ContentManifest.h"
#include "game/coop/CoopBodies.h"

#include "game/events/EventRuntime.h"
#include "game/app/GameSettings.h"
#include "game/gameplay/PlayerCommands.h"
#include "game/gameplay/CinematicRuntime.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayInputController.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/mm9/Mm9QuestMarkers.h"
#include "game/rules/LentAura.h"
#include "game/rules/maw/MawRules.h"
#include "game/scene/SceneKind.h"
#include "game/data/GameDataRepository.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayUiRuntime.h"

#include <SDL3/SDL.h>

#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Game
{
struct GameplayInputFrame;

struct GameplayUpdateFramePerformanceDiagnostics
{
    bool collected = false;
    uint64_t totalNanoseconds = 0;
    uint64_t sharedFrameStateNanoseconds = 0;
    uint64_t worldInteractionStateNanoseconds = 0;
    uint64_t activeMemberSyncNanoseconds = 0;
    uint64_t sharedInputNanoseconds = 0;
    uint64_t worldMovementNanoseconds = 0;
    uint64_t actorAiNanoseconds = 0;
    uint64_t combatEventsNanoseconds = 0;
    uint64_t interactionFrameNanoseconds = 0;
    uint64_t projectileAndCooldownNanoseconds = 0;
    uint64_t performanceTraceLogNanoseconds = 0;
    GameplayWorldMovementFrameDiagnostics worldMovement = {};
};

struct GameplayUiFramePerformanceDiagnostics
{
    bool collected = false;
    uint64_t totalNanoseconds = 0;
    uint64_t worldUiRenderStateNanoseconds = 0;
    uint64_t standardUiNanoseconds = 0;
    uint64_t pendingSpellOverlayNanoseconds = 0;
    GameplayUiOverlayFramePerformanceDiagnostics overlays = {};
};

// Joins a map's state key and the id of an instance of it (GameSession::mapStateKey).
constexpr char MapInstanceKeySeparator = '#';

class GameSession
{
public:
    GameSession();
    ~GameSession();

    using SaveGameToPathCallback = std::function<bool(
        const std::filesystem::path &,
        const std::string &,
        const std::vector<uint8_t> &,
        std::string &)>;
    using SettingsChangedCallback = std::function<void(const GameSettings &)>;

    void clear();
    void bindDataRepository(const GameDataRepository *pDataRepository);
    bool hasDataRepository() const;
    const GameDataRepository &data() const;

    const std::optional<Party> &partyState() const;
    std::optional<Party> &partyState();
    void setPartyState(const Party &party);
    void setPartyState(Party &&party);
    // The game's own record: quest progress, the journal, what events and NPCs remember, shop stock. The session owns
    // it, and the session's party and the loaded map's party are bound to it (Party::bindCampaign), so that every
    // party of the game plays in the same one.
    CampaignState &campaign();
    const CampaignState &campaign() const;

    SceneKind currentSceneKind() const;
    void setCurrentSceneKind(SceneKind sceneKind);

    bool hasCurrentMapFileName() const;
    const std::string &currentMapFileName() const;
    void setCurrentMapFileName(const std::string &mapFileName);
    void setCurrentMapFileName(std::string &&mapFileName);
    // The instance of the current map the party is in: a second state of the same map file that leaves the map's own
    // state alone (MAW's dimension rifts). Empty on the map itself. It belongs to the current map: set it together
    // with the map's file name when the party moves.
    const std::string &mapInstanceId() const;
    void setMapInstanceId(const std::string &instanceId);
    // The key a state of the map goes under in outdoorWorldStates() and indoorSceneStates(): the map's own, or its
    // instance's.
    std::string mapStateKey(const std::string &mapFileName, const std::string &instanceId) const;
    // Drops the states of map instances the rules no longer keep (MonsterRules::liveMapInstances).
    void discardEndedMapInstances();
    float gameMinutes() const;
    void setGameMinutes(float gameMinutes);
    // The rules this game is played by; the loaded tables must match (GameApplication::activateRuleset).
    const RulesetSelection &ruleset() const;
    // Builds the ruleset's rules (MAW) and installs them on the party.
    void setRuleset(const RulesetSelection &ruleset);
    // Changes the options of the game's ruleset mid-game (the Current game page): MAW re-sizes the current map's
    // monsters now and every other map's when it loads. The caller checks what the ruleset allows.
    void setRulesetOptions(const RulesetOptions &options);
    // The rules the ruleset plays by; null for Standard.
    const GameRules *rulesetGameRules() const;
    // A co-op session (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "Co-op rules"): the world belongs to
    // several players, so nothing this game shows may stop it. Its own screens (inventory, spellbook, journal,
    // dialogue, a chest, the game menu) hold this game's input only; the right button's inspect pause and a spell
    // waiting for its target no longer pause either. A property of the running session: not saved, not cleared with
    // the game, set by whoever hosts or joins (today the console's `coop`).
    void setCoopSession(bool coopSession);
    bool coopSession() const;
    // Whose simulation a co-op session's world is (game/coop/CoopSession.h): this game's, which other games joined, or
    // another game's, whose world this one shows as a replica. A replica runs no monster AI, no map scripts and no
    // loot rolls: its map's state comes from the host, and what its player does goes to the host as commands.
    enum class CoopRole : uint8_t
    {
        None,
        Host,
        Guest,
    };
    void setCoopRole(CoopRole role);
    CoopRole coopRole() const;
    bool coopReplica() const
    {
        return m_coopRole == CoopRole::Guest;
    }

    // A co-op session's other players (PlayerId 1 and up). Each has a party of its own, bound to the session's
    // campaign, and a place in the loaded map. Nothing connects them to another game yet: the scenario runner places
    // and drives them (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "Two players as built").
    struct GuestPlayer
    {
        PlayerId id = LocalPlayer;
        Party party;
        GameplayPlayerBody body = {};
        // The game minute its timed states were last advanced to.
        float timedStatesGameMinutes = 0.0f;
        // How long its party has been unable to act (playerDownSeconds).
        float downSeconds = 0.0f;
        // Its game is loading the map (a guest of another game, game/coop): until it is ready its party is not in
        // the map for monsters and missiles.
        bool loadingMap = false;
        // Counts the places the host put its party at (a teleport by an event, an arrival, a return): its own game
        // moves it there, and a position it sent before it knew is not taken.
        uint32_t bodyOrderSerial = 0;
        // The auras the other players' parties near it lend it now (updateLentAuras), which its game is told.
        std::vector<LentAura> lentAuras;
        // The player's screens as the host keeps them: while the host does something for the player, this is the
        // session's UI state (gameplayUiController), so a dialogue that opens, a status line and what the cursor
        // holds are this player's and not the host's own. The player's game shows its own copy of them.
        GameplayUiController ui;
        // The player's part of the map's event state while the host does not act for it: its conversation, its
        // messages and what its last event asked for (swapTransientEventRuntimeState).
        EventRuntimeState eventTransients;
        // What the host did for the player that its game has to show, until the game is told (game/coop).
        struct Outcome
        {
            // A dialogue that opened: the context it opened from and the conversation as it stood then, which the
            // player's game presents the same way.
            struct Dialogue
            {
                EventRuntimeState::PendingDialogueContext context;
                EventRuntimeState::DialogueRuntimeState dialogueState;
                std::vector<std::string> messages;
                size_t previousMessageCount = 0;
                bool allowNpcFallbackContent = true;
            };
            std::optional<Dialogue> dialogue;
            // The player's dialogue was closed by what the host did.
            bool dialogueClosed = false;
            std::vector<std::pair<std::string, float>> statusTexts;
            std::vector<EventRuntimeState::PendingSound> sounds;
            bool any() const
            {
                return dialogue.has_value() || dialogueClosed || !statusTexts.empty() || !sounds.empty();
            }
        };
        Outcome outcome;
        // The chest and the corpse the player has open, as they stood when the host last did something for the
        // player: the player's game shows them and sends back what its player took out or put in.
        std::optional<GameplayChestViewState> chestView;
        std::optional<GameplayCorpseViewState> corpseView;
    };
    // Takes a copy of the party into the session's campaign and world; the party's own campaign state is left
    // behind, as a character's is that joins another world. Returns the player's id.
    // `wantedId`: the id a returning player had (LocalPlayer for any); `keptIds` are held for players who are away.
    PlayerId addGuestPlayer(const Party &party, const GameplayPlayerBody &body, PlayerId wantedId = LocalPlayer,
        const std::vector<PlayerId> &keptIds = {});
    // The same for a character that came as a saved state (another game's): a party of this game's tables and rules
    // is made of it.
    PlayerId addGuestPlayer(const Party::Snapshot &snapshot, const GameplayPlayerBody &body,
        PlayerId wantedId = LocalPlayer, const std::vector<PlayerId> &keptIds = {});
    bool removeGuestPlayer(PlayerId player);
    // Puts the other players' parties into the map as they stand now, without waiting for the next frame (a guest
    // whose game just finished loading the map).
    void publishGuestBodies();
    GuestPlayer *guestPlayer(PlayerId player);
    const std::vector<std::unique_ptr<GuestPlayer>> &guestPlayers() const;
    // The local player and the guests.
    size_t playerCount() const;
    // A player's party: the loaded map's for the local player, a guest's own; null for a player the session has not.
    Party *partyOfPlayer(PlayerId player);
    // While another player's command runs, the world's party is that player's (PlayerCommands); the local player's
    // is kept here so that partyOfPlayer(LocalPlayer) still names it.
    void setLocalPartyBehindActingParty(Party *pLocalParty);
    // Where the player's party stands on the loaded map; none without a map or for a player the session has not.
    std::optional<GameplayPlayerBody> bodyOfPlayer(PlayerId player);
    // How far a party buff or aura reaches the other players, and how far a spell on another player's character
    // reaches: the reach of a party's own shots and spells on monsters (IGameplayWorldRuntime::partyHitReach: 5120,
    // MM9's 3800; the user, 2026-11-21. It was 1024 until then).
    float aidReach() const;
    // Whether the two players stand within aidReach of each other: enough for a buff on everyone and for an aura.
    bool playersWithinAidRadius(PlayerId first, PlayerId second);
    // That, and nothing of the map between them: what a heal, cure or raising of one character needs.
    bool playersInAidSight(PlayerId first, PlayerId second);
    // The height of a party's eyes over its feet in the loaded map, for such a line.
    float partyEyeHeight() const;
    // Whether any player's party can still act. The game is lost only when none can ("Everyone is down").
    bool anyPlayerCanAct() const;
    // How long the player's party has been down (no member able to act); 0 while it can act.
    float playerDownSeconds(PlayerId player);
    // A downed player may return after this long ("A downed player").
    static constexpr float DownedReturnSeconds = 10.0f;
    // Where the players arrived on the loaded map: where a downed player returns to, and where the guests are put
    // when the map changes. Unset before a map is loaded.
    const std::optional<GameplayPlayerBody> &mapArrivalBody() const;

    // A map change one player asked for waits for the others ("Map travel"): every player but the proposer answers,
    // one refusal cancels it, and after TravelVoteForceSeconds without all answers the host may force it.
    struct TravelProposal
    {
        EventRuntimeState::PendingMapMove move;
        PlayerId proposer = LocalPlayer;
        std::vector<PlayerId> accepted;
        float ageSeconds = 0.0f;
        // Counts the session's proposals, so that a game can tell a new one from the one it already asked about.
        uint32_t serial = 0;
        // Put to the other players. A guest's trip is first asked of that guest alone (with the party, or alone
        // and out of the session for now); the host's is put to the others at once, the host cannot go alone.
        bool open = false;
    };
    static constexpr float TravelVoteForceSeconds = 30.0f;
    // A vote not answered by everyone lapses after this long: the world waits while it is open.
    static constexpr float TravelVoteLapseSeconds = 60.0f;
    // What a player may answer in the vote's window (GameApplication::updateCoopPrompts).
    enum class TravelChoice : uint8_t
    {
        None = 0,
        // The proposer, asked first: put the trip to the others.
        WithParty,
        // A voter: go along, or refuse (which ends the vote for everyone), or leave the session for now.
        Travel,
        Stay,
        DropOut,
        // The proposer: go there alone, out of the session (a guest), or take the proposal back.
        GoAlone,
        Cancel,
        // The host, once the vote is TravelVoteForceSeconds old: go without the missing answers.
        Force,
        // Nothing to decide (everyone agreed, the host is on its way).
        Ok,
    };
    const std::optional<TravelProposal> &travelProposal() const;
    void proposeTravel(EventRuntimeState::PendingMapMove move, PlayerId proposer);
    // The player whose command asked for the map move that waits in the map's event state: the local player
    // unless another player's command left it there (PlayerCommands). Taking it sets it back.
    void notePendingMoveProposer(PlayerId player);
    PlayerId takePendingMoveProposer();
    // False for a player the session has not, and for the proposer's agreeing (it has). A refusal drops the
    // proposal: any player's, and the proposer's own is its taking the proposal back.
    bool answerTravelProposal(PlayerId player, bool accept);
    // What a player had asked of the others is over when that player leaves the session.
    void dropProposalsOf(PlayerId player);
    // A co-op guest's game: the proposal as the host has it, for this game's prompt (game/coop).
    void setReplicaTravelProposal(std::optional<TravelProposal> proposal);
    // The travel prompt this game shows its player for a proposal of another player: the proposal's serial, 0 while
    // none is shown. The prompt is the map transition dialogue; its OK and Cancel are the player's answer.
    // `choices`: what the window's buttons mean, in their order. The serial is the proposal's, or
    // TravelDepartingSerial for the notice that everyone agreed.
    static constexpr uint32_t TravelDepartingSerial = 0xffffffffu;
    void setTravelPromptSerial(uint32_t serial, std::vector<TravelChoice> choices = {});
    uint32_t travelPromptSerial() const;
    const std::vector<TravelChoice> &travelPromptChoices() const;
    // What this game's player last answered, and to which window (its serial): the window is not shown again for
    // an answer that is on its way to the host.
    void noteTravelPromptAnswer(uint32_t serial, TravelChoice choice);
    uint32_t travelPromptAnswerSerial() const;
    TravelChoice travelPromptAnswer() const;
    // The other players' names above their bodies, as this frame draws them (the frame sets them, the views draw
    // them).
    void setCoopPlayerLabels(std::vector<CoopPlayerLabel> labels);
    const std::vector<CoopPlayerLabel> &coopPlayerLabels() const;
    // The other players for the HUD's players panel and the minimap, and the places pointed at for the minimap,
    // set by the frame in the same way.
    void setCoopHud(std::vector<CoopHudPlayer> players, std::vector<CoopHudPing> pings);
    const std::vector<CoopHudPlayer> &coopHudPlayers() const;
    // The other players on the map as a spell cast on one needs them (CoopAidPlayer), set with the session's update.
    void setCoopAidPlayers(std::vector<CoopAidPlayer> players);
    const std::vector<CoopAidPlayer> &coopAidPlayers() const;
    const std::vector<CoopHudPing> &coopHudPings() const;

    // A rest or a wait one player asked for ("Rest and waiting"): every other player agrees by its own Rest key, and
    // a proposal not agreed by all within RestVoteSeconds lapses. The host then rests everyone where they stand.
    struct RestProposal
    {
        PlayerId proposer = LocalPlayer;
        std::vector<PlayerId> accepted;
        float ageSeconds = 0.0f;
        uint32_t serial = 0;
        // A rest that heals (eight hours, food), else a wait.
        bool heal = false;
        float minutes = 0.0f;
    };
    static constexpr float RestVoteSeconds = 20.0f;
    const std::optional<RestProposal> &restProposal() const;
    void proposeRest(bool heal, float minutes, PlayerId proposer);
    // False for a player who has no say: the proposer, or one the session has not. A refusal drops the proposal.
    bool answerRestProposal(PlayerId player, bool accept);
    // A co-op guest's game: the proposal as the host has it.
    void setReplicaRestProposal(std::optional<RestProposal> proposal);
    // The proposal every player agreed to, which ends it; none while it waits, and never in a guest's game.
    std::optional<RestProposal> takePassedRestProposal();
    bool travelProposalPassed() const;
    // The host's override once the proposal is old enough; false before that.
    bool forceTravelProposal();
    // The move of a proposal that passed, which ends the proposal; none while it waits.
    std::optional<EventRuntimeState::PendingMapMove> takePassedTravelProposal();
    // The MAW rules of a MAW game, else null.
    MawRules *mawRules();
    const MawRules *mawRules() const;
    // The player whose party the ruleset's own values are read and written for (MAW's auras in effect, the monsters
    // near it: MawRules::setPartyInPlay). It is the local player's, except while a co-op host works something out
    // for another player's party; whoever names another player names the local one again when done.
    void setRulesPartyInPlay(PlayerId player);
    // While a world is shared with other players its quest items are the world's under any ruleset: every party of
    // the game keeps them in the campaign's quest pouch (CampaignState::questPouchShared), and what lies in the
    // parties' bags goes there now. Ended, under a ruleset without pouches, they go back into the local party's
    // bags, unless its Party pouches setting is on. A co-op session sets it; a game about to join one sets it first,
    // so that its own quest items stay with its own world.
    void setQuestPouchShared(bool shared);
    // The Gameplay setting Party pouches (Party::setPartyPouches) for the game's parties; the local party's items move
    // into or out of its pouches now (Party::sortPouchItems).
    void setPartyPouches(bool enabled);
    // Every party of a shared game plays in the session's campaign. The loaded map's party does so only once the
    // session has taken its state (GameplayController::synchronizeSessionFromRuntime); this does that now if it has
    // not happened yet, so that another player's party and the local one never have a campaign each.
    void bindLoadedPartyToCampaign();
    // Root of the game's named random streams (game/rules/RandomStreams.h), chosen at new game and saved.
    uint64_t randomRootSeed() const;
    void setRandomRootSeed(uint64_t rootSeed);
    // Where MAW's Beyond Madness death ledger lives, for every MAW game the session creates (scenarios keep it in their
    // own save folder); the default is the game's saves folder.
    void setMadnessLedgerFile(const std::filesystem::path &file);

    // The local player's screens, or another player's while the host does something for that player
    // (setActingGuestPlayer).
    GameplayUiController &gameplayUiController();
    const GameplayUiController &gameplayUiController() const;
    // The other player the host acts for at the moment (PlayerCommands), or null.
    void setActingGuestPlayer(GuestPlayer *pGuest);
    GuestPlayer *actingGuestPlayer() const;
    GameplayScreenState &gameplayScreenState();
    const GameplayScreenState &gameplayScreenState() const;
    GameplayUiRuntime &gameplayUiRuntime();
    const GameplayUiRuntime &gameplayUiRuntime() const;
    GameplayActorService &gameplayActorService();
    const GameplayActorService &gameplayActorService() const;
    // The active world's taverns seat generated mercenaries (world.yml tavernHirelings).
    void setTavernHirelings(bool enabled)
    {
        m_tavernHirelings = enabled;
    }
    // Whether the active world's friendly actors without an NPC of their own talk as MMerge street NPCs: their group's
    // news or a generated NPC (world.yml streetNpcs).
    void setStreetNpcs(bool enabled)
    {
        m_streetNpcs = enabled;
    }
    bool streetNpcs() const
    {
        return m_streetNpcs;
    }
    // Whether the active world has the MM6-MM8 hired NPC followers (world.yml npcFollowers), handed to the party for
    // each map it enters.
    void setNpcFollowers(bool enabled)
    {
        m_npcFollowers = enabled;
    }
    // Whether the active world shows the combat log under its combat_log setting's Auto (world.yml combatLog).
    void setWorldCombatLog(bool shown)
    {
        m_worldCombatLog = shown;
    }
    bool worldCombatLog() const
    {
        return m_worldCombatLog;
    }
    // Whether the active world places the party on MM9's formation grid (world.yml formations), handed to the party
    // for each map it enters.
    void setFormations(bool enabled)
    {
        m_formations = enabled;
    }
    // Whether the active world casts MM9's Fleet Foot from Fly's slot (world.yml fleetFoot), handed to the party for
    // each map it enters.
    void setFleetFoot(bool enabled)
    {
        m_fleetFoot = enabled;
    }
    // The active world's Hum (world.yml hum), handed to the party for each map it enters.
    void setWorldHum(const WorldHumDefinition &hum)
    {
        m_worldHum = hum;
    }

    void setWorldFloorBurn(const WorldFloorBurnDefinition &floorBurn)
    {
        m_worldFloorBurn = floorBurn;
    }

    void setWorldObjectiveQBits(const std::vector<uint32_t> &qbits)
    {
        m_worldObjectiveQBits = qbits;
    }
    GameplayCombatController &gameplayCombatController();
    const GameplayCombatController &gameplayCombatController() const;
    // Where every player's actions on the world enter (game/gameplay/PlayerCommands.h).
    PlayerCommands &playerCommands();
    const PlayerCommands &playerCommands() const;
    GameplayItemService &gameplayItemService();
    const GameplayItemService &gameplayItemService() const;
    GameplayProjectileService &gameplayProjectileService();
    const GameplayProjectileService &gameplayProjectileService() const;
    GameplayFxService &gameplayFxService();
    const GameplayFxService &gameplayFxService() const;
    GameplaySpellService &gameplaySpellService();
    const GameplaySpellService &gameplaySpellService() const;
    TurnBasedCombatRuntime &turnBasedCombatRuntime();
    const TurnBasedCombatRuntime &turnBasedCombatRuntime() const;
    GameplayScreenRuntime &gameplayScreenRuntime();
    const GameplayScreenRuntime &gameplayScreenRuntime() const;
    GameplayDialogController &gameplayDialogController();
    const GameplayDialogController &gameplayDialogController() const;
    GameplayOverlayInteractionState &overlayInteractionState();
    const GameplayOverlayInteractionState &overlayInteractionState() const;
    std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState();
    const std::array<uint8_t, SDL_SCANCODE_COUNT> &previousKeyboardState() const;

    IGameplayWorldRuntime *activeWorldRuntime() const;
    void bindActiveWorldRuntime(IGameplayWorldRuntime *pWorldRuntime);
    Mm9QuestMarkerState questMarkerForActor(size_t actorIndex) const;
    const GameplayInputFrame *currentGameplayInputFrame() const;
    void bindCurrentGameplayInputFrame(const GameplayInputFrame *pInputFrame);
    // Fast mode's factor on the gameplay delta (1 in scenarios): overheard talk runs its timeline at real pace,
    // matching its real-time voices, while the party around it plays on fast.
    void setGameSpeed(float speed);
    void updateGameplay(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool collectPerformanceDiagnostics = false);
    void beginFramePerformanceDiagnostics(bool enabled);
    const GameplayUpdateFramePerformanceDiagnostics &lastGameplayUpdateFramePerformanceDiagnostics() const;
    const GameplayUiFramePerformanceDiagnostics &lastGameplayUiFramePerformanceDiagnostics() const;
    void clearSharedInputFrameResult(bool blockWorldInput = false);
    void consumePendingGameplayAudioRequests();
    void renderGameplayUi(int width, int height);
    const GameplaySharedInputFrameResult &sharedInputFrameResult() const;
    bool sharedWorldInteractionBlockedThisFrame() const;
    bool autoWalkActive() const;
    void requestRelativeMouseMotionReset();
    bool consumeRelativeMouseMotionResetRequest();

    const std::optional<OutdoorPartyRuntime::Snapshot> &outdoorPartyState() const;
    void setOutdoorPartyState(const OutdoorPartyRuntime::Snapshot &snapshot);
    void setOutdoorPartyState(OutdoorPartyRuntime::Snapshot &&snapshot);

    const std::optional<OutdoorWorldRuntime::Snapshot> &currentOutdoorWorldState() const;
    void setCurrentOutdoorWorldState(const OutdoorWorldRuntime::Snapshot &snapshot);
    void setCurrentOutdoorWorldState(OutdoorWorldRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates() const;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> &outdoorWorldStates();

    const std::optional<IndoorSceneRuntime::Snapshot> &currentIndoorSceneState() const;
    void setCurrentIndoorSceneState(const IndoorSceneRuntime::Snapshot &snapshot);
    void setCurrentIndoorSceneState(IndoorSceneRuntime::Snapshot &&snapshot);

    const std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates() const;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> &indoorSceneStates();

    const std::unordered_map<std::string, int32_t> &namedGlobalVars() const;
    int32_t namedGlobalVar(const std::string &name, int32_t defaultValue = 0) const;
    void setNamedGlobalVar(const std::string &name, int32_t value);
    void clearNamedGlobalVar(const std::string &name);
    void mergeNamedGlobalVarsFromRuntime(const EventRuntimeState &runtimeState);
    void applyNamedGlobalVarsToRuntime(EventRuntimeState &runtimeState) const;

    // In-engine cinematics (game/gameplay/CinematicRuntime.h): the current map's <stem>.cinematics.yml, set by the
    // application at each map load (none: the map has no file), and the playing cinematic with the camera shake.
    void setMapCinematics(std::optional<CinematicLibrary> library);
    const std::optional<CinematicLibrary> &mapCinematics() const;
    CinematicRuntime &cinematicRuntime();
    const CinematicRuntime &cinematicRuntime() const;
    // Starts a cinematic of the current map; false (logged, and its done event runs) when the map has none of that id.
    bool playCinematic(const std::string &id, uint16_t doneEventId);
    // Called when a cinematic starts here, with its id: a co-op host's game tells its guests', which play it too.
    void setCinematicStartedCallback(std::function<void(const std::string &id)> callback);
    // Ends the playing cinematic and the camera shake without running anything (the map changed).
    void stopCinematics();
    // Finishes overheard talk at once (its remaining map events run, as on a skip) so a save can be written; a
    // cinematic that takes over the view is left playing.
    void finishAmbientCinematic();

    // Camera of the current scene (outdoor or indoor), saved and restored with the game.
    void setCameraAngles(float yawRadians, float pitchRadians);
    float cameraYawRadians() const;
    float cameraPitchRadians() const;
    bool cameraAnglesValid() const;

    const std::optional<std::filesystem::path> &currentSavePath() const;
    void setCurrentSavePath(const std::filesystem::path &path);
    void clearCurrentSavePath();

    const std::optional<EventRuntimeState::PendingMapMove> &pendingMapMove() const;
    void setPendingMapMove(const EventRuntimeState::PendingMapMove &pendingMapMove);
    void setPendingMapMove(EventRuntimeState::PendingMapMove &&pendingMapMove);
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();
    void clearPendingMapMove();

    void setSaveGameToPathCallback(SaveGameToPathCallback callback);
    bool canSaveGameToPath() const;
    bool saveGameToPath(
        const std::filesystem::path &path,
        const std::string &saveName,
        const std::vector<uint8_t> &previewBmp,
        std::string &error) const;

    void setSettingsChangedCallback(SettingsChangedCallback callback);
    void notifySettingsChanged(const GameSettings &settings) const;

    void requestOpenNewGameScreen();
    void requestOpenLoadGameScreen();
    bool consumePendingOpenNewGameScreenRequest();
    bool consumePendingOpenLoadGameScreenRequest();

    void captureOutdoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const OutdoorPartyRuntime::Snapshot &partySnapshot,
        const OutdoorWorldRuntime::Snapshot &worldSnapshot,
        float yawRadians,
        float pitchRadians
    );

    void captureIndoorRuntimeState(
        const std::string &mapFileName,
        const Party &party,
        const IndoorSceneRuntime::Snapshot &snapshot
    );

    // The layout identity of the map whose runtime is being built (MapAssetInfo::layoutIdentity): the capture
    // functions stamp it on that map's state (devdocs/SAVED_MAP_STATE_IDENTITY.md).
    void setCurrentMapLayoutIdentity(uint64_t identity);
    // Drops a map's saved state (doors, mechanisms, actors, chests, items on the ground, map and decoration
    // variables, timers): the map starts from its initial state when it is next built. With partyInside (a save made
    // in that map is being loaded) the party's saved place and camera there go too, so the party starts at the map's
    // start point. Party state (members, inventory, gold, QBits, journal, hirelings, global variables) stays.
    // In a map instance (mapInstanceId) the current map's state is the instance's: only that one goes.
    void discardMapState(const std::string &mapFileName, bool partyInside);

    // The playthrough's statistics (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md); they outlive clear(), since a load of the
    // same playthrough continues them.
    PlaythroughStatistics &playthroughStatistics();
    const PlaythroughStatistics &playthroughStatistics() const;
    std::optional<GameSaveData> buildSaveData() const;
    void restoreFromSaveData(const GameSaveData &saveData);
    void restoreHeldInventoryItemFromSaveData(const GameSaveData &saveData);

private:
    // The one key a map's stored state goes under: its canonical id, or the file name of a map MapStats does not list.
    std::string mapStateKey(const std::string &mapFileName) const;
    // The key of the current map's state: its instance's when the party is in one.
    std::string currentMapStateKey(const std::string &mapFileName) const;
    // A save from before rifts were map instances (SaveVersionMapInstances): the open dimension run moves out of its
    // map's state into the rift's, and the party gets the dimensional portal.
    void migrateDimensionRunsToInstances();

    struct GameplayUpdatePerformanceDiagnostics
    {
        uint64_t frames = 0;
        uint64_t activeWorldFrames = 0;
        uint64_t actorAiFrames = 0;
        uint64_t totalNanoseconds = 0;
        uint64_t sharedFrameStateNanoseconds = 0;
        uint64_t worldInteractionStateNanoseconds = 0;
        uint64_t activeMemberSyncNanoseconds = 0;
        uint64_t sharedInputNanoseconds = 0;
        uint64_t worldMovementNanoseconds = 0;
        uint64_t actorAiNanoseconds = 0;
        uint64_t combatEventsNanoseconds = 0;
        uint64_t interactionFrameNanoseconds = 0;
        uint64_t projectileAndCooldownNanoseconds = 0;
        uint64_t performanceTraceLogNanoseconds = 0;

        bool hasActivity() const
        {
            return frames != 0;
        }
    };

    struct TurnBasedFrameTraceState
    {
        bool active = false;
        uint32_t lastLogTick = 0;
        TurnBasedCombatStage stage = TurnBasedCombatStage::None;
        bool actorAiUpdate = false;
        bool gameplayPaused = false;
        bool allowMoveInput = false;
        bool cursorMode = false;
        bool modalBlocked = false;
        bool pendingSpellTarget = false;
        bool sharedWorldBlocked = false;
        int movementActionPoints = 0;
        int pendingActions = 0;
    };

    bool logGameplayUpdatePerformanceDiagnostics(uint32_t currentTick) const;
    void logTurnBasedFrameTraceIfNeeded(
        bool actorAiUpdate,
        bool gameplayPaused,
        bool allowMoveInput,
        bool movementStep,
        bool cursorMode,
        bool modalBlocked,
        bool pendingSpellTarget,
        bool sharedWorldBlocked,
        float movementDeltaSeconds,
        float frameDeltaSeconds);
    void updateMm9QuestMarkerCache();
    // Takes the events' cinematic and shake requests, the skip keys and advances the cinematic; true while one plays
    // (the frame's input is then m_cinematicInputFrame: nothing held).
    bool updateCinematics(const GameplayInputFrame &input, float deltaSeconds);
    void renderCinematicOverlay(int width, int height);

    const GameDataRepository *m_pDataRepository = nullptr;
    std::optional<std::filesystem::path> m_madnessLedgerFile;
    PlaythroughStatistics m_playthroughStatistics;
    // Takes the campaign state of a party just put into m_partyState over into m_campaign and binds the party to it.
    void bindPartyStateCampaign();

    CampaignState m_campaign;
    std::optional<Party> m_partyState;
    SceneKind m_currentSceneKind = SceneKind::Outdoor;
    std::string m_currentMapFileName;
    std::string m_mapInstanceId;
    GameplayScreenState m_gameplayScreenState;
    GameplayUiController m_gameplayUiController;
    GameplayUiRuntime m_gameplayUiRuntime;
    GameplayActorService m_gameplayActorService;
    // Hands the guests' places to the world and advances their parties' recovery and timed states.
    void updateGuestPlayers(IGameplayWorldRuntime &worldRuntime, float deltaSeconds);
    // Twice a second in a host's game with other players: every party is lent the auras of the parties within the
    // aid reach of it (no line of sight needed; the user, 2026-11-21), the strongest of each.
    void updateLentAuras(float deltaSeconds);
    float m_lentAuraSeconds = 0.0f;
    bool m_aurasLent = false;

    // Notes where the players arrived when the loaded map has changed, and puts the guests there.
    void updateMapArrival(IGameplayWorldRuntime &worldRuntime);

    bool m_coopSession = false;
    CoopRole m_coopRole = CoopRole::None;
    std::optional<TravelProposal> m_travelProposal;
    uint32_t m_travelProposalSerial = 0;
    uint32_t m_travelPromptSerial = 0;
    std::vector<TravelChoice> m_travelPromptChoices;
    uint32_t m_travelPromptAnswerSerial = 0;
    TravelChoice m_travelPromptAnswer = TravelChoice::None;
    std::vector<CoopPlayerLabel> m_coopPlayerLabels;
    std::vector<CoopHudPlayer> m_coopHudPlayers;
    std::vector<CoopAidPlayer> m_coopAidPlayers;
    std::vector<CoopHudPing> m_coopHudPings;
    std::optional<RestProposal> m_restProposal;
    bool m_travelProposalForced = false;
    std::optional<GameplayPlayerBody> m_mapArrivalBody;
    // The map, its instance and the world runtime m_mapArrivalBody belongs to.
    std::string m_mapArrivalMapFileName;
    std::string m_mapArrivalInstanceId;
    const IGameplayWorldRuntime *m_pMapArrivalWorldRuntime = nullptr;
    float m_localPlayerDownSeconds = 0.0f;
    std::vector<std::unique_ptr<GuestPlayer>> m_guestPlayers;
    Party *m_pLocalPartyBehindActingParty = nullptr;
    GuestPlayer *m_pActingGuestPlayer = nullptr;
    PlayerId m_pendingMoveProposer = LocalPlayer;
    // Whether the world holds guest bodies, so that it is told once when the last guest has gone.
    bool m_guestBodiesPublished = false;
    bool m_tavernHirelings = true;
    bool m_streetNpcs = true;
    bool m_npcFollowers = true;
    bool m_worldCombatLog = true;
    bool m_formations = false;
    bool m_fleetFoot = false;
    WorldHumDefinition m_worldHum;
    WorldFloorBurnDefinition m_worldFloorBurn;
    std::vector<uint32_t> m_worldObjectiveQBits;
    GameplayCombatController m_gameplayCombatController;
    GameplayItemService m_gameplayItemService;
    GameplayProjectileService m_gameplayProjectileService;
    GameplayFxService m_gameplayFxService;
    GameplaySpellService m_gameplaySpellService;
    PlayerCommands m_playerCommands;
    TurnBasedCombatRuntime m_turnBasedCombatRuntime;
    size_t m_turnBasedPendingWorldActions = 0;
    GameplayScreenRuntime m_gameplayScreenRuntime;
    GameplayDialogController m_gameplayDialogController;
    GameplayOverlayInteractionState m_overlayInteractionState;
    std::array<uint8_t, SDL_SCANCODE_COUNT> m_previousKeyboardState = {};
    IGameplayWorldRuntime *m_pActiveWorldRuntime = nullptr;
    Mm9LoadedLocationQuestMarkerCache m_mm9QuestMarkerCache;
    uint64_t m_mm9QuestMarkerMapRevision = 1;
    const GameplayInputFrame *m_pCurrentGameplayInputFrame = nullptr;
    GameplaySharedInputFrameResult m_sharedInputFrameResult = {};
    bool m_sharedWorldInteractionBlockedThisFrame = false;
    // Auto-walk (KeyboardAction::AutoWalk): the party walks forward as if Forward were held.
    bool m_autoWalkActive = false;
    bool m_relativeMouseMotionResetRequested = false;
    std::optional<OutdoorPartyRuntime::Snapshot> m_outdoorPartyState;
    std::optional<OutdoorWorldRuntime::Snapshot> m_currentOutdoorWorldState;
    std::unordered_map<std::string, OutdoorWorldRuntime::Snapshot> m_outdoorWorldStates;
    std::optional<IndoorSceneRuntime::Snapshot> m_currentIndoorSceneState;
    std::unordered_map<std::string, IndoorSceneRuntime::Snapshot> m_indoorSceneStates;
    uint64_t m_currentMapLayoutIdentity = 0;
    std::unordered_map<std::string, int32_t> m_namedGlobalVars;
    float m_gameMinutes = 9.0f * 60.0f;
    RulesetSelection m_ruleset;
    std::unique_ptr<MawRules> m_pMawRules;
    uint64_t m_randomRootSeed = 0;
    float m_cameraYawRadians = 0.0f;
    float m_cameraPitchRadians = 0.0f;
    bool m_cameraAnglesValid = false;
    std::optional<std::filesystem::path> m_currentSavePath;
    std::optional<EventRuntimeState::PendingMapMove> m_pendingMapMove;
    SaveGameToPathCallback m_saveGameToPathCallback;
    SettingsChangedCallback m_settingsChangedCallback;
    mutable GameplayUpdatePerformanceDiagnostics m_gameplayUpdatePerformanceDiagnostics;
    mutable uint32_t m_lastGameplayUpdatePerformanceLogTick = 0;
    bool m_framePerformanceDiagnosticsEnabled = false;
    GameplayUpdateFramePerformanceDiagnostics m_lastGameplayUpdateFramePerformanceDiagnostics = {};
    GameplayUiFramePerformanceDiagnostics m_lastGameplayUiFramePerformanceDiagnostics = {};
    TurnBasedFrameTraceState m_turnBasedFrameTraceState;
    std::optional<CinematicLibrary> m_mapCinematics;
    CinematicRuntime m_cinematicRuntime;
    std::function<void(const std::string &id)> m_cinematicStarted;
    float m_gameSpeed = 1.0f;
    GameplayInputFrame m_cinematicInputFrame = {};
};
}
