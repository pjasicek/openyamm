"""Tests of the converter's pack growth (dungeon/density.py) on a synthetic map.

    python3 -m pytest level_generation/projects/mm9r_common/test_density.py

The map: room A (sector 1, floor z 0, x 0-2000, y 0-2000) split by a wall at x 1000 from y 0 to 1500; room B
(sector 2, x 2000-3000) beyond its east wall; a raised dais (z 100) in A; a pool (liquid texture), an exit pad (event
face), a door and a ladder in A's south-west quarter; a closet (sector 3) where no copy fits.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(COMMON))

from dungeon import density  # noqa: E402

WATER = "lqwater"


class Map:
    def __init__(self):
        self.vertices, self.faces = [], []

    def face(self, points, facet_type, sector, attributes=0, texture="floor", event=0):
        start = len(self.vertices)
        self.vertices += [{"x": x, "y": y, "z": z} for x, y, z in points]
        self.faces.append({"index": len(self.faces), "is_portal": False, "attributes": attributes,
                           "vertex_indices": list(range(start, start + len(points))), "facet_type": facet_type,
                           "room_number": sector, "texture_name": texture, "face_param": {"cog_triggered": event}})
        return len(self.faces) - 1

    def floor(self, x0, y0, x1, y1, z, sector, **kw):
        return self.face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], 3, sector, **kw)

    def wall(self, x0, y0, x1, y1, sector, z0=0, z1=512):
        return self.face([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], 1, sector)


def synthetic():
    m = Map()
    m.floor(0, 0, 1000, 2000, 0, 1)
    m.floor(1000, 0, 2000, 2000, 0, 1)
    m.floor(1400, 1400, 1800, 1800, 100, 1)                     # the dais
    m.floor(200, 200, 500, 500, 0.5, 1, texture=WATER)          # the pool, over the floor
    m.floor(600, 200, 700, 300, 3, 1, attributes=0x04000000 | 0x2000, event=7)   # an exit pad
    m.floor(2000, 0, 3000, 2000, 0, 2)
    m.floor(4000, 0, 4100, 100, 0, 3)                            # the closet
    for wall in ((0, 0, 3000, 0), (3000, 0, 3000, 2000), (3000, 2000, 0, 2000), (0, 2000, 0, 0),
                 (2000, 0, 2000, 2000), (1000, 0, 1000, 1500),
                 (4000, 0, 4100, 0), (4100, 0, 4100, 100), (4100, 100, 4000, 100), (4000, 100, 4000, 0)):
        m.wall(*wall, sector=1)
    door = m.face([(100, 900, 0), (300, 900, 0), (300, 900, 300), (100, 900, 300)], 1, 1)
    blv = {"vertices": m.vertices, "faces": m.faces}
    scene = {"initial_state": {"doors": [{"door_id": 1, "face_ids": [door], "direction": [0, 0, 65536],
                                          "move_length": 300}], "face_attribute_overrides": []},
             "ladders": [{"bottom": [900, 1900, 0], "top": [900, 1900, 300], "width": 96, "reach": 48}]}
    return blv, scene


def actor(index, x, y, z=1, sector=1, radius=40, **extra):
    record = {"actor_index": index, "name": "Thrall", "npc_id": 0, "attributes": 0x00080000, "hp": 50,
              "hostility_type": 4, "monster_info_id": 9100, "monster_id": 9100, "radius": radius, "height": 160,
              "move_speed": 200, "position": {"x": x, "y": y, "z": z}, "initial_yaw_units": 512, "immobile": False,
              "sector_id": sector, "group": 3, "ally": 0, "unique_name_index": 0, "draw_scale": 1.0,
              "mm9_ai": {"sight": 1536, "wander": {"stops": [[1, 2, 3], [4, 5, 6]]}}}
    record.update(extra)
    return record


def world():
    blv, scene = synthetic()
    return density.World(blv, scene, {WATER})


def run(actors, packs, lua="", stem="testmap", counted_today=None):
    anchors = {f"M{a['actor_index']}": a["actor_index"] for a in actors}
    return density.grow(stem, actors, anchors, packs, world(), density.lua_actor_indices(lua), counted_today)


def test_copies_stand_next_to_their_member_on_its_floor_in_its_room():
    actors = [actor(0, 800, 1000), actor(1, 2500, 1000, sector=2)]
    copies, report = run(actors, [{"members": ["M0"], "add": 4}, {"members": ["M1"], "add": 3}])
    summary = report["summary"]
    assert (summary["wanted_adds"], summary["placed_adds"], summary["moved_adds"], summary["unplaced_adds"]) == (7, 7, 0, 0)
    w = world()
    for copy in copies:
        member = actors[0] if copy["sector_id"] == 1 else actors[1]
        p, m = copy["position"], member["position"]
        assert 120 <= math.hypot(p["x"] - m["x"], p["y"] - m["y"]) <= 600
        assert p["z"] == 1                                   # the same floor, not the dais
        z, record = w.floor(p["x"], p["y"], p["z"] + 1)
        assert record["sector"] == member["sector_id"]
        # never behind the dividing wall from a member west of it
        if member is actors[0] and p["y"] < 1500:
            assert p["x"] < 1000 - copy["radius"]
        assert w.wall_distance(p["x"], p["y"], 8, 160, 500) >= copy["radius"] + density.MARGIN
    everyone = actors + copies
    for i, a in enumerate(everyone):
        for b in everyone[i + 1:]:
            gap = math.hypot(a["position"]["x"] - b["position"]["x"], a["position"]["y"] - b["position"]["y"])
            assert gap >= a["radius"] + b["radius"] + density.MARGIN


def test_copies_are_appended_with_the_members_record_without_its_identity():
    actors = [actor(0, 800, 1000, mm9_source_object_index=12, dormant=True, mm9_guard=True), actor(1, 2500, 1000,
                                                                                                    sector=2)]
    copies, report = run(actors, [{"members": ["M0"], "add": 2}])
    assert [c["actor_index"] for c in copies] == [2, 3]
    assert [c["anchor"] for c in report["packs"][0]["copies"]] == ["M0_grow1", "M0_grow2"]
    copy = copies[0]
    assert "mm9_source_object_index" not in copy and copy["npc_id"] == 0 and copy["unique_name_index"] == 0
    for key in ("monster_id", "hp", "attributes", "hostility_type", "group", "dormant", "mm9_guard", "draw_scale",
                "radius", "height", "sector_id", "mm9_ai"):
        assert copy[key] == actors[0][key]
    copy["mm9_ai"]["wander"]["stops"].append([0, 0, 0])
    assert len(actors[0]["mm9_ai"]["wander"]["stops"]) == 2      # a deep copy


def test_placement_is_deterministic_and_seeded_by_map_and_anchor():
    actors = [actor(0, 800, 1000)]
    first, _ = run(actors, [{"members": ["M0"], "add": 3}])
    second, _ = run(actors, [{"members": ["M0"], "add": 3}])
    other, _ = run(actors, [{"members": ["M0"], "add": 3}], stem="othermap")
    assert first == second
    assert [c["position"] for c in first] != [c["position"] for c in other]


def test_water_pads_doors_and_ladders_are_kept_clear():
    w = world()
    member = actor(0, 600, 600)
    assert w.spot(member, member, 350, 350, [member]) is None          # the pool
    assert w.spot(member, member, 650, 250, [member]) is None          # the exit pad
    assert w.spot(member, member, 200, 850, [member]) is None          # beside the door (its whole travel)
    assert w.spot(member, member, 860, 1800, [member]) is None         # the ladder
    assert w.spot(member, member, 750, 750, [member]) is not None      # open floor


def test_scripted_members_are_not_copied_and_other_members_take_their_place():
    lua = "local BOSS = 1\nhandlers[1] = function() MM9.removeActor(BOSS) end\n"
    actors = [actor(0, 800, 1000), actor(1, 700, 1000), actor(2, 2500, 1000, sector=2, attributes=0x00010000),
              actor(3, 2600, 1000, sector=2, npc_id=5)]
    copies, report = run(actors, [{"members": ["M1", "M0"], "add": 2}, {"members": ["M2", "M3"], "add": 2}], lua)
    first, second = report["packs"]
    assert first["skipped"] == {"M1": "named by the map Lua"} and first["placed"] == 2
    assert all(c["copy_of"] == "M0" for c in first["copies"])
    assert second["skipped"] == {"M2": "hidden", "M3": "identity"} and second["placed"] == 0 and second["note"]
    assert report["summary"]["packs_scripted_only"] == 1


def test_a_member_without_room_hands_its_copy_to_the_pack_and_shortfalls_are_reported():
    actors = [actor(0, 4050, 50, sector=3), actor(1, 2500, 1000, sector=2)]
    copies, report = run(actors, [{"members": ["M0", "M1"], "add": 2}, {"members": ["M0"], "add": 1}])
    assert [c["copy_of"] for c in report["packs"][0]["copies"]] == ["M1", "M1"]
    assert report["packs"][1]["placed"] == 0 and report["packs"][1]["shortfall"] == 1
    assert report["summary"]["packs_short"] == 1


def test_lua_actor_indices():
    lua = "\n".join([
        "-- MM9.removeActor(99) in a comment",
        'evt.StatusText("removeActor(98)")',
        "MM9.removeActor(4)",
        "local YANMIR = 71",
        "evt.WakeActor(YANMIR)",
        "local SPAWNED = {SpawnLoc0 = {16, 17}, SpawnLoc1 = {18, 19}}",
        "for _, index in ipairs(SPAWNED[loc]) do evt.SetMonsterBit(index, MonsterBits.Invisible, false) end",
        "local DEATH = {[45] = {\"Spawner9\", \"default\"}}",
        "local MUMMIES = {[0] = {next = 5, onDeath = true}}",
        "local ACTOR = {[\"Eye0\"] = 104, [\"Eye1\"] = 105}",
        "local GENIE_ITEMS = {2, 359, 81}",
        "handlers[97] = function(context)",
        "    local index = context.actorIndex",
        "    if DEATH[index] ~= nil then spawn(DEATH[index][1]) end",
        "    if MUMMIES[index] ~= nil then evt.WakeActor(MUMMIES[index].next) end",
        "    if index == 33 then set(\"Dead\", 1) end",
        "end",
        "if msg == \"go\" then evt.WakeActor(ACTOR[target]) end",
        "if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 13, 0, false) then end",
        "if evt.CheckMonstersKilled(ActorKillCheck.Group, 70, 0, false) then end",
        "evt.SetDoorState(3, DoorAction.Open)",
    ])
    found = density.lua_actor_indices(lua, directories=("ACTOR",))
    assert {4, 71, 16, 17, 18, 19, 45, 0, 5, 33, 13} <= found
    assert not found & {99, 98, 104, 105, 2, 359, 81, 70, 3}
    assert {104, 105} <= density.lua_actor_indices(lua)


def test_actor_directories_take_the_copies():
    script = "local ACTOR = {[\"A\"] = 1}\nprint(1)\n"
    out = density.add_to_directories(script, ("ACTOR",), [{"anchor": "A_grow1", "actor_index": 7}])
    assert out.splitlines()[1].startswith('for name, index in pairs({["A_grow1"] = 7}) do ACTOR[name] = index end')


def test_unplaced_copies_move_to_the_roomiest_packs_up_to_their_capacity():
    actors = [actor(0, 2500, 1000, sector=2), actor(1, 700, 1000), actor(2, 2700, 600, sector=2, npc_id=4),
              actor(3, 4050, 50, sector=3), actor(4, 2300, 1700, sector=2, attributes=0x00010000)]
    packs = [{"members": ["M0"], "add": 1, "capacity": 6},       # room after its own copy: 4
             {"members": ["M1"], "add": 1, "capacity": 4},       # 2
             {"members": ["M2"], "add": 3, "capacity": 12},      # scripted only: 3 to move
             {"members": ["M3"], "add": 2, "capacity": 12},      # the closet: no spot, 2 to move
             {"members": ["M4"], "add": 3, "capacity": 12}]      # hidden only: 3 to move
    copies, report = run(actors, packs, counted_today=5)
    a, b, c, d, e = report["packs"]
    assert (a["placed"], a["moved_in"], a["room_left"]) == (1, 4, 0)
    assert (b["placed"], b["moved_in"], b["room_left"]) == (1, 2, 0)
    assert c["placed"] == d["placed"] == e["placed"] == 0
    summary = report["summary"]
    assert (summary["wanted_adds"], summary["placed_adds"], summary["moved_adds"], summary["unplaced_adds"]) == \
        (10, 8, 6, 2)
    assert sum(summary["unplaced_reasons"].values()) == 2
    assert (summary["target_total"], summary["placed_total"]) == (15, 13)
    assert len(copies) == 8 and all(c["copy_of"] in ("M0", "M1") for p in (a, b) for c in p["copies"])


def test_scripted_placements_groups_receivers_and_cinematics_are_not_copied():
    """The DAT placement's script, quest flag and unique name, a group the Lua addresses, an MM9.receives target (by
    index and by DAT name) and a cinematic's actor keep a member out (Lich Lab's LichSummoner, group 70)."""
    lua = "\n".join([
        "if evt.CheckMonstersKilled(ActorKillCheck.Group, 70, 0, false) then end",
        'if MM9.receives("lab", "Critter", "ForceBreak", 5) then end',
        'local KK = {{"Breaker", 6}}',
    ])
    dat = {"m0": ("Thrall", {"ScriptName": "scripts\\Summoner.scr"}), "m1": ("Thrall", {"ShouldRepopulate": 0}),
           "jk": ("Thrall", {}), "thrall": ("Thrall", {}), "m4": ("Thrall", {}), "breaker": ("Thrall", {}),
           "m7": ("Thrall", {}), "m8": ("Thrall", {}), "m9": ("Thrall", {})}
    references = density.References(dat=dat, name_uses=density.Counter(list(dat)), lua_groups=density.lua_group_numbers(lua),
                                    lua_names=density.lua_strings(lua), scene_indices=density.cinematic_actors(
                                        {"cinematics": [{"cues": [{"at": 0, "actor": 8}, {"look_at_actor": 9}]}]}))
    indices = density.lua_actor_indices(lua)
    cases = {"m0": (0, {}), "m1": (1, {}), "jk": (2, {}), "thrall": (3, {}), "m4": (4, {"group": 70}),
             "m5": (5, {}), "breaker": (6, {}), "m7": (7, {"monster_id": 9212}), "m8": (8, {}), "m9": (9, {})}
    reasons = {anchor: density.scripted_reason(actor(index, 0, 0, **dict({"group": 0}, **extra)), indices,
                                               references, anchor)
               for anchor, (index, extra) in cases.items()}
    assert reasons == {"m0": "script", "m1": "quest actor", "jk": "unique name", "thrall": None,
                       "m4": "group named by the map Lua", "m5": "named by the map Lua",
                       "breaker": "named by the map Lua", "m7": "boss", "m8": "named by the map's cinematics",
                       "m9": "named by the map's cinematics"}


def test_a_mixed_pack_grows_in_its_own_mix_not_its_first_member():
    # One Bone Thrasher (row 9100) listed first and three Skeletons (row 9200): two copies are both Skeletons.
    actors = [actor(0, 600, 1000), actor(1, 800, 1200, monster_info_id=9200), actor(2, 800, 800, monster_info_id=9200),
              actor(3, 700, 1400, monster_info_id=9200)]
    _, report = run(actors, [{"members": ["M0", "M1", "M2", "M3"], "add": 2}])
    copied = [c["copy_of"] for c in report["packs"][0]["copies"]]
    assert all(actors[int(anchor[1:])]["monster_info_id"] == 9200 for anchor in copied)
    assert len(set(copied)) == 2                                   # the least copied member first
    # Four copies of an even pair: two of each.
    pair = [actor(0, 600, 1000), actor(1, 800, 1200, monster_info_id=9200)]
    _, report = run(pair, [{"members": ["M0", "M1"], "add": 4}])
    assert sorted(c["copy_of"] for c in report["packs"][0]["copies"]) == ["M0", "M0", "M1", "M1"]


def test_moved_copies_keep_their_monster_row():
    # A scripted Skeleton's copy goes to the pack with an ordinary Skeleton, not to the roomier Thrall pack.
    lua = "local X = 0\nhandlers[1] = function() MM9.removeActor(X) end\n"
    actors = [actor(0, 2500, 1000, sector=2, monster_info_id=9200), actor(1, 700, 1000),
              actor(2, 2600, 1500, sector=2, monster_info_id=9200)]
    packs = [{"members": ["M0"], "add": 1, "capacity": 12},     # scripted only: its Skeleton copy moves
             {"members": ["M1"], "add": 0, "capacity": 12},      # Thralls, roomiest
             {"members": ["M2"], "add": 0, "capacity": 4}]       # a Skeleton
    _, report = run(actors, [p for p in packs], lua)
    receiver = report["packs"][2]
    assert receiver["moved_in"] == 1 and receiver["copies"][0]["copy_of"] == "M2"
    assert report["packs"][1]["moved_in"] == 0


def test_a_forced_arrival_keeps_its_quota_and_the_rest_move_to_other_packs():
    # The arrival stands by M0 in room B; M1's pack in room A (beyond its 600-unit radius) takes the rest.
    actors = [actor(0, 2500, 1000, sector=2), actor(1, 500, 1500)]
    packs = [{"members": ["M0"], "add": 4, "capacity": 12}, {"members": ["M1"], "add": 1, "capacity": 12}]
    arrivals = [{"name": "Landing", "at": [2500, 1100, 0], "radius": 900, "copies": 1}]
    anchors = {f"M{a['actor_index']}": a["actor_index"] for a in actors}
    copies, report = density.grow("testmap", actors, anchors, packs, world(), set(), arrivals=arrivals)
    near = [c for c in copies if density.arrival_distance(arrivals[0], (c["position"]["x"], c["position"]["y"],
                                                                        c["position"]["z"])) <= 900]
    assert len(near) == 1
    assert report["summary"]["arrivals"] == {"Landing": {"copies": 1, "quota": 1}}
    a, b = report["packs"]
    assert density.ARRIVAL_FULL in a["refused"]
    assert len(copies) == 5 and b["moved_in"] == 3


def test_pod_launchers_keep_their_quota_nearby_and_the_rest_grow_other_packs():
    # Two Lobbers in room A wanting two copies each: the quota of three nearby lets one launcher copy stand, and the
    # Thrall pack in room B (within the launchers' radius, but a Thrall is no launcher) takes the other three.
    lobber = 9086
    actors = [actor(0, 500, 1000, monster_info_id=lobber), actor(1, 1500, 600, monster_info_id=lobber),
              actor(2, 2500, 1000, sector=2)]
    packs = [{"members": ["M0"], "add": 2, "capacity": 12}, {"members": ["M1"], "add": 2, "capacity": 12},
             {"members": ["M2"], "add": 0, "capacity": 12}]
    copies, report = run(actors, packs)
    assert sum(1 for c in copies if c["monster_info_id"] == lobber) == density.LAUNCHERS_PER_SPOT - 2
    assert len(copies) == 4 and report["summary"]["unplaced_adds"] == 0
    assert report["packs"][2]["moved_in"] == 3
    assert any(density.LAUNCHERS_FULL in p.get("refused", {}) for p in report["packs"][:2])


def test_no_copy_under_a_floor_or_on_a_steep_face_and_none_of_a_buried_member():
    m = Map()
    m.floor(0, 0, 2000, 2000, 0, 1)                                  # the box's bottom (an open-air BLV's sky shell)
    m.floor(0, 0, 1000, 2000, 300, 1)                                # the ground over its west half, one-sided
    m.face([(1000, 0, 1), (1300, 0, 401), (1300, 2000, 401), (1000, 2000, 1)], 4, 1)   # a 53 degree slope
    blv = {"vertices": m.vertices, "faces": m.faces}
    w = density.World(blv, {"initial_state": {"doors": [], "face_attribute_overrides": []}}, set())
    assert w.under_cover(500, 1000, 0) and not w.under_cover(500, 1000, 300) and not w.under_cover(1500, 1000, 0)
    member = actor(0, 1600, 1000)
    assert w.spot(member, member, 1800, 1000, [member]) is not None    # beside it on the open floor
    assert w.check(member, member, 1150, 1000, [member])[1] == "under a floor"      # under the slope
    on_slope = actor(3, 1010, 1000, z=15)
    assert w.check(on_slope, on_slope, 1012, 1130, [on_slope])[1] == "steep"
    buried = actor(1, 500, 1000)                                       # on the bottom, under the ground
    assert w.check(buried, buried, 650, 1000, [buried])[1] == "member has no floor"
    standing = actor(2, 500, 1000, z=301)
    assert w.spot(standing, standing, 650, 1000, [standing]) is not None


def test_a_flyer_copy_keeps_its_height_only_under_a_high_enough_ceiling():
    m = Map()
    m.floor(0, 0, 2000, 1000, 0, 1)
    m.face([(1000, 0, 200), (1000, 1000, 200), (2000, 1000, 200), (2000, 0, 200)], 5, 1)   # a low ceiling, east half
    blv = {"vertices": m.vertices, "faces": m.faces}
    w = density.World(blv, {"initial_state": {"doors": [], "face_attribute_overrides": []}}, set())
    flyer = actor(0, 500, 500, z=301)
    assert w.spot(flyer, flyer, 700, 500, [flyer]) is not None
    assert w.check(flyer, flyer, 1300, 500, [flyer])[1] == "in the ceiling"
