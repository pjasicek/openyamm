"""
MM9 object classes every converted map shares, written by the shared converter (FINAL_REBUILD_WORK.md phase 3):

- **BonePile** (search loot, C2): the class's decorations click into `evt.SearchLootProp` with the scene's
  `searchable_loot_props` (the shared MM9 item sources, mm9_item_sources.py: TreasureLevel, DiseaseChance, kept after
  the search; game/gameplay/SearchableLootPropRuntime.cpp, kind `bone_pile`).
- **DestructableProp SpawnObject TreasureBag** (C6): a breaking urn drops its bag (`evt.SpawnLootContainer`, the
  scene's `spawned_loot_containers`).
- **Exploding destructibles** (C6, MM9's DestructableBrush/DestructableProp `Exploding 1`): breaking deals
  ExplodeDamage within DamageRadius to the party and to the other exploding destructibles there (a chain).
- **Death/DamageTrigger "off" to a PerceptionBrush** (C3): breaking (or damaging) a destructible turns off the hint
  that marks it (Thjorgard's and Sturmford's boards and chains).
- **Fire** (C4, MM9's particle fire, `On 1, Fire 1`, not switched by anything): the flames (the gate fire's cards at
  FireScale / 12, unless a burning prop under it already has them) and the flicker light (LightMaxRadius, LightColor1)
  where no MM9 Light stands within that radius. Every fire's sound, and the torches' and braziers', is
  ambient.fire_sounds'.
- **Trigger -> AmbientSound** (C10): a plain touch Trigger (PlayerTriggerable, TriggerTouch, StartOn 1) sends On, Off
  or Toggle to an AmbientSound (or a fire, for its sound): the scene sound is switched by the map variable
  `AmbientSound<key>` (1 on, 2 off; game/audio/WorldAmbientSounds.h).

Each map's own wiring wins: an object the map's hooks already placed or scripted is left to them. The map Lua comes
from lua.Script.finish (`shared_lines`); events: OBJECT_EVENT_BASE + DAT index (MM9's object Use event, as
generate_mm9_events.py), AMBIENT_POLL_EVENT.
"""

from __future__ import annotations

import re
from functools import lru_cache

import numpy as np

from .source import ROOT, SCALE

OBJECT_EVENT_BASE = 30000           # an object's own event: 30000 + its DAT index (generate_mm9_events.py)
DAMAGED_EVENT_BASE = 34000          # a destructible's shared damaged event: 34000 + its DAT index
SHARED_LOAD_EVENT = 902             # the shared objects' map-load event (hints, the trigger poll)
AMBIENT_POLL_EVENT = 903            # the ambient triggers' 4 Hz poll
PERCEPTION_LIGHT_POLL_EVENT = 904   # the perception lights' 3 s check
WEATHER_POLL_EVENT = 905            # the weather triggers' 4 Hz poll
PARTY_REACH = 37                    # the party's collision radius (IndoorWorldRuntime PartyCollisionRadius)
PARTY_HEIGHT = 170                  # feet to head, native
GATE_FIRE_SCALE = 12.0              # Anskram's ImpGateFire (FireScale 12) is the gate fire's full size (mm9_gatefire)
BURNING_PROP_REACH_LT = 48.0        # a Fire this near a decoration with flame cards burns on it (the log piles)
FIRE_SOUND_INNER = 0.25             # inner radius / SoundRadius (MM9's AmbientSounds: 250 / 1000)
SCRIPTS = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"


def _number(value, default: float = 0.0) -> float:
    """MM9 stores some floats as their bit pattern in an int."""
    import struct
    if value in (None, ""):
        return default
    if isinstance(value, int) and abs(value) > 100000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value)


@lru_cache(maxsize=None)
def _script_text(name: str) -> str:
    """An MM9 script's text, lower case ('' when it is not shipped)."""
    base = name.replace("\\", "/").rsplit("/", 1)[-1].lower()
    for path in SCRIPTS.glob("*"):
        if path.name.lower() == base:
            return path.read_text(encoding="latin-1").lower()
    return ""


def scripted_names(source) -> set:
    """Lower-case names another object names: in a property (a link or ScriptParams token) or in the text of a script
    an object of the map runs (`GetObjectHandle FallingTorchFire0`)."""
    names = set()
    texts = set()
    for o in source.objects:
        for key, value in o["properties"].items():
            if key == "Name" or not isinstance(value, str) or not value:
                continue
            names |= {token.lower() for token in re.split(r"[\s,;]+", value) if token}
            if key == "ScriptName":
                texts.add(value)
    words = set()
    for name in texts:
        words |= set(re.findall(r"[a-z0-9_]+", _script_text(name)))
    return names | words


# --- Bone piles and urn bags -------------------------------------------------------------------------------------------
def searchable_records(content) -> list[dict]:
    """The scene's `searchable_loot_props`: the placed BonePile decorations' records (content.searchable)."""
    out = []
    for record in content.item_source_data.get("searchable_loot_props", []):
        if record["source_object_index"] in content.searchable:
            out.append(_framed(content.project, record))
    return out


def spawned_records(build, indices: set) -> list[dict]:
    """The scene's `spawned_loot_containers` of the given destructibles (a breaking urn's TreasureBag)."""
    return [_framed(build.project, record) for record in build.content.item_source_data.get("spawned_loot_containers", [])
            if record["source_object_index"] in indices]


def _framed(project, record: dict) -> dict:
    record = dict(record)
    record.pop("world_visual", None)
    if any(project.offset):
        position = project.native(record["source_position_lt"]).round().astype(int)
        record["position"] = {k: int(v) for k, v in zip(("x", "y", "z"), position)}
    return record


def spawn_sources(build) -> dict:
    """DAT index -> source id of every object whose SpawnObject is a TreasureBag."""
    return {record["source_object_index"]: record["source_id"]
            for record in build.content.item_source_data.get("spawned_loot_containers", [])
            if record.get("kind") == "treasure_bag"}


def exploding(properties: dict) -> bool:
    return bool(_number(properties.get("Exploding"))) and _number(properties.get("ExplodeDamage")) > 0


# --- Fires -------------------------------------------------------------------------------------------------------------
def fire_decoration(properties: dict) -> str:
    """The gate fire's row at the Fire's size (FireScale / 12 of Anskram's gate fire, as Bathhouse's x8 and x33)."""
    percent = int(round(_number(properties.get("FireScale"), 1.0) / GATE_FIRE_SCALE * 100))
    return "mm9_gatefire_unlit" if percent == 100 else f"mm9_gatefire_x{percent}"


def always_on_fires(source) -> list[dict]:
    """MM9's Fire objects that burn from the start with flames and that nothing switches or scripts."""
    scripted = scripted_names(source)
    return [o for o in source.objects if o["class"] == "Fire" and _number(o["properties"].get("On"))
            and _number(o["properties"].get("Fire")) and o["name"].lower() not in scripted]


def place_fires(build) -> None:
    """C4: the always-on fires' flames and lights (module docstring). Fires the map placed are left to it."""
    content, project = build.content, build.project
    placed = {entry["anchor"].lower() for entry in content.report["decorations"]}
    lights = [np.asarray(o["properties"]["Pos"], float) for o in build.source.objects if o["class"] == "Light"
              and isinstance(o["properties"].get("Pos"), list)]
    report = content.report.setdefault("fires", [])
    for o in always_on_fires(build.source):
        if o["name"].lower() in placed:
            continue
        p = o["properties"]
        pos = np.asarray(p["Pos"], float)
        native = project.native(pos)
        entry = {"fire": o["name"], "position": [int(round(v)) for v in native]}
        burning = content.burning_decoration_near(native, BURNING_PROP_REACH_LT * SCALE)
        if burning:
            entry["burns_on"] = burning
        else:
            decoration = fire_decoration(p)
            if decoration in content.ids:
                content.entity(f"fire_{o['name']}", decoration, native, 0)
                entry["flames"] = decoration
            else:
                print(f"WARNING: fire {o['name']}: no decoration row {decoration} (props/mm9_outdoor_regions_claude/"
                      "scripts/converter_rows.py)")
                entry["flames_missing"] = decoration
        radius = _number(p.get("LightMaxRadius"))
        if radius > 0 and not any(np.linalg.norm(light - pos) < radius for light in lights):
            colour = [int(round(min(max(_number(v), 0), 255))) for v in (p.get("LightColor1") or [255, 190, 130])]
            content.point_light(f"LIGHT_fire_{o['name']}", native + [0, 0, 16], radius * SCALE, colour)
            entry["light_radius"] = round(radius * SCALE)
        report.append(entry)


# --- Ambient sound triggers --------------------------------------------------------------------------------------------
def _links(properties: dict):
    """(target name, message) of a Trigger's TargetName<k> / MessageName<k> pairs."""
    for key, value in properties.items():
        if key.startswith("TargetName") and isinstance(value, str) and value:
            yield value, str(properties.get("MessageName" + key[len("TargetName"):]) or "").strip().lower()


def ambient_triggers(build, sounds: list[dict]) -> list[dict]:
    """C10: plain touch Triggers that switch the scene's ambient sounds: [{name, box (native low, high), uses,
    switches: [(key, 'on' | 'off' | 'toggle', start_on)]}]. A Trigger that lights or puts out a fire switches its sound
    (ambient.fire_sounds) the same way."""
    from .ambient import FIRE_CLASSES
    by_name = {o["name"].lower(): o for o in build.source.objects
               if o["class"] == "AmbientSound" or o["class"] in FIRE_CLASSES}
    built = {s["key"]: s for s in sounds}
    out = []
    for o in build.source.objects:
        p = o["properties"]
        if o["class"] != "Trigger" or not _number(p.get("PlayerTriggerable")) or not _number(p.get("TriggerTouch"), 1):
            continue
        if not _number(p.get("StartOn"), 1) or "Pos" not in p or "Dims" not in p:
            continue
        switches = []
        for target, message in _links(p):
            sound = by_name.get(target.lower())
            if sound is None or sound["index"] not in built or message not in ("on", "off", "toggle"):
                continue
            switches.append((sound["index"], message, built[sound["index"]].get("start_on", True)))
        if not switches:
            continue
        pos, dims = np.asarray(p["Pos"], float), np.asarray(p["Dims"], float)
        corners = build.project.native(np.array([pos - dims, pos + dims]))
        low, high = corners.min(0), corners.max(0)
        low = [low[0] - PARTY_REACH, low[1] - PARTY_REACH, low[2] - PARTY_HEIGHT]
        high = [high[0] + PARTY_REACH, high[1] + PARTY_REACH, high[2]]
        out.append({"name": o["name"], "index": o["index"], "low": [int(round(v)) for v in low],
                    "high": [int(round(v)) for v in high], "uses": int(_number(p.get("ActivationCount"))),
                    "switches": switches})
    return out


# --- Perception lights -----------------------------------------------------------------------------------------------
def perception_light_lua(build, name: str, on: bool) -> str:
    """The Lua of MM9's On or Off message to a PerceptionLight (by DAT name), for a map's own handlers: Off puts it out
    at once and for good, On lets the shared check show it again to a perceptive party (dungeon/lights.py)."""
    from .lights import PULSING_LIGHT_KEY_BASE
    key = PULSING_LIGHT_KEY_BASE + build.source.by_name[name.lower()]["index"]
    if on:
        return f"set(\"LightOff{key}\", 0); set(\"Light{key}\", 0); handlers[{PERCEPTION_LIGHT_POLL_EVENT}]()"
    return f"set(\"LightOff{key}\", 1); set(\"Light{key}\", 1); evt.SetLight({key}, false)"


# --- Bonus props -----------------------------------------------------------------------------------------------------
BONUS_HINTS = {"WellMMIX": ("Well", "Drink"), "Cauldron": ("Cauldron", "Drink"), "Cookpot": ("Cook pot", "Eat"),
               "Clover": ("Clover", "Pick")}


def bonus_call(build, name: str) -> str:
    """The Lua that uses an MM9 bonus prop by its DAT name (for a map that keeps the prop's own click event): its
    class's use (object.lto, devdocs/mm9_rework/MM9_BONUS_PROPS_RE.md) through the world's MM9.useWell / useCauldron /
    useCookpot / useClover (worlds/mm9/events/common/mm9_common.lua), with the DAT values."""
    o = build.source.by_name[name.lower()]
    index, p = o["index"], o["properties"]
    number = lambda key: int(round(_number(p.get(key))))
    if o["class"] == "WellMMIX":
        return (f"MM9.useWell({index}, {number('Stat')}, {number('StatType')}, {number('BonusAmt')}, "
                f"{number('BonusSeconds')}, {number('DosesPerDay')})")
    if o["class"] == "Cauldron":
        return f"MM9.useCauldron({index}, {number('Resistance')}, {number('BonusAmt')})"
    if o["class"] == "Cookpot":
        return (f"MM9.useCookpot({index}, {number('PoisonChance')}, {number('Resistance')}, {number('BonusAmt')}, "
                f"{number('DosesPerDay')})")
    if o["class"] == "Clover":
        return f"MM9.useClover({index}, \"{build.project.stem}:{o['name']}\")"
    raise SystemExit(f"{name}: class {o['class']} is not an MM9 bonus prop")


def bonus_lines(build) -> tuple[list[str], list[tuple]]:
    """MM9's wells, cauldrons, cook pots and clovers (content.bonus_props: the placed props the map gave no event of
    its own): a click runs bonus_call."""
    props = getattr(build.content, "bonus_props", {})
    lines, registrations = [], []
    for index, name in sorted(props.items()):
        o = build.source.objects[index]
        call = bonus_call(build, o["name"])
        event = OBJECT_EVENT_BASE + index
        lines.append(f"handlers[{event}] = function() {call} end   -- {name} ({o['class']})")
        title, hint = BONUS_HINTS[o["class"]]
        registrations.append((event, title, hint, "event"))
    if lines:
        lines = ["-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,",
                 "-- cook pots and clovers.", *lines, ""]
    return lines, registrations


# --- Greeting voices -------------------------------------------------------------------------------------------------
def voice_lines(build, taken: set, written: str = "") -> tuple[list[str], list[tuple]]:
    """MM9's greeting voices (voices.py): each placed actor (the scene's, build.scene_actors) with a voice on use (its
    GreetingSound or its script's :OnUse) gets its click event (53000 + its DAT index): the voice, then its RUDE
    dialogue as a click would open it. A click the map's own Lua takes keeps its handler with the voice played first,
    unless that Lua (`written`) plays the voice itself."""
    from .voices import USE_EVENT_BASE, use_voices
    actors = getattr(build, "scene_actors", None) or []
    voices = use_voices(build.source)
    lines, registrations, done = [], [], set()
    for actor in actors:
        index = actor.get("mm9_source_object_index")
        voice = voices.get(index)
        event = USE_EVENT_BASE + index if index else None
        if not voice or not voice.startswith("voices/") or event in done or index >= 3000:
            continue
        done.add(event)
        if event in taken:
            if voice not in written.lower():
                lines.append(f"do local own = handlers[{event}]; handlers[{event}] = function() "
                             f"MM9.playSound(\"{voice}\"); own() end end   -- {build.source.objects[index]['name']}")
            continue
        rude = int(actor.get("mm9_rude_id") or 0)
        calls = f"MM9.playSound(\"{voice}\")" + (f"; MM9.openRude({rude})" if rude > 0 else "")
        lines.append(f"handlers[{event}] = function() {calls} end   -- {build.source.objects[index]['name']}")
        registrations.append((event, actor.get("name") or "Voice", None, "event"))
    if lines:
        lines = ["-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the",
                 "-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).",
                 *lines, ""]
    return lines, registrations


# --- Weather triggers ------------------------------------------------------------------------------------------------
def fog_state_lua(source, fog: dict, seconds: str) -> str:
    """evt.SetFog for an MM9 Fog state (its colour, FogNearZ/FarZ x 2.56, the sky in fog when its SkyFogNearZ is
    inside the sky box: Source.sky_fogged), or evt.ClearFog for one that shows none (FogEnable 0, or its fog begins
    past FarZ, MM9's far clip: Frosgard's Fog1)."""
    p = fog["properties"]
    near, far, clip = (_number(p.get(k)) for k in ("FogNearZ", "FogFarZ", "FarZ"))
    if not _number(p.get("FogEnable")) or (clip > 0 and near >= clip):
        return f"evt.ClearFog({seconds})"
    colour = ", ".join(str(int(round(min(max(_number(c), 0), 255)))) for c in p["FogColor"])
    sky = 1 if source.sky_fogged(p) else 0
    return f"evt.SetFog({colour}, {near * SCALE:.0f}, {far * SCALE:.0f}, {seconds}, {sky})"


def trigger_box(build, o: dict) -> tuple[list[int], list[int]]:
    """A Trigger's box (Pos +- Dims) in native units, grown by the party's radius and reaching down by its height (MM9
    fires on any part of the party in the box): (low, high) to test the party's feet against."""
    p = o["properties"]
    pos, dims = np.asarray(p["Pos"], float), np.asarray(p["Dims"], float)
    corners = build.project.native(np.array([pos - dims, pos + dims]))
    low, high = corners.min(0), corners.max(0)
    return ([int(round(v)) for v in (low[0] - PARTY_REACH, low[1] - PARTY_REACH, low[2] - PARTY_HEIGHT)],
            [int(round(v)) for v in (high[0] + PARTY_REACH, high[1] + PARTY_REACH, high[2])])


def weather_triggers(build) -> list[dict]:
    """MM9's WeatherMan switched by touch Triggers (Frosgard's pass, Trigger1-4: thick Fog0 on the way in, the clear
    Fog1 on the way out): each Trigger (PlayerTriggerable, StartOn) that sends On or Off to a WeatherMan. Its On
    fades to the WeatherMan's FogOn state, Off to its FogOff state, each over that state's TransitionTime
    (devdocs/INDOOR_FOG.md "Fog from Lua"). [{name, index, low, high, switches: [(weatherman index, on)]}]."""
    weathermen = {o["name"].lower(): o for o in build.source.objects if o["class"] == "WeatherMan"}
    out = []
    for o in build.source.objects:
        p = o["properties"]
        if o["class"] != "Trigger" or not _number(p.get("PlayerTriggerable")) or not _number(p.get("StartOn"), 1):
            continue
        if "Pos" not in p or "Dims" not in p:
            continue
        switches = [(weathermen[target.lower()]["index"], message == "on") for target, message in _links(p)
                    if target.lower() in weathermen and message in ("on", "off")]
        if not switches:
            continue
        low, high = trigger_box(build, o)
        out.append({"name": o["name"], "index": o["index"], "low": low, "high": high, "switches": switches})
    return out


def weather_lines(build, triggers: list[dict]) -> list[str]:
    """The weather triggers' Lua: a 4 Hz poll of the party in each box (entering fires it); the WeatherMan's state in
    the map variable Weather<index> (1 on, 2 off), set again on load (the scripted fog is not saved)."""
    source = build.source
    states = {}
    for t in triggers:
        for index, _ in t["switches"]:
            p = source.objects[index]["properties"]
            calls = []
            for key in ("FogOff", "FogOn"):
                fog = source.by_name.get(str(p.get(key) or "").lower())
                if fog is None or fog["class"] != "Fog":
                    calls.append("evt.ClearFog(fade and 1 or 0)")
                    continue
                seconds = _number(fog["properties"].get("TransitionTime"))
                calls.append(fog_state_lua(source, fog, f"fade and {seconds:g} or 0"))
            states[index] = calls
    rows = [f"    {{name = \"{t['name']}\", box = {{{_point(t['low'])}, {_point(t['high'])}}}, "
            f"switches = {{{', '.join(f'{{{i}, {str(on).lower()}}}' for i, on in t['switches'])}}}}},"
            for t in triggers]
    weather = [f"    [{index}] = {{off = function(fade) {off} end, on = function(fade) {on} end}},"
               for index, (off, on) in sorted(states.items())]
    return [
        "-- MM9's WeatherMan switched by touch Triggers (dungeon/objects.py weather_triggers): entering a box sends its",
        "-- On / Off; On fades to the WeatherMan's FogOn state, Off to its FogOff state (evt.SetFog / evt.ClearFog, over the",
        "-- state's TransitionTime). Map variable Weather<index>: 1 on, 2 off; set again on load without the fade.",
        "local WEATHER = {", *weather, "}",
        "local WEATHER_TRIGGERS = {", *rows, "}",
        "local weatherInside = {}",
        f"handlers[{WEATHER_POLL_EVENT}] = function()",
        "    local x, y, z = evt.GetPartyPosition()",
        "    for _, t in ipairs(WEATHER_TRIGGERS) do",
        "        local b = t.box",
        "        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]",
        "        if now and not weatherInside[t.name] then",
        "            for _, s in ipairs(t.switches) do",
        "                set(\"Weather\" .. s[1], s[2] and 1 or 2)",
        "                if s[2] then WEATHER[s[1]].on(true) else WEATHER[s[1]].off(true) end",
        "            end",
        "        end",
        "        weatherInside[t.name] = now",
        "    end",
        f"    evt.StartTimer({WEATHER_POLL_EVENT}, seconds(0.25))",
        "end",
    ]


# --- Lua -------------------------------------------------------------------------------------------------------------
def _point(p) -> str:
    return "{" + ", ".join(str(int(round(v))) for v in p) + "}"


def shared_lines(build, taken: set = frozenset(), written: str = "") -> tuple[list[str], list[tuple], list[int]]:
    """The shared objects' Lua (lines, registrations (event, title, hint, kind), map-load events). `taken`: the events
    the map's own Lua already has, `written` its text (a greeting voice goes first in such a click unless it plays
    the voice itself)."""
    lines, registrations, load = [], [], []
    voice, voice_registrations = voice_lines(build, taken, written)
    lines += voice
    registrations += voice_registrations
    shared = getattr(build, "shared", {})
    piles = shared.get("bone_piles", {})
    if piles:
        lines.append("-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its")
        lines.append("-- TreasureLevel loot once, DiseaseChance; the pile stays).")
        for index, (source_id, hint, name) in sorted(piles.items()):
            event = OBJECT_EVENT_BASE + index
            lines.append(f"handlers[{event}] = function() evt.SearchLootProp(\"{source_id}\") end   -- {name}")
            registrations.append((event, hint, hint, "event"))
        lines.append("")
    bonus, bonus_registrations = bonus_lines(build)
    lines += bonus
    registrations += bonus_registrations
    broken = shared.get("broken", {})
    if broken:
        blasts = {index: b["explode"] for index, b in broken.items() if b.get("explode")}
        if blasts:
            rows = ", ".join(f"[{i}] = {{{_point(e['centre'])}, {e['radius']}, {e['damage']}}}"
                             for i, e in sorted(blasts.items()))
            lines += [
                "-- MM9's exploding destructibles (Exploding 1): breaking deals ExplodeDamage within DamageRadius of its",
                "-- centre to the party and to the other exploding destructibles there (the next of a chain breaks then).",
                f"local EXPLODING = {{{rows}}}",
                "local function explode(id)",
                "    local e = EXPLODING[id]",
                "    local c, r = e[1], e[2]",
                "    evt.SpawnWorldEffect(\"mm9:column_of_fire\", c[1], c[2], c[3], 0.6)",
                "    local x, y, z = evt.GetPartyPosition()",
                "    local dz = math.max(0, c[3] - (z + 170), z - c[3])",
                "    if (x - c[1]) ^ 2 + (y - c[2]) ^ 2 + dz ^ 2 <= r * r then",
                "        evt.DamagePlayer(Players.All, const.Damage.Fire, e[3])",
                "    end",
                "    for other, o in pairs(EXPLODING) do",
                "        local q = o[1]",
                "        if other ~= id and (q[1] - c[1]) ^ 2 + (q[2] - c[2]) ^ 2 + (q[3] - c[3]) ^ 2 <= r * r then",
                "            evt.DamageDestructible(other, e[3])",
                "        end",
                "    end",
                "end",
            ]
        lines.append("-- MM9's breaking destructibles: an urn's SpawnObject TreasureBag drops (evt.SpawnLootContainer).")
        for index, b in sorted(broken.items()):
            calls = []
            if b.get("spawn"):
                calls.append(f"evt.SpawnLootContainer(\"{b['spawn']}\")")
            if b.get("explode"):
                calls.append(f"explode({index})")
            for cog in b.get("hints_off", []):
                calls.append(f"set(\"HintOff{cog}\", 1); evt.SetFacetBit({cog}, FacetBits.Invisible, true)")
            for key in b.get("lights_off", []):
                calls.append(f"set(\"LightOff{key}\", 1); set(\"Light{key}\", 1); evt.SetLight({key}, false)")
            event = OBJECT_EVENT_BASE + index
            lines.append(f"handlers[{event}] = function() {'; '.join(calls)} end   -- {b['name']}")
            registrations.append((event, b["name"], None, "event"))
        lines.append("")
    clicks = shared.get("break_clicks", {})
    if clicks:
        from .destructibles import CLICK_DAMAGE, CLICK_EVENT_BASE, material
        hints = {"stone": "Rocks", "wood": "Boards", "glass": "Glass", "metal": "Metal"}
        lines.append("-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break")
        lines.append("-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).")
        for index, name in sorted(clicks.items()):
            event = CLICK_EVENT_BASE + index
            lines.append(f"handlers[{event}] = function() evt.DamageDestructible({index}, {CLICK_DAMAGE}) end   -- {name}")
            # the hover hint: what it breaks into (its debris material)
            hint = hints[material(build.source.objects[index]["properties"], prop=False)]
            registrations.append((event, name, hint, "event"))
        lines.append("")
    damaged = shared.get("damaged", {})
    for index, d in sorted(damaged.items()):
        calls = [f"set(\"HintOff{cog}\", 1); evt.SetFacetBit({cog}, FacetBits.Invisible, true)"
                 for cog in d["hints_off"]]
        calls += [f"set(\"LightOff{key}\", 1); set(\"Light{key}\", 1); evt.SetLight({key}, false)"
                  for key in d.get("lights_off", [])]
        event = DAMAGED_EVENT_BASE + index
        lines.append(f"handlers[{event}] = function() {'; '.join(calls)} end   -- {d['name']} damaged: its hint off")
        registrations.append((event, d["name"], None, "event"))
    if damaged:
        lines.append("")
    hints = shared.get("hints", {})
    if hints:
        from .perception import HINT_POLL_EVENT, PERCEPTION_SKILL
        rows = ", ".join(f"[{cog}] = {value}" for cog, value in sorted(hints.items()))
        lines += [
            "-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the",
            "-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with",
            "-- set(\"HintOff<cog>\", 1) (MM9's Off message to the brush).",
            f"local HINTS = {{{rows}}}",
            f"handlers[{HINT_POLL_EVENT}] = function()",
            "    for cog, value in pairs(HINTS) do",
            f"        local want = (var(\"HintOff\" .. cog) == 0 and evt.CheckSkill({PERCEPTION_SKILL}, 0, value)) and 2 or 1",
            "        if var(\"Hint\" .. cog) ~= want then",
            "            set(\"Hint\" .. cog, want)",
            "            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)",
            "        end",
            "    end",
            "end",
        ]
        registrations.append((HINT_POLL_EVENT, "Perception hints", None, "timer"))
    lights = shared.get("perception_lights", {})
    if lights:
        from .perception import PERCEPTION_SKILL
        rows = ", ".join(f"[{key}] = {value}" for key, value in sorted(lights.items()))
        lines += [
            "-- MM9's PerceptionLights (dungeon/lights.py perception_lights): the red hint lights shine for a party whose",
            "-- Perception reaches their PerceptionValue (scene pulsing lights, evt.SetLight), checked on load and every",
            "-- 3 s. MM9's Off message: set(\"LightOff<key>\", 1) and evt.SetLight(key, false); On: set(\"LightOff<key>\", 0).",
            f"local PERCEPTION_LIGHTS = {{{rows}}}",
            f"handlers[{PERCEPTION_LIGHT_POLL_EVENT}] = function()",
            "    for key, value in pairs(PERCEPTION_LIGHTS) do",
            f"        local want = (var(\"LightOff\" .. key) == 0 and evt.CheckSkill({PERCEPTION_SKILL}, 0, value)) and 2 or 1",
            "        if var(\"Light\" .. key) ~= want then",
            "            set(\"Light\" .. key, want)",
            "            evt.SetLight(key, want == 2)",
            "        end",
            "    end",
            "end",
        ]
        registrations.append((PERCEPTION_LIGHT_POLL_EVENT, "Perception lights", None, "timer"))
    weather = shared.get("weather_triggers", [])
    if weather:
        lines += weather_lines(build, weather)
        registrations.append((WEATHER_POLL_EVENT, "Weather triggers", None, "timer"))
    triggers = shared.get("ambient_triggers", [])
    if triggers:
        rows = []
        for t in triggers:
            switches = ", ".join(f"{{{key}, \"{message}\", {'true' if on else 'false'}}}" for key, message, on in t["switches"])
            rows.append(f"    {{name = \"{t['name']}\", box = {{{_point(t['low'])}, {_point(t['high'])}}}, uses = {t['uses']}, "
                        f"switches = {{{switches}}}}},")
        lines += [
            "-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle",
            "-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.",
            "local SOUND_TRIGGERS = {", *rows, "}",
            "local soundInside = {}",
            f"handlers[{AMBIENT_POLL_EVENT}] = function()",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, t in ipairs(SOUND_TRIGGERS) do",
            "        local b = t.box",
            "        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]",
            "        if now and not soundInside[t.name] and (t.uses == 0 or var(\"SoundUses\" .. t.name) < t.uses) then",
            "            set(\"SoundUses\" .. t.name, var(\"SoundUses\" .. t.name) + 1)",
            "            for _, s in ipairs(t.switches) do",
            "                local name = \"AmbientSound\" .. s[1]",
            "                local on = var(name) == 1 or (var(name) == 0 and s[3])",
            "                local want = (s[2] == \"on\" or (s[2] == \"toggle\" and not on)) and 1 or 2",
            "                set(name, want)",
            "            end",
            "        end",
            "        soundInside[t.name] = now",
            "    end",
            f"    evt.StartTimer({AMBIENT_POLL_EVENT}, seconds(0.25))",
            "end",
        ]
        registrations.append((AMBIENT_POLL_EVENT, "Ambient triggers", None, "timer"))
    if hints or triggers or lights or weather:
        from .perception import HINT_POLL_EVENT
        body = []
        if hints:
            body += ["    for cog, _ in pairs(HINTS) do set(\"Hint\" .. cog, 0) end",
                     f"    handlers[{HINT_POLL_EVENT}]()"]
        if lights:
            body += ["    for key, _ in pairs(PERCEPTION_LIGHTS) do set(\"Light\" .. key, 0) end",
                     f"    handlers[{PERCEPTION_LIGHT_POLL_EVENT}]()"]
        if triggers:
            body.append(f"    handlers[{AMBIENT_POLL_EVENT}]()")
        if weather:
            body += ["    for k, w in pairs(WEATHER) do",
                     "        local f = w.on",
                     "        if var(\"Weather\" .. k) == 2 then f = w.off elseif var(\"Weather\" .. k) ~= 1 then f = nil end",
                     "        if f ~= nil then f(false) end",
                     "    end",
                     "    for _, t in ipairs(WEATHER_TRIGGERS) do weatherInside[t.name] = false end",
                     f"    handlers[{WEATHER_POLL_EVENT}]()"]
        lines += [f"handlers[{SHARED_LOAD_EVENT}] = function()   -- map load: the shared objects", *body, "end"]
        registrations.append((SHARED_LOAD_EVENT, "Shared objects", None, "event"))
        load.append(SHARED_LOAD_EVENT)
    if lines:
        lines.append("")
    return lines, registrations, load
