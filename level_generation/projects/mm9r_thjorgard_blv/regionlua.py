"""
Thjorgard (the region) map Lua: its scripted objects as native handlers, each citing its .scr (mm9/extracted/SCRIPTS/
SCRIPTS). Loaded by ../mm9r_common/outdoor_blv.py `map_script` after the shared doors, chests and ForadWorld.scr
(devdocs/mm9_rework/REGIONS_FINISH.md step 2; the behaviour spec of every script is work/scr_spec.md). RUDE exits are
event 50000 + the DAT object index, a click before the dialogue 53000 + index (game/mm9/Mm9RudeDialogue.h).

- The fair games (ThjorgardGamesCommon.inc): the Huckster sells tickets (item 557, 5 gold; ten for 40; the rule book,
  item 594, with the first), every game takes one; each win gives its key (stones 7100, boat 7101, runes 7102, honky
  7103, bell 7104, might 7105); all six won while on Yrsa's quest (key 93): key 7106, 10 000 experience, the Stuffed
  Dragon (item 395) and key 94.
  - The stones game (StonesGame.scr, StonesSquare.scr, StonesPiece.scr, StonesPlayer.scr): a click on a board stone
    places a white (yellow) stone next to one of the party's; the stones player answers at random with a black (blue)
    one; whoever leaves the other without a move wins. Colours are decoration swaps (SetSprite), empty squares keep a
    grey stone so they can be clicked (MM9 hides them; its squares are brushes).
  - The runes game (Mastermind.scr, MastermindColor.scr, MastermindSpace.scr, the Switch door's "check"): four
    hidden colours, four tries; the flames by each right stone are told in the status line (MM9's FireCorrect fires
    are not placed).
  - The boat race (BoatJudge.scr, RacingBoat.scr): the judge's dialogue starts it after a countdown; each click on the
    party's boat pushes it one length (MM9: a hit), the rival boats advance on their own; the boats do not move here,
    the status line tells the race.
  - The bell (DingTheBell.scr, BellWeight.scr): a click on the strike plate rolls MM9's strength test and the weight
    (the Riser1 door) climbs to the height it reached.
- Hjarrand Fixer (NPC7.scr, RUDE 7): the payment for fixing the refinery's machine on his dialogue's exit; he is gone
  once paid (as in Thjorgard City).
- Thorgard_actor.scr: the jumpers (Jumper0-3) hidden until JumperTrigger, then one by one, and a dead one's partner at
  once (BuddyDead); Ken1-3, the night robbers, stay hidden until the party passes RobPlayerTrigger at night; the
  Magreeb ambush (MagreebBaby0, Jim, Dean, Walter, two Dummies) is hidden while the Scholar quest waits for its
  Magreeb (key 201 without 202), and the Magreeb baby gives key 202 once the party comes within 1 800 units of it.
  Scholarpromo.scr (Magreeb0, the adult) gives key 202 on sight during that quest, when the map places it.

- Whack-a-Honky.scr (Honky0-3) and Switch0, its start lever: a pull with a ticket counts down, then for ten seconds
  one goose at a time pops up; eight whacks win (key 7103).
- Armwrestle.scr "2" (HalfOrcCaptain0, placed through overrides.yml `outdoor.people`): a click with a ticket pits the
  active character's Might + 9-50 against his 2 + 1-40 (key 7105).

Not here (work/scr_spec.md): the stones player's own dialogue (his DAT row has no RUDE id), the boats' and the bell's
other motions, the jumpers' leap arc (their clips are played) and the ambush's chase (monster AI), the training hall's
breakable wall (TrainingEnter.scr: destructible brushes), voices, posed figures and banners (PropAnim.scr), the unplaced
stat stone, ambient sounds.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from dungeon import lua
from quest_xp import balanced_experience, experience_lua

SCALE = 2.56                    # MM9 units -> engine units
TAG = "thjorgard"
EV_TICK, EV_BELL = 300, 301     # timers: the games' half-second tick (also the polls), the bell's steps
EV_HONK, EV_HONK_END = 302, 303  # timers: whack-a-honky's countdown and geese, its ten seconds of play
EV_JUMPER_KILLED = 304          # monster killed hook: a jumper's DeathTriggerTarget (BuddyDead)
EV_PROP = 600                   # a scripted prop's click: EV_PROP + k
COG_PROP = 400                  # its SetSprite key: COG_PROP + k
EV_WALL = 370                   # the training hall's wall broken (DestructableBrush7, destructibles.py)
KEY_TRAINED = 301               # TrainingEnter.scr :OnBreak, as in the Training Hall (mm9r_traininghall)


def destructible_events(build) -> dict:
    """TrainingEnter.scr: the training hall's breakable wall (DestructableBrush7, DeathTrigger tomneededatrigger1 ->
    ScriptObject1 Break) gives the hall's reward when it breaks."""
    return {"DestructableBrush7": (EV_WALL, 0)} if "destructablebrush7" in build.source.by_name else {}

PIECES = [f"Piece{k}" for k in range(36)]           # StonesPiece.scr, on Square0-35 (StonesSquare.scr "Piece<k> <k>")
BUTTONS = [f"ColorButton{k}" for k in range(5)]     # MastermindColor.scr "0".."4": red, blue, yellow, orange, green
SPACES = [f"ColorSpace{k}" for k in range(4)]       # MastermindSpace.scr "0".."3"
PLAYER_BOAT = "RacingBoat0"                         # RacingBoat.scr "FinishLine0 0": the party's (not AI) boat
HONKIES = [f"Honky{k}" for k in range(4)]          # Whack-a-Honky.scr "<k> Honky 0 3"
CLICK_PROPS = PIECES + BUTTONS + SPACES + [PLAYER_BOAT] + HONKIES
COG_PROPS = PIECES + SPACES + HONKIES
# The stones' colours (StonesPiece.scr: skins\gibs\yellow.dtx white, blue.dtx black). MM9's pieces are stone.abc at
# scale 1; only the 2x coloured stones exist as decorations (the runes game's), so placed stones show twice as big.
STONE_EMPTY, STONE_WHITE, STONE_BLACK = "mm9_stone", "mm9_stoneyellow_x200", "mm9_stoneblue_x200"
RUNE_STONES = ["mm9_stonered_x200", "mm9_stoneblue_x200", "mm9_stoneyellow_x200", "mm9_stoneorange_x200",
               "mm9_stonegreen_x200"]           # MastermindSpace.scr :InitColors, by colour 0-4
RUNE_PLAIN = "mm9_stone_x200"
KENS = ("Ken1", "Ken2", "Ken3")
JUMPERS = ("Jumper0", "Jumper1", "Jumper2", "Jumper3")   # Thorgard_actor.scr :SetupJumper
JUMPER_TRIGGER = "JumperTrigger"
WARNING_TRIGGER = "JumperWarningTrigger0"   # its ActivationSound, rubble.wav (MM9_AMBIENT_AUDIO_RE.md G13)
# seconds from the trigger to each jumper's appearance: GetPlayer; Jumper.inc minWait/maxWait 1-2.5;
# Thorgard_actor.scr :JumperWaitGetPlayer 10-25 and 30-45
JUMPER_WAITS = ((0, 0), (1, 2.5), (10, 25), (30, 45))
AMBUSH = ("MagreebBaby0", "Jim", "Dean", "Walter", "Dummy")     # Thorgard_actor.scr :DisableCheckStart
ROB_TRIGGER = "RobPlayerTrigger"
BOAT_LENGTHS = 10               # RacingBoat.scr: a tenth of the way per move; arrival after ten (work/scr_spec.md)
TEXT = {                        # MMIXSCRIPTTEXT.csv (RollOverText numbers)
    6: "You Win!", 7: "You Lost.", 226: "Sorry, you need a ticket to play...", 227: "You bought a ticket.",
    228: "You received the Stuffed Dragon for completing all the games!",
    229: "You do not have enough gold to purchase a ticket.", 230: "White wins!!!", 231: "Black wins!!!",
    232: "You used a ticket.", 233: "Stone must be placed adjacent to another of your stones.",
    234: "You bought 10 tickets.", 235: "Five...", 236: "Four...", 237: "Three...", 238: "Two...", 239: "One...",
    241: "Only 3 chances left!!!", 242: "Only 2 chances left!!!", 243: "Only 1 chance left!!!", 244: "Your move.",
}


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def placed_props(build) -> set:
    """DAT names of the props the region places (its props.json)."""
    path = build.hooks.props_path(build)
    return {e["source_name"] for e in json.loads(path.read_text())} if path is not None and path.exists() else set()


def prop_events(build) -> tuple[dict, dict]:
    placed = placed_props(build)
    events = {name: EV_PROP + k for k, name in enumerate(CLICK_PROPS) if name in placed}
    cogs = {name: COG_PROP + k for k, name in enumerate(COG_PROPS) if name in placed}
    return events, cogs


def rude_exit(build, name: str) -> int:
    return 50000 + build.source.by_name[name.lower()]["index"]


def rude_use(build, name: str) -> int:
    return 53000 + build.source.by_name[name.lower()]["index"]


def group_event(build, group: str):
    return next((m["event"] for m in build.movers if m["group"] == group and m["event"]), None)


def group_doors(build, group: str) -> list:
    return [m["door_id"] for m in build.movers if m["group"] == group]


def extend(hooks, build, script) -> None:
    events, cogs = prop_events(build)
    actors = defaultdict(list)                  # DAT name -> placed actor indices (the monsters and the people)
    monster_of = {}                             # actor index -> its monster row (the clip lengths of its body)
    for record in build.content.report["actors"]:
        actors[record["anchor"]].append(record["actor_index"])
        monster_of[record["actor_index"]] = record["monster_id"]
    npc = getattr(hooks, "npc_actor", {})
    registrations = []
    load = []
    tick = []

    def item(verb, number):
        return f"MM9.{verb}Item({number}, \"{TAG}:games\")"

    lines = [
        "local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end",
        "local function say(text) evt.StatusText(text) end",
        "local function rnd(a, b)   -- MM9's GetRandomInt a, b (the high bits of the event generator)",
        "    return a + math.floor(MM9.random(0, 1073741823) / 65536) % (b - a + 1)",
        "end",
        "",
        "-- ThjorgardGamesCommon.inc: :CheckGameTicket + :TakeGameTicket (item 557), :Record*Win -> :CheckThjorgardWins",
        "-- -> :GiveThjorgardPrize (all six games won while on Yrsa's quest, key 93; MM9 waits two seconds first).",
        "local function ticket()",
        f"    if {item('has', 557)} ~= 1 then say({lua_string(TEXT[226])}); return false end",
        f"    {item('take', 557)}; say({lua_string(TEXT[232])})",
        "    return true",
        "end",
        "local function gameWon(key)",
        f"    say({lua_string(TEXT[6])}); MM9.giveKey(key)",
        "    if has(7106) then return end",
        "    for k = 7100, 7105 do if not has(k) then return end end",
        "    if not has(93) then return end",
        f"    MM9.giveKey(7106); MM9.giveExperience({balanced_experience(10000, 7106)}); {item('give', 395)}; "
        "MM9.giveKey(94); quest()",
        f"    say({lua_string(TEXT[228])})",
        "end",
        f"local function gameLost() say({lua_string(TEXT[7])}) end",
        "local function currentMight()   -- GetAttribute 0: the active character's Might",
        "    evt.ForPlayer(Players.Current)",
        "    local low, high = 0, 1023",
        "    while low < high do",
        "        local mid = math.floor((low + high + 1) / 2)",
        "        if IsAtLeast(ActualMight, mid) then low = mid else high = mid - 1 end",
        "    end",
        "    return low",
        "end",
        "",
    ]

    # --- the Huckster: HucksterMod.scr "0" (TicketMaster, RUDE 429) -------------------------------------------------
    if "TicketMaster" in npc:
        lines += [
            "-- HucksterMod.scr :OnRudeExit (TicketMaster, RUDE 429): his row \"We'd love to play\" gives key 1001 (one",
            "-- ticket, 5 gold), \"a batch\" key 1010 (ten, 40 gold); the rule book (item 594) comes with the first.",
            "-- Without the gold MM9 plays a character's grumble (NoGold.inc): its text 229 here.",
            "local function sellTickets(count, cost)   -- :SellGameTicket, :SellBatchTickets",
            f"    if MM9.hasGold(cost) ~= 1 then say({lua_string(TEXT[229])}); return end",
            "    evt.PlaySoundName(\"events/gold01.wav\", 0, 0, 0)",
            f"    MM9.takeGold(cost); if {item('has', 594)} ~= 1 then {item('give', 594)} end",
            f"    for _ = 1, count do {item('give', 557)} end",
            f"    say(count == 1 and {lua_string(TEXT[227])} or {lua_string(TEXT[234])})",
            "end",
            f"handlers[{rude_exit(build, 'TicketMaster')}] = function()",
            "    if has(1001) then MM9.takeKey(1001); sellTickets(1, 5)",
            "    elseif has(1010) then MM9.takeKey(1010); sellTickets(10, 40) end",
            "end",
            "",
        ]
        registrations.append((rude_exit(build, "TicketMaster"), "The Huckster", None))

    # --- the stones game ---------------------------------------------------------------------------------------------
    if all(name in cogs and name in events for name in PIECES):
        piece_cogs = ", ".join(str(cogs[name]) for name in PIECES)
        lines += [
            "-- StonesGame.scr \"Square 6\" (TronMgr), StonesSquare.scr (Square0-35), StonesPiece.scr (Piece0-35),",
            "-- StonesPlayer.scr (TronPlayer, the bot). A 6 x 6 board, map vars St0-St35: 0 empty, 1 white (the party),",
            "-- 2 black (the bot). A move goes on an empty square next to (8 ways) a stone of the mover's colour; after",
            "-- each move, the side to move without a legal square loses (MM9's scan skips the last square). The first",
            "-- move of a game takes a ticket. The board is set again on every load (:InitStonesGame).",
            f"local ST_COGS = {{{piece_cogs}}}",
            "local ST_OFFSETS = {-5, 1, 7, -6, 6, -7, -1, 5}   -- :SetupCheck (BOARDSIZE 6); 1-3 right, 6-8 left",
            "local function stDraw(i, colour)   -- StonesPiece.scr :TurnWhite / :TurnBlack; empty keeps a grey stone",
            "    local key = ST_COGS[i + 1]",
            f"    if colour == 1 then evt.SetSprite(key, 1, \"{STONE_WHITE}\")",
            f"    elseif colour == 2 then evt.SetSprite(key, 1, \"{STONE_BLACK}\")",
            f"    else evt.SetSprite(key, 1, \"{STONE_EMPTY}\") end",
            "end",
            "local function stSet(i, colour) set(\"St\" .. i, colour); stDraw(i, colour) end",
            "local function stLegal(i, colour)   -- :CheckSurrounding",
            "    if var(\"St\" .. i) ~= 0 then return false end",
            "    for n, offset in ipairs(ST_OFFSETS) do",
            "        local j = i + offset",
            "        local edge = ((i + 1) % 6 == 0 and n <= 3) or (i % 6 == 0 and n >= 6) or j < 0 or j > 35",
            "        if not edge and var(\"St\" .. j) == colour then return true end",
            "    end",
            "    return false",
            "end",
            "local function stCanMove(colour)   -- :CheckVictory (while nCurSquare < LISTLAST: squares 0-34)",
            "    for i = 0, 34 do if stLegal(i, colour) then return true end end",
            "    return false",
            "end",
            "local function stReset()   -- :ResetVars, :ResetBoard: one white and the mirrored black at random",
            "    for i = 0, 35 do stSet(i, 0) end",
            "    local r = rnd(0, 35)",
            "    stSet(r, 1); stSet(35 - r, 2); set(\"StTicket\", 0); set(\"StTurn\", 0)",
            "end",
            "-- A slain stones player (TronPlayer) takes no \"play\" (MM9.receives): the board waits on black, and the",
            "-- party's next click places black (:CheckMove alternates the colours whoever clicks). Map var StTurn 2.",
            f"local ST_BOT = {npc.get('TronPlayer', 'nil')}",
            "local function stMove(i)   -- StonesSquare.scr :RequestMove -> StonesGame.scr :CheckMove",
            "    if var(\"StTicket\") == 0 then",
            "        if not ticket() then return end",
            "        set(\"StTicket\", 1)",
            "    end",
            "    if var(\"StTurn\") == 2 then   -- black's turn (:HandleInvalidMove sends the dead bot \"play\": nothing)",
            "        if not stLegal(i, 2) then return end",
            "        stSet(i, 2); set(\"StTurn\", 0)",
            f"        if not stCanMove(1) then say({lua_string(TEXT[231])}); stReset(); return end",
            f"        say({lua_string(TEXT[244])})",
            "        return",
            "    end",
            f"    if not stLegal(i, 1) then say({lua_string(TEXT[233])}); return end   -- :HandleInvalidMove",
            "    stSet(i, 1)",
            f"    if not stCanMove(2) then say({lua_string(TEXT[230])}); gameWon(7100); stReset(); return end",
            "    if not MM9.receives(\"thjorgard\", \"TronPlayer\", \"play\", ST_BOT) then set(\"StTurn\", 2); return end",
            "    local legal = {}   -- StonesPlayer.scr :PlacePiece: random squares until a legal one",
            "    for j = 0, 35 do if stLegal(j, 2) then legal[#legal + 1] = j end end",
            "    stSet(legal[rnd(1, #legal)], 2)",
            f"    if not stCanMove(1) then say({lua_string(TEXT[231])}); stReset(); return end",
            f"    say({lua_string(TEXT[244])})",
            "end",
        ]
        for k, name in enumerate(PIECES):
            lines.append(f"handlers[{events[name]}] = function() stMove({k}) end   -- {name} (Square{k})")
            registrations.append((events[name], "Stone", "Stone"))
        lines.append("")
        if getattr(hooks, "npc_rude", {}).get("TronPlayer"):
            # His DAT row has NPCNbr 0: npcs() places him without a RUDE id, so these run once it gives him one
            lines += [
                "-- StonesPlayer.scr :OnRudeEnter / :OnRudeExit (TronPlayer): key 7002 opens his row of RUDE 428.",
                f"handlers[{rude_use(build, 'TronPlayer')}] = function() MM9.giveKey(7002); MM9.openRude(428) end",
                f"handlers[{rude_exit(build, 'TronPlayer')}] = function() MM9.takeKey(7002) end",
                "",
            ]
            registrations += [(rude_use(build, "TronPlayer"), "Stones player", None),
                              (rude_exit(build, "TronPlayer"), "Stones player", None)]
        load.append("    stReset()   -- StonesGame.scr :InitStonesGame")

    # --- the runes game ----------------------------------------------------------------------------------------------
    switch_event = group_event(build, "Switch")
    if all(name in events for name in BUTTONS) and all(name in cogs and name in events for name in SPACES) \
            and switch_event is not None:
        switch = group_doors(build, "Switch")
        # the stones as seen from the colour buttons (west of them, facing +x: the left is +z in LithTech)
        by_z = sorted(range(4), key=lambda k: -build.source.by_name[SPACES[k].lower()]["properties"]["Pos"][2])
        ordinal = [by_z.index(k) + 1 for k in range(4)]
        lines += [
            "-- Mastermind.scr \"FireCorrect\", MastermindColor.scr (ColorButton0-4), MastermindSpace.scr (ColorSpace0-3)",
            "-- and the Switch door (OpenTrigger \"check\"). Map vars: MMCode1-4 the hidden colours (0-4), MMPick1-4 the",
            "-- chosen ones (colour + 1), MMColor the button last pressed, MMChances, MMTicket (paid this round). A new",
            "-- code on every load, after a win and after the fourth miss (:GenerateColors keeps the chosen stones).",
            f"local MM_COGS = {{{', '.join(str(cogs[name]) for name in SPACES)}}}",
            f"local MM_PLACE = {{{', '.join(str(n) for n in ordinal)}}}   -- each stone's place from the left",
            "local function mmPaint(slot, colour)   -- MastermindSpace.scr :ChangeColor (SetModelFilenames)",
            "    local key = MM_COGS[slot]",
        ]
        for colour, name in enumerate(RUNE_STONES):
            lines.append(f"    {'if' if colour == 0 else 'elseif'} colour == {colour} then "
                         f"evt.SetSprite(key, 1, \"{name}\")")
        lines += [
            f"    else evt.SetSprite(key, 1, \"{RUNE_PLAIN}\") end",
            "end",
            "local function mmNew()   -- :GenerateColors",
            "    for i = 1, 4 do set(\"MMCode\" .. i, rnd(0, 4)) end",
            "    set(\"MMChances\", 4); set(\"MMTicket\", 0)",
            "end",
            "local function mmPaid()   -- bNeedsTicket: the first pick or check of a round takes a ticket",
            "    if var(\"MMTicket\") == 1 then return true end",
            "    if not ticket() then return false end",
            "    set(\"MMTicket\", 1)",
            "    return true",
            "end",
        ]
        for k, name in enumerate(BUTTONS):
            lines.append(f"handlers[{events[name]}] = function() evt.PlaySoundName(\"door/trapdooropen.wav\", 0, 0, 0); "
                         f"set(\"MMColor\", {k}) end   -- {name} (MastermindColor.scr :ChangeColor)")
            registrations.append((events[name], "Rune stone", "Stone"))
        for k, name in enumerate(SPACES):
            lines += [
                f"handlers[{events[name]}] = function()   -- {name} (MastermindSpace.scr :UpdateColor; Mastermind.scr "
                ":ColorChosen)",
                "    local colour = var(\"MMColor\")",
                f"    if var(\"MMChances\") > 0 and mmPaid() then set(\"MMPick{k + 1}\", colour + 1) end",
                f"    evt.PlaySoundName(\"door/doorlatch01.wav\", 0, 0, 0); mmPaint({k + 1}, colour)",
                "end",
            ]
            registrations.append((events[name], "Rune stone", "Stone"))
        presses = " ".join(f"evt.SetDoorState({d}, DoorAction.Open)" for d in switch)
        releases = " ".join(f"evt.SetDoorState({d}, DoorAction.Close)" for d in switch)
        lines += [
            "-- The Switch (a push door: its open sends \"check\"): it goes down on a click and back up on the next tick.",
            "-- Mastermind.scr :CompareColors lights a flame by each right stone (told here), then :Correct (MM9 plays",
            "-- spells\\bless.wav, not among the imported sounds: the quest sound) or :Incorrect.",
            f"handlers[{switch_event}] = function()",
            f"    {presses}; set(\"MMSwitch\", 1)",
            "    if var(\"MMChances\") <= 0 or not mmPaid() then return end",
            "    local right = {}",
            "    for i = 1, 4 do",
            "        if var(\"MMPick\" .. i) == var(\"MMCode\" .. i) + 1 then right[#right + 1] = MM_PLACE[i] end",
            "    end",
            "    local chances = var(\"MMChances\") - 1",
            "    set(\"MMChances\", chances)",
            "    if #right == 4 then quest(); mmNew(); gameWon(7102); return end",
            "    table.sort(right)",
            "    local flames = #right == 0 and tr(\"No flame burns.\")",
            "        or tr(\"Flames burn by stone {stones} (from the left).\", {stones = table.concat(right, \", \")})",
            f"    local left = {{{lua_string(TEXT[243])}, {lua_string(TEXT[242])}, {lua_string(TEXT[241])}}}",
            "    if chances == 0 then say(flames .. \" \" .. "
            f"tr({lua_string(TEXT[7])})); mmNew() else say(flames .. \" \" .. tr(left[chances])) end",
            "end",
            "",
        ]
        registrations.append((switch_event, "Switch", "Switch"))
        load += ["    mmNew()   -- Mastermind.scr :InitMastermind",
                 "    for i = 1, 4 do set(\"MMPick\" .. i, 0); mmPaint(i, -1) end",
                 f"    set(\"MMColor\", 0); if var(\"MMSwitch\") == 1 then set(\"MMSwitch\", 0); {releases} end"]
        tick.append(f"    if var(\"MMSwitch\") == 1 then set(\"MMSwitch\", 0); {releases} end")

    # --- the boat race -----------------------------------------------------------------------------------------------
    if "BoatJudge" in npc and PLAYER_BOAT in events:
        count = ", ".join(lua_string(TEXT[n]) for n in (239, 238, 237, 236))
        lines += [
            "-- BoatJudge.scr \"RacingBoat 0 3\" (RUDE 429) and RacingBoat.scr. A click gives key 7003 (his rows about",
            "-- the race); leaving with key 7004 (\"Sure!\") and a ticket starts the countdown (Countdown5: Five... One...,",
            "-- the bell), then the race. The party's boat moves one length (a tenth of the way, one second) per hit;",
            "-- here per click, not again while it moves. The three rival boats move a length in two to four seconds",
            "-- each (here a random share every half second). Map vars: BoatState (0 idle, 1 countdown, 2 racing),",
            "-- BoatCount (countdown ticks), BoatPushes, BoatMoving (ticks), BoatAI1-3 (hundredths of a length).",
            f"local BOAT_COUNT = {{{count}}}",
            f"handlers[{rude_use(build, 'BoatJudge')}] = function() MM9.giveKey(7003); MM9.openRude(429) end   -- :OnUse",
            f"handlers[{rude_exit(build, 'BoatJudge')}] = function()   -- :StartRace",
            "    MM9.takeKey(7003)",
            "    if not has(7004) then return end",
            "    MM9.takeKey(7004)",
            "    if var(\"BoatState\") ~= 0 or not ticket() then return end",
            "    set(\"BoatState\", 1); set(\"BoatCount\", 10); set(\"BoatPushes\", 0); set(\"BoatMoving\", 0)",
            "    for b = 1, 3 do set(\"BoatAI\" .. b, 0) end",
            f"    evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0); say({lua_string(TEXT[235])})",
            "end",
            f"handlers[{events[PLAYER_BOAT]}] = function()   -- {PLAYER_BOAT} (RacingBoat.scr :Ready -> :MoveForward)",
            "    if var(\"BoatState\") ~= 2 or var(\"BoatMoving\") > 0 then return end",
            "    set(\"BoatPushes\", var(\"BoatPushes\") + 1); set(\"BoatMoving\", 2)",
            f"    say(tr(\"Your boat: {{pushes}} of {BOAT_LENGTHS} lengths.\", {{pushes = var(\"BoatPushes\")}}))",
            "end",
            "local function boatEnd(won)   -- BoatJudge.scr :PlayerWon / :AIWon, then the boats submerge and reset",
            "    set(\"BoatState\", 0)",
            "    -- RacingBoat.scr :Arrived sends the judge PlayerArrival / CPUArrival: a slain judge takes neither (no",
            "    -- result; the race is over, and no new one starts without his dialogue)",
            f"    if not MM9.receives(\"thjorgard\", \"BoatJudge\", won and \"PlayerArrival\" or \"CPUArrival\", "
            f"{npc['BoatJudge']}) then return end",
            "    if won then evt.PlaySoundName(\"events/trumpets02.wav\", 0, 0, 0); gameWon(7101) else gameLost() end",
            "end",
            "local function boatTick(tick)",
            "    local state = var(\"BoatState\")",
            "    if state == 1 then",
            "        local count = var(\"BoatCount\") - 1",
            "        set(\"BoatCount\", count)",
            "        if count % 2 ~= 0 then return end",
            "        if count > 0 then evt.PlaySoundName(\"door/doorlock01.wav\", 0, 0, 0); say(BOAT_COUNT[math.floor(count / 2)])",
            "        else evt.PlaySoundName(\"events/dingbell.wav\", 0, 0, 0); set(\"BoatState\", 2) end   -- :Countdown0",
            "    elseif state == 2 then",
            "        local moving = var(\"BoatMoving\")",
            "        if moving > 0 then",
            "            set(\"BoatMoving\", moving - 1)",
            f"            if moving == 1 and var(\"BoatPushes\") >= {BOAT_LENGTHS} then boatEnd(true); return end",
            "        end",
            "        local best = 0",
            "        for b = 1, 3 do",
            "            local p = var(\"BoatAI\" .. b) + rnd(12, 25)",
            "            set(\"BoatAI\" .. b, p)",
            "            if p > best then best = p end",
            "        end",
            f"        if best >= {BOAT_LENGTHS * 100} then boatEnd(false); return end",
            "        if tick % 4 == 0 then",
            f"            say(tr(\"Your boat: {{pushes}} of {BOAT_LENGTHS} lengths; the leading rival: {{rival}}.\",",
            "                {pushes = var(\"BoatPushes\"), rival = math.floor(best / 100)}))",
            "        end",
            "    end",
            "end",
            "",
        ]
        registrations += [(rude_use(build, "BoatJudge"), "Boat judge", None),
                          (rude_exit(build, "BoatJudge"), "Boat race", None),
                          (events[PLAYER_BOAT], "Toy boat", "Boat")]
        load.append("    set(\"BoatState\", 0)   -- RacingBoat.scr :InitRacingBoat (a race does not survive a load)")
        tick.append("    boatTick(tick)")

    # --- the bell ----------------------------------------------------------------------------------------------------
    strike_event = group_event(build, "Strikeplate1")
    riser = [m for m in build.movers if m["group"] == "Riser1"]
    if strike_event is not None and riser:
        strike = group_doors(build, "Strikeplate1")
        rise_seconds = max(m["move_length"] / max(1, m["open_speed"]) for m in riser)
        up = " ".join(f"evt.SetDoorState({m['door_id']}, DoorAction.Open)" for m in riser)
        down = " ".join(f"evt.SetDoorState({m['door_id']}, DoorAction.Close)" for m in riser)
        press = " ".join(f"evt.SetDoorState({d}, DoorAction.Open)" for d in strike)
        release = " ".join(f"evt.SetDoorState({d}, DoorAction.Close)" for d in strike)
        lines += [
            "-- DingTheBell.scr (Strikeplate1) and BellWeight.scr \"360\" (Riser1). A click with a ticket: ding 60-80,",
            "-- timing 40-60 + the character's Might (GetAttribute 0; the active character here); the weight climbs to",
            "-- timing / ding of its full height (BellWeight :AdjustHeight); it rings and wins when timing > ding",
            "-- (:CheckWin, when the weight stops). The plate takes no click for three seconds after (:BlockUse).",
            "-- Map vars: BellStage (0 idle, 1 rising, 2 waiting), BellWin. The weight's way up takes "
            f"{rise_seconds:.2f} s.",
            f"handlers[{strike_event}] = function()   -- :HitBell",
            "    if var(\"BellStage\") ~= 0 or not ticket() then return end",
            "    local ding, timing = rnd(60, 80), rnd(40, 60) + currentMight()",
            "    set(\"BellWin\", timing > ding and 1 or 0); set(\"BellStage\", 1)",
            f"    {press} {up}",
            f"    evt.StartTimer({EV_BELL}, seconds(math.min(1, timing / ding) * {rise_seconds:.3f}))",
            "end",
            f"handlers[{EV_BELL}] = function()",
            "    local stage = var(\"BellStage\")",
            "    if stage == 1 then   -- the weight at its height: Strikeplate1 \"ring\" -> :CheckWin",
            f"        {down}",
            "        if var(\"BellWin\") == 1 then evt.PlaySoundName(\"events/dingbell.wav\", 0, 0, 0); gameWon(7104)",
            "        else gameLost() end",
            f"        set(\"BellStage\", 2); evt.StartTimer({EV_BELL}, seconds(3))",
            "    else   -- :AllowUse",
            f"        if stage == 2 then {release} end",
            f"        set(\"BellStage\", 0); evt.StopTimer({EV_BELL})",
            "    end",
            "end",
            "",
        ]
        registrations += [(strike_event, "Bell strike plate", "Strike"), (EV_BELL, "Bell", None, "timer")]
        load.append("    set(\"BellStage\", 0)   -- DingTheBell.scr :Main")
    riser_event = group_event(build, "Riser1")
    if riser_event is not None:
        lines += ["-- Riser1 is the bell's weight (PushOpen 0 in MM9): a click does nothing.",
                  f"handlers[{riser_event}] = function() end", ""]
        registrations.append((riser_event, "Bell weight", None))

    # --- whack-a-honky ------------------------------------------------------------------------------------------------
    honk_event = group_event(build, "Switch0")
    if all(name in events and name in cogs for name in HONKIES) and honk_event is not None:
        lever = group_doors(build, "Switch0")
        pull = " ".join(f"evt.SetDoorState({d}, DoorAction.Open)" for d in lever)
        release = " ".join(f"evt.SetDoorState({d}, DoorAction.Close)" for d in lever)
        lines += [
            "-- Whack-a-Honky.scr \"<k> Honky 0 3\" (Honky0-3) and Switch0 (OpenTrigger0 Honky0 \"start\"). A pull with a",
            "-- ticket: Countdown5, then ten seconds (Wait 19, 15 EndGame from the pull) of geese, one up at a time: it",
            "-- rises (0.2 s), waits 0.5-1 s, goes down (0.2 s) and another rises (:OnFinishedLower, never the same one); a",
            "-- click on the raised goose counts (WHACK_COUNTER) and sends it down at once. Eight win (WIN_CONDITION).",
            "-- MM9 raises the geese 20 units from their holes; here the idle geese all stand, and while the game runs",
            "-- only the raised one shows. Map vars: HonkState (0 idle, 1 countdown, 2 playing), HonkStep, HonkUp (1-4,",
            "-- 0 none), HonkLast, HonkHits.",
            f"local HONK_COGS = {{{', '.join(str(cogs[name]) for name in HONKIES)}}}",
            f"local HONK_COUNT = {{{', '.join(lua_string(TEXT[n]) for n in range(235, 240))}}}",
            "local function honkShowAll(on) for i = 1, 4 do evt.SetSprite(HONK_COGS[i], on and 1 or 0, \"0\") end end",
            "local function honkRaise()   -- :ReceivePopup",
            "    local k = rnd(1, 4)",
            "    while k == var(\"HonkLast\") do k = rnd(1, 4) end",
            "    set(\"HonkUp\", k); set(\"HonkLast\", k); evt.SetSprite(HONK_COGS[k], 1, \"0\")",
            f"    evt.StartTimer({EV_HONK}, seconds((200 + rnd(500, 1000)) / 1000))",
            "end",
            "local function honkLower()   -- :SendPopup",
            "    local k = var(\"HonkUp\")",
            "    if k > 0 then evt.SetSprite(HONK_COGS[k], 0, \"0\") end",
            f"    set(\"HonkUp\", 0); evt.StartTimer({EV_HONK}, seconds(0.2))",
            "end",
            "local function honkReset()",
            f"    evt.StopTimer({EV_HONK}); evt.StopTimer({EV_HONK_END})",
            "    set(\"HonkState\", 0); set(\"HonkUp\", 0); honkShowAll(true)",
            f"    {release}",
            "end",
            f"handlers[{honk_event}] = function()   -- Switch0 -> Honky0 :StartGame",
            "    if var(\"HonkState\") ~= 0 or not ticket() then return end",
            f"    {pull}",
            "    set(\"HonkState\", 1); set(\"HonkStep\", 1); set(\"HonkHits\", 0); set(\"HonkLast\", 0)",
            f"    say(HONK_COUNT[1]); evt.StartTimer({EV_HONK}, seconds(1))",
            f"    evt.StartTimer({EV_HONK_END}, seconds(15))",
            "end",
            f"handlers[{EV_HONK}] = function()",
            "    local state = var(\"HonkState\")",
            "    if state == 1 then",
            "        local step = var(\"HonkStep\")",
            f"        if step < 5 then set(\"HonkStep\", step + 1); say(HONK_COUNT[step + 1]); "
            f"evt.StartTimer({EV_HONK}, seconds(1))",
            "        else set(\"HonkState\", 2); honkShowAll(false); honkRaise() end",
            "    elseif state == 2 then",
            "        if var(\"HonkUp\") > 0 then honkLower() else honkRaise() end",
            "    end",
            "end",
            f"handlers[{EV_HONK_END}] = function()   -- :EndGame",
            "    if var(\"HonkState\") ~= 2 then return end",
            "    local hits = var(\"HonkHits\")",
            "    honkReset()",
            "    if hits >= 8 then gameWon(7103) else gameLost() end",
            "end",
        ]
        for k, name in enumerate(HONKIES):
            lines += [
                f"handlers[{events[name]}] = function()   -- {name} :OnDamage",
                f"    if var(\"HonkState\") ~= 2 or var(\"HonkUp\") ~= {k + 1} then return end",
                "    set(\"HonkHits\", var(\"HonkHits\") + 1)",
                "    evt.PlaySoundName(\"ambient/animals/goose honk.wav\", 0, 0, 0)   -- MM9: animsounds\\hen\\fidget01",
                "    honkLower()",
                "end",
            ]
            registrations.append((events[name], "Goose", "Goose"))
        lines.append("")
        registrations += [(honk_event, "Whack-a-honky lever", "Lever"), (EV_HONK, "Whack-a-honky", None, "timer"),
                          (EV_HONK_END, "Whack-a-honky end", None, "timer")]
        load.append("    honkReset()   -- Whack-a-Honky.scr :Main, :ResetPOS")

    # --- the arm wrestler ----------------------------------------------------------------------------------------
    if "HalfOrcCaptain0" in npc:
        wrestle = rude_use(build, "HalfOrcCaptain0")
        wrestler = npc["HalfOrcCaptain0"]
        lines += [
            "-- Armwrestle.scr \"2\" (HalfOrcCaptain0) :OnUse -> :StartMightGame: with a ticket, his 2 + 1-40 against the",
            "-- active character's Might (GetAttribute 0) + 9-50; a tie wins. A win: :StartCower (PlayAnim cowerstart,",
            "-- LoopAnim cower 5, PlayAnim cowerstop), his use removed until it ends (:RemoveUse, :RestoreUse). His body",
            "-- (the Half Orc's) has only the loop, cower: five of it (MM9's DookMilitia.abc has no cowerstop either).",
            f"local WRESTLER = {wrestler}",
            f"handlers[{wrestle}] = function()",
            "    if var(\"Tick\") < var(\"WrestlerCowerUntil\") then return end   -- :RemoveUse while he cowers",
            "    if not ticket() then return end",
            "    local mine, theirs = 2 + rnd(1, 40), currentMight() + rnd(9, 50)",
            "    if theirs >= mine then",
            "        evt.PlayActorClip(WRESTLER, {\"cower\", \"cower\", \"cower\", \"cower\", \"cower\"}, false)",
            f"        set(\"WrestlerCowerUntil\", var(\"Tick\") + "
            f"{math.ceil(5 * lua.model_clip_seconds(monster_of[wrestler])['cower'] * 2)})",
            "        gameWon(7105)",
            "    else gameLost() end",
            "end",
            "",
        ]
        load.append("    set(\"WrestlerCowerUntil\", 0)   -- the cower is not saved")
        registrations.append((wrestle, "Arm wrestler", None))

    # --- people: Hjarrand --------------------------------------------------------------------------------------------
    hjarrand = "ShopkeeperElfFemaleB8"
    if hjarrand in npc:
        lines += [
            "-- NPC7.scr (Hjarrand Fixer, RUDE 7; no Location param: :Payment on the exit). With key 360 (1 000 gold)",
            "-- or 361 (2 000) and the gold: key 362, 363 cleared, the quest sound; without the gold: key 363 (MM9 plays",
            "-- a character's voice). :Init: he is here while key 362 is not held.",
            f"handlers[{rude_exit(build, hjarrand)}] = function()",
            "    if has(362) then return end",
            "    for _, cost in ipairs({{360, 1000}, {361, 2000}}) do",
            "        if has(cost[1]) then",
            "            if MM9.hasGold(cost[2]) == 1 then MM9.takeGold(cost[2]); MM9.giveKey(362); MM9.takeKey(363); quest()",
            "            else MM9.giveKey(363) end",
            "            return",
            "        end",
            "    end",
            "end",
            "",
        ]
        registrations.append((rude_exit(build, hjarrand), "Hjarrand Fixer", None))
        load.append(f"    show({npc[hjarrand]}, not has(362))   -- NPC7.scr :Init")

    # --- Thorgard_actor.scr: the robbers and the Magreeb ambush ------------------------------------------------------
    kens = [a for name in KENS for a in actors.get(name, [])]
    robber = build.source.by_name.get(ROB_TRIGGER.lower())
    if kens and robber is not None:
        p = robber["properties"]
        dims = p.get("Dims") or [50.0, 50.0, 50.0]
        corners = build.project.native([[p["Pos"][0] - dims[0], p["Pos"][1] - dims[1], p["Pos"][2] - dims[2]],
                                        [p["Pos"][0] + dims[0], p["Pos"][1] + dims[1], p["Pos"][2] + dims[2]]])
        low = [int(min(corners[0][i], corners[1][i])) for i in range(3)]
        high = [int(max(corners[0][i], corners[1][i])) for i in range(3)]
        margin = 64                         # the party's body and a half-second step through the small box
        lines += [
            "-- Thorgard_actor.scr :SetupKen (Ken1-3): hidden, not solid, until RobPlayerTrigger sends RobPlayer; at",
            "-- night (18:00-05:00, :IsNightTime) they appear and come for the party (:OnRobPlayer; the walk to their",
            "-- markers and the taunt are the monster AI's). Map var KensOut: they have appeared.",
            f"local KENS = {{{', '.join(map(str, kens))}}}",
            "local KEN_NAMES = {" + ", ".join(f'"{name}"' for name in KENS for _ in actors.get(name, [])) + "}",
            "local function robberTick()",
            "    if var(\"KensOut\") == 1 then return end",
            "    local hour = math.floor(evt.CurrentGameMinutes() / 60) % 24",
            "    if hour < 18 and hour >= 5 then return end",
            "    local x, y, z = evt.GetPartyPosition()",
            f"    if x < {low[0] - margin} or x > {high[0] + margin} or y < {low[1] - margin} or y > {high[1] + margin}"
            f" or z < {low[2] - margin} or z > {high[2]} then return end",
            "    set(\"KensOut\", 1)",
            "    for k, a in ipairs(KENS) do   -- a slain Ken takes no RobPlayer (MM9.receives)",
            "        if MM9.receives(\"thjorgard\", KEN_NAMES[k], \"RobPlayer\", a) then show(a, true) end",
            "    end",
            "end",
            "",
        ]
        load.append("    if var(\"KensOut\") == 0 then for _, a in ipairs(KENS) do show(a, false) end end   -- :SetupKen")
        tick.append("    robberTick()")
    jumpers = [actors.get(name, [None])[0] for name in JUMPERS]
    jumper_trigger = build.source.by_name.get(JUMPER_TRIGGER.lower())
    if None not in jumpers and jumper_trigger is not None:
        p = jumper_trigger["properties"]
        dims = p.get("Dims") or [50.0, 50.0, 50.0]
        corners = build.project.native([[p["Pos"][0] - dims[0], p["Pos"][1] - dims[1], p["Pos"][2] - dims[2]],
                                        [p["Pos"][0] + dims[0], p["Pos"][1] + dims[1], p["Pos"][2] + dims[2]]])
        low = [int(min(corners[0][i], corners[1][i])) for i in range(3)]
        high = [int(max(corners[0][i], corners[1][i])) for i in range(3)]
        margin = 64
        waits = ", ".join(f"{{{round(a * 2)}, {round(b * 2)}}}" for a, b in JUMPER_WAITS)
        clips = lua.model_clip_seconds(monster_of[jumpers[0]])
        jump_ticks = math.ceil((clips["lying_down"] + clips["jumping_down"]) * 2)   # half-second ticks
        lines += [
            "-- Thorgard_actor.scr / Jumper.inc (Jumper0-3, the bandits on the cliff): hidden, not solid, until",
            f"-- {JUMPER_TRIGGER} (once): Jumper0 GetPlayer at once, Jumper1-3 WaitGetPlayer (Jumper.inc 1-2.5 s; Jumper2",
            "-- 10-25 s, Jumper3 30-45 s, Thorgard_actor.scr :JumperWaitGetPlayer); then they appear and come for the party",
            "-- (the leap's clips below; the monster AI takes them on sight). Their DeathTriggerTarget: Jumper0's death sends",
            "-- Jumper2 BuddyDead, Jumper1's Jumper3 (:SetupJumper AddTrigger BuddyDead, JumperGetPlayer: at once).",
            "-- Map vars JumpersSprung, JumperDue<k> (the tick it appears), JumperOut<k>.",
            f"local JUMPERS = {{{', '.join(map(str, jumpers))}}}   -- {', '.join(JUMPERS)}",
            f"local JUMPER_WAIT = {{{waits}}}   -- half-second ticks",
            "local JUMPER_NAMES = {" + ", ".join(f'"{name}"' for name in JUMPERS) + "}",
            "-- A slain jumper takes no GetPlayer, WaitGetPlayer or BuddyDead (MM9.receives); a wait it took still ends.",
            "-- Jumper.inc :JumperGetPlayer (LoopAnim LyingDown while it rises, then :JumpAtTarget LoopAnim JumpingDown",
            "-- until it lands): the two clips in turn, held in place meanwhile (the leap's arc is not carried);",
            "-- map var JumperLands<k>: the tick it is free (a load frees it at once). Freed, it goes for the party",
            "-- (JumpAtTarget's GetPlayer): on the cliff top it seldom sees the party below, and one left waiting there",
            "-- stood on it for good (Jumper3 in the user's save, 2026-11-11); a load sets the free ones on it again.",
            f"local JUMP_TICKS = {jump_ticks}",
            "local function jumpNow(k)",
            "    if var(\"JumperOut\" .. k) == 1 then return end",
            "    set(\"JumperOut\" .. k, 1); set(\"JumperDue\" .. k, 0)",
            "    show(JUMPERS[k], true)",
            "    evt.SetActorImmobile(JUMPERS[k], true)",
            "    evt.PlayActorClip(JUMPERS[k], {\"lying_down\", \"jumping_down\"}, false)",
            "    set(\"JumperLands\" .. k, var(\"Tick\") + JUMP_TICKS)",
            "end",
            "local function jumperLands(k)",
            "    set(\"JumperLands\" .. k, 0)",
            "    evt.SetActorImmobile(JUMPERS[k], false)",
            "    if MM9.actorAlive(JUMPERS[k]) then evt.SetActorTarget(JUMPERS[k], \"party\") end",
            "end",
            "local function jumperTick(tick)",
            "    if var(\"JumpersSprung\") == 0 then",
            "        local x, y, z = evt.GetPartyPosition()",
            f"        if x < {low[0] - margin} or x > {high[0] + margin} or y < {low[1] - margin} or y > {high[1] + margin}"
            f" or z < {low[2] - margin} or z > {high[2]} then return end",
            "        set(\"JumpersSprung\", 1)",
            "        for k = 1, #JUMPERS do",
            "            if var(\"JumperOut\" .. k) == 0 and MM9.receives(\"thjorgard\", JUMPER_NAMES[k], k == 1 and "
            "\"GetPlayer\" or \"WaitGetPlayer\", JUMPERS[k]) then",
            "                set(\"JumperDue\" .. k, tick + rnd(JUMPER_WAIT[k][1], JUMPER_WAIT[k][2]))",
            "            end",
            "        end",
            "    end",
            "    for k = 1, #JUMPERS do",
            "        local due = var(\"JumperDue\" .. k)",
            "        if due > 0 and tick >= due then jumpNow(k) end",
            "        local lands = var(\"JumperLands\" .. k)",
            "        if lands > 0 and tick >= lands then jumperLands(k) end",
            "    end",
            "end",
            f"handlers[{EV_JUMPER_KILLED}] = function(context)   -- a jumper's DeathTriggerTarget: BuddyDead",
            "    local buddy = context.actorIndex == JUMPERS[1] and 3 or context.actorIndex == JUMPERS[2] and 4 or nil",
            "    if buddy ~= nil and MM9.receives(\"thjorgard\", JUMPER_NAMES[buddy], \"BuddyDead\", JUMPERS[buddy]) then "
            "jumpNow(buddy) end",
            "end",
            "",
        ]
        load.append("    for k = 1, #JUMPERS do if var(\"JumperOut\" .. k) == 0 then show(JUMPERS[k], false) end end"
                    "   -- :SetupJumper")
        load.append("    for k = 1, #JUMPERS do if var(\"JumperOut\" .. k) == 1 then jumperLands(k) end end")
        tick.append("    jumperTick(tick)")
        script.hooks.append(f'RegisterMonsterKilledHook({EV_JUMPER_KILLED}, "Jumper killed", '
                            f'handlers[{EV_JUMPER_KILLED}])')
    warning = build.source.by_name.get(WARNING_TRIGGER.lower())
    if warning is not None and warning["properties"].get("ActivationSound"):
        p = warning["properties"]
        dims = p.get("Dims") or [50.0, 50.0, 50.0]
        corners = build.project.native([[p["Pos"][0] - dims[0], p["Pos"][1] - dims[1], p["Pos"][2] - dims[2]],
                                        [p["Pos"][0] + dims[0], p["Pos"][1] + dims[1], p["Pos"][2] + dims[2]]])
        low = [int(min(corners[0][i], corners[1][i])) for i in range(3)]
        high = [int(max(corners[0][i], corners[1][i])) for i in range(3)]
        margin = 37                                     # the party's collision radius: MM9's touch on any part of it
        lines += [
            f"-- {WARNING_TRIGGER} (a plain touch Trigger, ActivationCount 1, no targets): its ActivationSound",
            "-- (Sounds\\Events\\rubble.wav, SoundRadius 600: the party is inside it) once, when the party walks in.",
            "local function warningTick()",
            "    if var(\"RubbleWarned\") == 1 then return end",
            "    local x, y, z = evt.GetPartyPosition()",
            f"    if x < {low[0] - margin} or x > {high[0] + margin} or y < {low[1] - margin} or y > {high[1] + margin}"
            f" or z + 170 < {low[2]} or z > {high[2]} then return end",
            "    set(\"RubbleWarned\", 1)",
            "    evt.PlaySoundName(\"events/rubble.wav\", 0, 0, 0)",
            "end",
            "",
        ]
        tick.append("    warningTick()")
    ambush = [a for name in AMBUSH for a in actors.get(name, [])]
    baby = actors.get("MagreebBaby0", [])
    adult = actors.get("Magreeb0", [])
    if ambush or adult:
        lines += [
            "-- Thorgard_actor.scr :CheckDisable: MagreebBaby0, Jim, Dean, Walter and the Dummies are hidden while the",
            "-- Scholar promotion waits for its Magreeb (key 201 without 202); the adult Magreeb (Scholarpromo.scr) is the",
            "-- one to find then. :MagreebAttackCheck: once a load, the baby within 1 800 units of the party gives key 202",
            "-- (its leap from the water and the bandits' chase are the monster AI's). Scholarpromo.scr :RunAway: the",
            "-- adult on sighting the party (its SightDistance) or hurt (OnDamage; here slain) gives key 202 with the quest",
            "-- sound during the quest and leaves for good (map var MagreebGone). Only once the quest is taken (201): MM9's",
            "-- ran off before it too, and the journal's Thjorgard Magreeb was then gone (2026-11-08).",
            "local function magreebWaits() return has(201) and not has(202) end",
            f"local AMBUSH = {{{', '.join(map(str, ambush))}}}",
            "local function magreebTick()",
        ]
        if baby:
            lines += [
                f"    if var(\"MagreebSeen\") == 0 and not magreebWaits() and evt.IsMapActorWithinPartyDistance({baby[0]},"
                f" {int(1800 * SCALE)}) then",
                "        set(\"MagreebSeen\", 1); MM9.giveKey(202)",
                "    end",
            ]
        if adult:
            sight = float(build.source.by_name["magreeb0"]["properties"].get("SightDistance") or 600.0)
            lines += [
                "    -- :RunAway is its OnFoundPlayer / OnDamage",
                "    if var(\"MagreebGone\") == 0 and has(201) then",
                f"        if not MM9.actorAlive({adult[0]}) then",
                "            if magreebWaits() then MM9.giveKey(202); quest() end",
                "            set(\"MagreebGone\", 1)",
                f"        elseif evt.IsMapActorWithinPartyDistance({adult[0]}, {int(sight * SCALE)}) then",
                "            if magreebWaits() then MM9.giveKey(202); quest() end",
                f"            set(\"MagreebGone\", 1); MM9.removeActor({adult[0]})",
                "        end",
                "    end",
            ]
        lines += ["end", ""]
        load += ["    for _, a in ipairs(AMBUSH) do show(a, not magreebWaits()) end   -- :CheckDisable",
                 "    set(\"MagreebSeen\", 0)"]
        if adult:
            load.append(f"    if var(\"MagreebGone\") == 1 then MM9.removeActor({adult[0]}) end")
        tick.append("    if tick % 2 == 0 then magreebTick() end")

    # --- the tick and the load ---------------------------------------------------------------------------------------
    if tick:
        lines += [
            "-- The games' half-second tick (countdowns, the rival boats, the switch's release) and the polls.",
            f"handlers[{EV_TICK}] = function()",
            "    local tick = var(\"Tick\") % 1000000 + 1",
            "    set(\"Tick\", tick)",
            *tick,
            f"    evt.StartTimer({EV_TICK}, seconds(0.5))",
            "end",
            "",
        ]
        registrations.append((EV_TICK, "Fair games", None, "timer"))
        load.append(f"    evt.StartTimer({EV_TICK}, seconds(0.5))")
    # ExitTrigger3 and ExitTrigger6 to the Training Hall start off (StartOn 0): the wall's break turns ExitTrigger3 on
    # (tomneededatrigger1 "on"), TrainingEnter.scr :Init ExitTrigger6 once key 301 is held. Here key 301 (the wall
    # broken, or the hall's end) turns both on, on load and at the break.
    hall_exits = {name: build.source.by_name[name.lower()]["index"] for name in ("ExitTrigger3", "ExitTrigger6")
                  if name.lower() in build.source.by_name}
    for name, source in hall_exits.items():
        load.append(f"    set(\"Mm9ExitDisabled{source}\", has({KEY_TRAINED}) and 0 or 1)   -- {name} (StartOn 0)")
    hint = build.source.by_name.get("perceptionbrush6")
    wall_hint = 23000 + hint["index"] if hint is not None else None     # its hint's cog (dungeon/perception.py)
    if destructible_events(build):
        lines += [
            "-- TrainingEnter.scr (ScriptObject1) :OnBreak: breaking the training hall's wall (DestructableBrush7) gives",
            f"-- key {KEY_TRAINED}, +5 Might and +5 Intellect (GiveAttribute 0 5 1, 1 5 1: the active member), 20000",
            "-- experience and the quest sound, once (the Training Hall's own end gives the same).",
            f"handlers[{EV_WALL}] = function()",
            *[f"    set(\"Mm9ExitDisabled{source}\", 0)   -- {name} on (tomneededatrigger1 \"on\", :Init)"
              for name, source in hall_exits.items()],
            *([f"    set(\"HintOff{wall_hint}\", 1)   -- PerceptionBrush6 off (tomneededatrigger1, dungeon/perception.py)"]
              if wall_hint else []),
            f"    if MM9.hasKey({KEY_TRAINED}) == 1 then return end",
            f"    MM9.giveKey({KEY_TRAINED})",
            "    AddValue(BaseMight, 5)",
            "    AddValue(BaseIntellect, 5)",
            f"    {experience_lua(20000, KEY_TRAINED)}",
            "    MM9.playSound(\"sounds/events/quest.wav\")",
            "end",
            "",
        ]
        registrations.append((EV_WALL, "Training hall wall broken", None))
    if load:
        lines += ["handlers.regionLoad = function()", *load, "end", ""]
    script.add(lines, *registrations)
