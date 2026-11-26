#!/usr/bin/env python3
"""Plays Xeen quest scenarios through the generated topics and hooks in a stub Lua runtime (A3).

    python3 tools/xeen/quest_stub.py                              every scenario in tools/xeen/quest_stub/
    python3 tools/xeen/quest_stub.py tools/xeen/quest_stub/act1.yml

What it proves: the generated xeen_quests.lua and the hand-written xeen_common.lua load, and each quest's topics and
hooks set the bits, give and take the items, pay the experience and promote the classes the scenario expects, in the
order a player meets them. It is no game run: the engine (evt, qbits, items, classes) is a small Lua stub, map events
that kill a boss are `set:` steps, and the dialogue's text is only printed. The playthrough segments
(tests/playthrough/xeen/) prove the rest in the game.

It builds the world's tables in memory with the driver's modules (tools/xeen/build_world.py; nothing is written) and
runs Lua 5.4, compiled once from the engine's own Lua sources (build-xeen/_deps_src/lua-src or build/_deps/lua-src)
into output/xeen_tools/lua with the system C compiler.

A scenario (YAML):

    name: Act I
    party: [Knight, Paladin, Sorcerer, Ranger]       # the members' classes
    steps:
      - hook: m1.opening                    # XeenQuests.hook(name); `hook: [name, false]` expects it to refuse
      - talk: [4003, Pests]                 # click NPC 4003's topic labelled Pests (it must be shown, and only one)
      - talk: [4003, m2]                    # a quest file's stem: its topics of NPC 4003 (labelled Quest, or the
                                            # afterword the Quest topic becomes after its hand-in), the one shown
      - hidden: [4003, Pests]               # the topic must be hidden now
      - set: m3.clan_king_slain             # what a map event does (a kill, a lever)
      - give: alacorn                       # an item the party picks up (A2 key or engine:<id>); [key, n] for n
      - give: [megacredit, 6]
      - class: [2, Knight]                  # a member changes class (a recruit)
      - gold: 12000                         # the party earns gold elsewhere (counts in `expect: gold`)
      - hour: 22                            # the time of day (Xeen.isNight, time gates); noon by default
      - map: Castle Blackfang               # the map the party is on, its map_stats name (Xeen.onMap)
      - event: 255                          # the map event the next hooks run in (CurrentEventId: a harvest's spot)
      - actual: [Might, 70]                 # the clicking member's current statistic (IsAtLeast(ActualMight, n))
      - answer: "Yes"                       # answer the last topic's question (`ask:`: the button Yes or No)
      - player_bit: 11302                   # a player bit of the clicking member (the stub has one clicking member)
      - lua: 'Xeen.alamarSundial("fire", 1, 1)'  # any Lua: a map event calling a xeen_common.lua helper (evt map vars)
      - expect: {qbit: m4.done, not_qbit: m4.started, item: alacorn, no_item: crystal_key, class: [0, Cavalier],
                 xp: 15750, gold: 3600, award: m4.crusaders}
      - expect: {count: [megacredit, 1], stat: [Personality, 5]}   # items carried; a base stat's total gain
      - expect: {stat: [Food, 20]}                                  # Food, Age, resistances (FireResistance) and
                                                                    # conditions (Insane: 1) are counted like stats
      - expect: {player_bit: 11296, last: "For the eyes"}          # a player bit; the last line shown contains
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_world  # noqa: E402
import gen_quests  # noqa: E402
import xeenlib  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent / 'quest_stub'
LUA_DIR = xeenlib.ROOT / 'output' / 'xeen_tools'
LUA_SOURCES = [xeenlib.ROOT / 'build-xeen' / '_deps_src' / 'lua-src' / 'src', xeenlib.ROOT / 'build' / '_deps' / 'lua-src' / 'src']
COMMON = xeenlib.WORLD / 'events' / 'common' / 'xeen_common.lua'

RUNTIME = r'''
local bits, items, awards, notes, xp, gold, classes = {}, {}, {}, {}, 0, 0, {}
local last = ""
Stub = {bits = bits, items = items, awards = awards, notes = notes}
events, canshow = {}, {}
evt = {}
function QBit(n) return n end
function Award(n) return n end
function InventoryItem(n) return "item" end
Experience, Gold = "xp", "gold"
Players = {All = "all", Member0 = 0, Current = "current"}
ItemType = {Any = 0}
local function say(kind, text) last = text; print("    " .. kind .. ": " .. string.sub(tostring(text), 1, 100)) end
function IsQBitSet(n) return bits[n] == true end
local playerBits = {}
Stub.playerBits = playerBits
function PlayerBit(n) return n end
function IsPlayerBitSet(n) return playerBits[n] == true end
function SetPlayerBit(n) playerBits[n] = true end
function ClearPlayerBit(n) playerBits[n] = nil end
function Stub.last() return last end
function SetQBit(n) bits[n] = true end
function ClearQBit(n) bits[n] = nil end
function HasItem(n) return (items[n] or 0) > 0 end
-- D-90 5: every item the party ever held (the engine's Party::recordEverOwnedItem); a scenario's `give:` counts too.
local everOwned = {}
Stub.everOwned = everOwned
function HasEverOwnedItem(n) return everOwned[n] == true or (items[n] or 0) > 0 end
function RemoveItem(n) if (items[n] or 0) > 0 then everOwned[n] = true end items[n] = (items[n] or 0) - 1 end
function AddValue(kind, v)
    if kind == "item" then items[v] = (items[v] or 0) + 1 everOwned[v] = true
    elseif kind == "xp" then xp = xp + v
    elseif kind == "gold" then gold = gold + v
    else Stub.stats[kind] = (Stub.stats[kind] or 0) + v end
end
function SubtractValue(kind, v) gold = math.max(0, gold - v) end
function IsAtLeast(kind, v) if kind == Gold then return gold >= v end return (Stub.actual[kind] or 0) >= v end
function SetAward(n) awards[n] = true end
function HasAward(n) return awards[n] == true end
function SetAutonote(n) notes[n] = true end
function NPCText(id, text) return text end
function evt.SetMessage(t) say("says", t) end
function evt.SimpleMessage(t) say("message", t) end
function evt.StatusText(t) say("status", t) end
function evt.ForPlayer() end
const = {Damage = {Fire = 0, Air = 1, Water = 2, Earth = 3, Physical = 4, Magic = 5, Mind = 7, Energy = 12}}
function evt.DamagePlayer(who, kind, amount) say("damage", amount .. " to the party") end
function evt.PlaySoundName(name) say("sound", name) end
function evt.CameraShake(intensity, seconds) say("shake", intensity .. " for " .. seconds .. " s") end
Stub.random = 1
function evt.RandomBetween(a, b) return Stub.random end
-- The run's rules: a solo run (D-191, m21.arrival) is a `lua: "Stub.solo = true"` step.
Stub.solo = false
function evt.RulesetInfo() return {soloRun = Stub.solo == true} end
ActorKillCheck = {Group = 1}
Stub.killed = {}
function evt.CheckMonstersKilled(kind, group) return Stub.killed[group] == true end
Stub.position = {0, 0, 0}
function evt.GetPartyPosition() return Stub.position[1], Stub.position[2], Stub.position[3] end
function evt.SetNPCGreeting(npc, greeting) say("greeting", "NPC " .. npc .. " greets with " .. greeting) end
-- A map without the cinematic runs its done event at once (GameSession::playCinematic); so does the stub.
function evt.PlayCinematic(id, done) say("cinematic", id) if done ~= nil and done ~= 0 then events[done]() end end
function evt.MoveNPC(npc, house) say("moves", "NPC " .. npc .. " to house " .. house) end
function evt.MoveToMap(x, y, z, yaw, a, b, c, d, map) say("travels", map .. " " .. x .. " " .. y .. " " .. z) end
function evt.SetOutdoorSky(name) say("sky", name) end
MonsterBits = {Invisible = 1, Hostile = 2}
function evt.SetMonGroupBit(group, bit, on) say("group", "monster group " .. group .. " bit " .. bit .. " = " .. on) end
function evt.GiveItem(level) say("treasure", "a random item of treasure level " .. level) end
function AskChoiceWithAnswerSteps(eventId, fallback, question, answers)
    say("asks", question) Stub.prompt = {eventId = eventId, fallback = fallback, answers = answers}
end
function AskQuestionWithAnswerSteps(eventId, fallback, question, answers)
    say("asks", question) Stub.prompt = {eventId = eventId, fallback = fallback, answers = answers}
end
local mapVars = {}
function evt.GetMapVar(name, default) if mapVars[name] == nil then return default or 0 end return mapVars[name] end
function evt.SetMapVar(name, v) mapVars[name] = v end
function CurrentEventId() return Stub.event or 0 end
function RegisterGlobalEvent(id, title, fn) events[id] = fn end
function RegisterCanShowTopic(id, fn) canshow[id] = fn end
function PartyMembers() local list = {} for i = 0, #classes do table.insert(list, i) end return list end
function GetPlayerClassName(i) return classes[i] end
function SetPlayerClass(i, c) say("promotes", "member " .. i .. " " .. classes[i] .. " -> " .. c) classes[i] = c return true end
-- Items are the party's, held by member 0 (gems, Megacredits); stats are counted per name.
function PlayerItemCount(i, id) if i == 0 then return items[id] or 0 end return 0 end
-- tr() as the game's: the English with its {placeholders} filled in.
function tr(text, args)
    return (text:gsub("{(%w+)}", function(key) if args and args[key] ~= nil then return tostring(args[key]) end end))
end
function evt.CountItems(low, high) local count = 0 for id = low, high do count = count + (items[id] or 0) end return count end
function RemovePlayerItem(i, id, n) everOwned[id] = true items[id] = (items[id] or 0) - (n or 1) return true end
local stats = {}
for _, name in ipairs({"Might", "Intellect", "Personality", "Endurance", "Accuracy", "Speed", "Luck"}) do
    _G["Base" .. name] = "stat:" .. name
    _G["Actual" .. name] = "actual:" .. name
end
Stub.actual = {}
Stub.stats = stats
Food, Age = "stat:Food", "stat:Age"
-- Resistances and conditions of the clicking member, counted per name like stats.
for _, name in ipairs({"FireResistance", "AirResistance", "WaterResistance", "EarthResistance", "MindResistance",
                       "BodyResistance", "Afraid", "Drunk", "Insane", "Weak", "Unconscious", "Cursed", "Stoned", "MightBonus",
                       "IntellectBonus", "PersonalityBonus", "EnduranceBonus", "AccuracyBonus", "SpeedBonus",
                       "LuckBonus", "FireResistanceBonus", "AirResistanceBonus", "WaterResistanceBonus",
                       "EarthResistanceBonus"}) do
    _G[name] = "stat:" .. name
end
function SetValue(kind, v) Stub.stats[kind] = v end
Stub.minutes = 12 * 60
function CurrentGameMinutes() return Stub.minutes end
Stub.map = ""
function evt.GetCurrentMapName() return Stub.map end
Stub.classes = classes
function Stub.xp() return xp end
function Stub.gold() return gold end
function Stub.shown(id) return canshow[id] == nil or canshow[id]() end
-- The answer to the last AskChoiceWithAnswerSteps (a button's label) or AskQuestionWithAnswerSteps (typed) of a global
-- event (a topic's `ask:` has the buttons Yes and No): any case, trimmed.
function Stub.answer(text, message)
    local prompt = Stub.prompt
    assert(prompt ~= nil and events[prompt.eventId] ~= nil, message)
    Stub.prompt = nil
    local typed = string.lower((text:gsub("^%s+", ""):gsub("%s+$", "")))
    local step = prompt.fallback
    for _, answer in ipairs(prompt.answers) do
        if string.lower(answer.Answer) == typed then step = answer.Step break end
    end
    events[prompt.eventId](step)
end
function Stub.pick(ids, message)
    local picked = nil
    for _, id in ipairs(ids) do
        if Stub.shown(id) then
            -- Two shown topics with one label are ambiguous to a player too (two "Quest" topics at once).
            assert(picked == nil, message .. " (ambiguous: topics " .. tostring(picked) .. " and " .. id .. ")")
            picked = id
        end
    end
    if picked == nil then error(message) end
    return picked
end
'''


def lua_binary() -> Path:
    binary = LUA_DIR / 'lua'
    if binary.exists():
        return binary
    source = next((path for path in LUA_SOURCES if (path / 'lapi.c').exists()), None)
    compiler = shutil.which('cc') or shutil.which('gcc')
    if source is None or compiler is None:
        xeenlib.fail('no Lua: need the engine\'s Lua sources (a configured build tree) and a C compiler')
    LUA_DIR.mkdir(parents=True, exist_ok=True)
    files = [str(path) for path in sorted(source.glob('*.c')) if path.name != 'luac.c']
    print(f'compiling Lua from {source.relative_to(xeenlib.ROOT)} into {binary.relative_to(xeenlib.ROOT)}')
    result = subprocess.run([compiler, '-O1', '-w', '-o', str(binary), *files, '-lm'], capture_output=True, text=True)
    if result.returncode != 0:
        xeenlib.fail(f'compiling Lua failed:\n{result.stderr}')
    return binary


def build_tables():
    ctx = xeenlib.BuildContext(xeenlib.World())
    build_world.run_modules(ctx, [])
    lua = ctx.texts['events/common/xeen_quests.lua'][0]
    lua = '\n'.join(line for line in lua.split('\n') if not line.startswith('#'))
    topics = {}
    for row in ctx.tables['npc_topic.txt'].rows:
        topics.setdefault((int(row[6]), row[1]), []).append(int(row[0]))
    # A quest file's stem names its Quest topics of an NPC and their afterwords (QUESTS_FORMAT 4.4).
    model = gen_quests.load_model()
    for record in model.topics:
        if record['label'] == 'Quest' or record.get('afterword_of'):
            topics.setdefault((record['npc'], record['file']['_stem']), []).append(record['id'])
    for key, ids in topics.items():
        topics[key] = sorted(set(ids))
    return ctx, lua, topics


def lua_str(text) -> str:
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"') + '"'


def scenario_lua(scenario: dict, items: dict, topics: dict) -> str:
    def item(key):
        key = str(key)
        if key.startswith('engine:'):
            return int(key.split(':', 1)[1])
        if key not in items:
            raise xeenlib.BuildError(f'scenario: unknown item {key}')
        return int(items[key])

    def topic(pair):
        npc, label = pair
        if (int(npc), label) not in topics:
            raise xeenlib.BuildError(f'scenario: NPC {npc} has no topic {label!r}')
        # Topics of one NPC may share a label when they never show together (Ellinger's discs, M19 then M26), and a
        # quest file's stem names its Quest topics and their afterwords.
        return '{' + ', '.join(str(value) for value in topics[(int(npc), label)]) + '}'

    lines = []
    for index, name in enumerate(scenario.get('party') or []):
        lines.append(f'Stub.classes[{index}] = {lua_str(name)}')
    lines.append('local q = XeenQuests.qbits')
    lines.append('local function bit(name) assert(q[name], "unknown qbit " .. name) return q[name] end')
    for number, step in enumerate(scenario.get('steps') or [], 1):
        where = f'step {number}'
        (kind, value), = step.items()
        lines.append(f'print({lua_str(f"{where}: {kind} {value}")})')
        if kind == 'hook':
            name, expected = (value, True) if isinstance(value, str) else (value[0], bool(value[1]))
            lines.append(f'assert(XeenQuests.hook({lua_str(name)}) == {str(expected).lower()}, '
                         f'{lua_str(where + ": hook " + name + " did not return " + str(expected).lower())})')
        elif kind == 'talk':
            lines.append(f'events[Stub.pick({topic(value)}, {lua_str(where + ": topic hidden")})]()')
        elif kind == 'hidden':
            lines.append(f'for _, id in ipairs({topic(value)}) do assert(not Stub.shown(id), '
                         f'{lua_str(where + ": topic shown")}) end')
        elif kind == 'set':
            lines.append(f'SetQBit(bit({lua_str(value)}))')
        elif kind == 'give':
            key, count = (value, 1) if not isinstance(value, list) else (value[0], int(value[1]))
            lines.append(f'Stub.items[{item(key)}] = (Stub.items[{item(key)}] or 0) + {count}')
        elif kind == 'gold':
            lines.append(f'AddValue(Gold, {int(value)})')
        elif kind == 'actual':
            lines.append(f'Stub.actual["actual:{value[0]}"] = {int(value[1])}')
        elif kind == 'player_bit':
            lines.append(f'SetPlayerBit({int(value)})')
        elif kind == 'answer':
            lines.append(f'Stub.answer({lua_str(str(value))}, {lua_str(where + ": no question asked")})')
        elif kind == 'lua':
            lines.append(str(value))
        elif kind == 'hour':
            lines.append(f'Stub.minutes = {int(value)} * 60')
        elif kind == 'map':
            lines.append(f'Stub.map = {lua_str(value)}')
        elif kind == 'event':
            lines.append(f'Stub.event = {int(value)}')
        elif kind == 'class':
            lines.append(f'Stub.classes[{int(value[0])}] = {lua_str(value[1])}')
        elif kind == 'expect':
            for key, expected in value.items():
                message = lua_str(f'{where}: expected {key} {expected}')
                checks = {
                    'qbit': lambda v: f'IsQBitSet(bit({lua_str(v)}))',
                    'not_qbit': lambda v: f'not IsQBitSet(bit({lua_str(v)}))',
                    'item': lambda v: f'HasItem({item(v)})',
                    'no_item': lambda v: f'not HasItem({item(v)})',
                    'class': lambda v: f'Stub.classes[{int(v[0])}] == {lua_str(v[1])}',
                    'xp': lambda v: f'Stub.xp() == {int(v)}',
                    'gold': lambda v: f'Stub.gold() == {int(v)}',
                    'count': lambda v: f'(Stub.items[{item(v[0])}] or 0) == {int(v[1])}',
                    'stat': lambda v: f'(Stub.stats["stat:" .. {lua_str(v[0])}] or 0) == {int(v[1])}',
                    'player_bit': lambda v: f'IsPlayerBitSet({int(v)})',
                    'no_player_bit': lambda v: f'not IsPlayerBitSet({int(v)})',
                    'last': lambda v: f'string.find(tostring(Stub.last()), {lua_str(v)}, 1, true) ~= nil',
                }
                if key in ('journal', 'no_journal'):
                    # a Current Quests line (english/quests.txt, by its qbit's name): visible while every required
                    # bit is set and no forbidden one is, as JournalQuestTable::isVisible
                    for single in expected if isinstance(expected, list) else [expected]:
                        test = f'Stub.journalVisible(bit({lua_str(single)}))'
                        lines.append(f'assert({"" if key == "journal" else "not "}{test}, '
                                     f'{lua_str(f"{where}: expected {key} {single}")})')
                    continue
                if key == 'award':
                    lines.append(f'assert(Stub.awards[XeenStubAwards[{lua_str(expected)}]], {message})')
                    continue
                if key not in checks:
                    raise xeenlib.BuildError(f'{where}: unknown expectation {key}')
                values = expected if key in ('qbit', 'not_qbit', 'item', 'no_item') and isinstance(expected, list) \
                    else [expected]
                for single in values:
                    lines.append(f'assert({checks[key](single)}, {message})')
        else:
            raise xeenlib.BuildError(f'{where}: unknown step {kind}')
    lines.append('print(string.format("  xp per member %d, gold %d", Stub.xp(), Stub.gold()))')
    return '\n'.join(lines) + '\n'


def run(paths: list[Path]) -> int:
    lua = lua_binary()
    ctx, quests_lua, topics = build_tables()
    awards = {}
    import gen_quests  # noqa: E402 - after the driver put it on the path
    model = gen_quests.load_model()
    for (stem, name), number in model.awards.items():
        awards[f'{stem}.{name}'] = number
    award_lua = 'XeenStubAwards = {' + ', '.join(f'[{lua_str(k)}] = {v}' for k, v in awards.items()) + '}\n'
    journal = []
    for row in ctx.tables['english/quests.txt'].rows:
        lists = [[int(v) for v in str(cell).split(',') if str(v).strip()] for cell in (row[4], row[5])]
        journal.append(f'[{int(row[0])}] = {{req = {{{", ".join(map(str, lists[0]))}}}, '
                       f'forb = {{{", ".join(map(str, lists[1]))}}}}}')
    award_lua += ('XeenStubJournal = {' + ', '.join(journal) + '}\n'
                  'function Stub.journalVisible(id)\n'
                  '    local row = XeenStubJournal[id]\n'
                  '    if not row then return false end\n'
                  '    for _, b in ipairs(row.req) do if not IsQBitSet(b) then return false end end\n'
                  '    for _, b in ipairs(row.forb) do if IsQBitSet(b) then return false end end\n'
                  '    return true\n'
                  'end\n')
    failures = 0
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        for path in paths:
            scenario = xeenlib.load_yaml(path) or {}
            script = folder / 'run.lua'
            script.write_text(RUNTIME + '\n' + COMMON.read_text(encoding='utf-8') + '\n' + quests_lua + '\n' + award_lua
                              + scenario_lua(scenario, ctx.shared.get('items') or {}, topics), encoding='utf-8')
            print(f"== {scenario.get('name', path.stem)} ({path.relative_to(xeenlib.ROOT)})", flush=True)
            result = subprocess.run([str(lua), str(script)])
            if result.returncode != 0:
                failures += 1
                print(f'FAILED: {path.name}', flush=True)
            else:
                print(f'passed: {path.name}', flush=True)
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('scenarios', nargs='*', type=Path, help='scenario files (default: all in tools/xeen/quest_stub/)')
    args = parser.parse_args()
    paths = [path.resolve() for path in args.scenarios] or sorted(SCENARIOS.glob('*.yml'))
    try:
        sys.exit(run(paths))
    except xeenlib.BuildError as error:
        xeenlib.fail(str(error))


if __name__ == '__main__':
    main()
