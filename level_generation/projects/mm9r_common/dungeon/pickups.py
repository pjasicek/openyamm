"""MM9's pickable props as the scene's world items (devdocs/mm9_rework/PLACED_ITEMS_PLAN.md).

MM9 placed its pickable items as Props whose script gives the item and removes the prop: givetake.scr, bootgive.scr,
skillbook.scr, orb.scr and one script per quest item. Content.props places these as `world_items` instead of
decorations: real ground items (the item's 3D model, its sparkle, right-click inspect), picked up as any. Their gates
are the keys the script's Init hides or removes the object on (raw MM9 key + 90000, world.yml `qbits.mapping`).

The side effects of the pickup (keys, experience, sounds, triggers) stay in the map script: a map that passes the
prop a click event (content.props `events`) gets that event as the item's `pickup_event`, run after the pickup.
A pickup without a map event sets its rule's `set_keys` itself (the shared rules' only side effect).

Interactions (the slag extractor, the great book, the book key, the Capstone, the fake book, Thjorad) and set
dressing are not here: they stay props.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
ITEM_IDS = ROOT / "assets_dev/worlds/mm9/state/item_ids.yml"
QBIT_BASE = 90000

# SkillBook.scr's SkillInit: the skill name of P0 (its own spellings) -> its book (285-306); no name or "Random": any.
SKILL_BOOKS = {"blade": 285, "bow": 286, "cudgel": 287, "spear": 288, "armsmaster": 289, "unarmed": 290,
               "armor": 291, "shield": 292, "dodge": 293, "elemental": 294, "light": 295, "dark": 296, "sprit": 297,
               "disarm": 298, "merchant": 299, "perception": 300, "repair": 301, "id_item": 302, "id_monster": 303,
               "body": 304, "learning": 305, "meditation": 306}
ANY_SKILL_BOOK = list(range(285, 307))

# Items MM9's scripts give that its item table lacks (givetake.scr "386 1": Wizard's Lab's skeleton).
MISSING_ITEMS = {386}


@dataclass
class Pickup:
    item: int | None                                  # raw MM9 item, or None with a pool
    pool: list[int] = field(default_factory=list)     # raw MM9 items, one drawn per session
    required_keys: list[int] = field(default_factory=list)
    forbidden_keys: list[int] = field(default_factory=list)
    pickup_keys: list[int] = field(default_factory=list)      # shown, but taken only with these (no sparkle before)
    set_keys: list[int] = field(default_factory=list)


# One quest pickup per script: item, the keys that show it (Init hides it without them) and hide it (Init removes it
# with them), and the key its OnUse gives when no map event takes over. The scripts' other branches (an early find
# versus the quest's find: Crona Kiga, Ludwig's Manuscript, the Book of Rules, the Relic, the Golden Honk) are the map
# events'.
QUEST_PICKUPS = {
    "herbs": Pickup(372, required_keys=[128], forbidden_keys=[131], set_keys=[131]),
    "plow": Pickup(371, required_keys=[128], forbidden_keys=[130], set_keys=[130]),
    "dolly": Pickup(370, required_keys=[128], forbidden_keys=[132], set_keys=[132]),
    # KiraShield.scr: the shield always lies there, but a click takes it only with key 214 (the quest)
    "kirashield": Pickup(375, forbidden_keys=[216], pickup_keys=[214], set_keys=[216]),
    "relic": Pickup(368, forbidden_keys=[340]),
    "treeoflife": Pickup(241, forbidden_keys=[256], set_keys=[256]),
    "writ": Pickup(392, required_keys=[99], forbidden_keys=[100], set_keys=[100]),
    "cronakiga": Pickup(390, forbidden_keys=[48, 169]),
    "lichinstructions": Pickup(447, forbidden_keys=[296], set_keys=[296]),
    "ludwigsmanuscript": Pickup(248, forbidden_keys=[16, 110]),
    "bookofrules": Pickup(391, forbidden_keys=[59, 166]),
    "honk": Pickup(369, forbidden_keys=[344, 345]),
    "honkkey": Pickup(445, forbidden_keys=[7000], set_keys=[7000]),
    "yanmirkey": Pickup(570, forbidden_keys=[7001], set_keys=[7001]),
    "blackheart": Pickup(29, forbidden_keys=[223], set_keys=[223]),
}


# Props MM9 left as set dressing that OpenYAMM makes pickups: (map stem, DAT name) -> rule. Markel's six awards in his
# hall (Guberland City, Sign4 "Awards Won by Markel ... at The Gathering") are the Thing's Stuffed Dragon: shown as
# before, taken once Markel is dead (key 40, the council): a way past the Thing's games on Yrsa's errand (the map
# event gives key 94).
NAMED_PICKUPS = {("guberlandcity", f"Prize{n}"): Pickup(395, pickup_keys=[40]) for n in range(6)}

# Pickups MM9 places hidden (Visible 0) for a script to show later: (map stem, DAT name) -> the keys that show them.
# The Afterworld's heroes' swords appear with Absolution (key 492; SixFires.inc); Sven's lies there from the start.
REVEALED_BY = {("afterworld", name): [492] for name in ("BjarniSword", "SigmundSword", "TryygvaSword", "KiraSword")}


def script_name(properties: dict) -> str:
    """givetake for 'scripts\\Givetake.scr'."""
    name = str(properties.get("ScriptName", "")).replace("/", "\\").split("\\")[-1].lower()
    return name[:-4] if name.endswith(".scr") else name


def rule(properties: dict, stem: str = "") -> Pickup | None:
    """The pickup a DAT object's script (or NAMED_PICKUPS, by map stem and name) makes it, or None (not a pickup)."""
    named = NAMED_PICKUPS.get((stem, str(properties.get("Name", ""))))
    if named is not None:
        return named
    script = script_name(properties)
    params = str(properties.get("ScriptParams", "")).split()
    if script in ("givetake", "bootgive"):
        item = int(params[0]) if params and params[0].isdigit() else 0
        return Pickup(item) if item and item not in MISSING_ITEMS else None
    if script == "skillbook":
        name = params[0].lower() if params else ""
        return Pickup(SKILL_BOOKS[name]) if name in SKILL_BOOKS else Pickup(None, pool=ANY_SKILL_BOOK)
    if script == "orb":
        return Pickup(252, forbidden_keys=[337])     # Orb.scr: giveitem 252; Init removes the orbs with key 337
    return QUEST_PICKUPS.get(script)


def engine_items() -> dict[int, int]:
    """Raw MM9 item -> engine item (worlds/mm9/state/item_ids.yml, as MM9.ItemIds)."""
    if not hasattr(engine_items, "table"):
        data = yaml.load(ITEM_IDS.read_text(), Loader=yaml.CSafeLoader)
        engine_items.table = {int(m["raw_mm9_id"]): int(m["item_id"]) for m in data["mappings"]}
    return engine_items.table


def engine_item(raw: int) -> int:
    table = engine_items()
    if raw not in table:
        raise SystemExit(f"MM9 item {raw} has no engine item (worlds/mm9/state/item_ids.yml)")
    return table[raw]


def scene_entry(stem: str, source_object: int, name: str, dat_name: str, position, pickup: Pickup,
                event: int, placement: dict | None = None) -> dict:
    """The scene's `world_items` entry (game/maps/MapItemSourceYml.cpp). name: the props.json name (a region's
    `obj_<DAT name>`); dat_name: the DAT object's own Name (REVEALED_BY). placement: the map's overrides.yml
    `pickups: {<DAT name>: {pose: [yaw, pitch, roll], offset: [x, y, z]}}`, degrees and native units: an item MM9
    stood or leaned (Kira's Shield on its wall) drawn so, its lowest point on the prop's position plus the offset,
    instead of lying flat."""
    required = pickup.required_keys + REVEALED_BY.get((stem, dat_name), [])
    placement = placement or {}
    offset = placement.get("offset", [0, 0, 0])
    position = [float(v) + float(d) for v, d in zip(position, offset)]
    entry = {
        "source_id": f"{stem}:{name}",
        "source_object_index": int(source_object),
        "source_name": name,
        "position": {axis: int(round(float(v))) for axis, v in zip("xyz", position)},
        "item_id": engine_item(pickup.item) if pickup.item is not None else 0,
        "random_item_pool": [engine_item(raw) for raw in pickup.pool],
        "required_qbits": [QBIT_BASE + key for key in required],
        "forbidden_qbits": [QBIT_BASE + key for key in pickup.forbidden_keys],
        "pickup_qbits": [QBIT_BASE + key for key in pickup.pickup_keys],
        # a map event sets the keys itself (its branches); without one the rule's keys are the pickup's only effect
        "set_qbits": [] if event else [QBIT_BASE + key for key in pickup.set_keys],
        "pickup_event": int(event),
    }
    if "pose" in placement:
        yaw, pitch, roll = (float(v) for v in placement["pose"])
        entry["pose"] = {"yaw": yaw, "pitch": pitch, "roll": roll}
    return entry
