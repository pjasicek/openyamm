"""MM9's posed people (RUDEProps and character Props whose script loops an animation) as actors, for every MM9 map.

MM9 places the innkeeper, the tavern drinkers, Ludwig at his desk, Bjarni on his chair, the Arena spectators and the
Thronheim council as props whose script loops one animation for ever (PropAnim.scr `LoopAnim <params>`,
Sturmgaardinn.scr, TryggvaSpeech.scr, ErccSpeech.scr, LudwigVan.scr, Bjarni.scr, AkeRetainer.scr). They never walk,
turn or look at the party; a click opens their RUDE dialogue (RUDENPCId) and a few scripts play another clip at a
moment (Ercc passes out, Ludwig looks up).

Here each is a friendly, passive, immobile actor on the existing HD model of its body (the row of its model and skin
below, no model of its own) that loops its pose clip: the map's load handler calls `evt.PlayActorClip(actor, clip,
true)` and `evt.FaceActorTo` (a map script's presentation: it replaces the AI's animation, keeps the body's facing
through a dialogue and turns the head look off). Its use and exit parts are the ordinary MM9 actor hooks (53000 /
50000 + DAT object index, game/mm9/Mm9RudeDialogue.h). The pose clips are script clips of the HD bodies
(level_generation/creatures/mm9_peasantm2_claude and mm9_peasantm2d_claude roles: sitting, sitting2, listen,
conv_seated, innkeeper2, ludwig_writing, ludwig_lookup, ercc01a-c, ercc02; the named heroes' `sit`).

    import rude_props
    record = rude_props.actor(content, o, entry, sector_of_room, names, group)    # in a map's actors()
    lines = rude_props.load_lines(actor_index, record, entry)                    # in its load handler
"""

from __future__ import annotations

import re

from mm9_monster_bodies import native_body

UNDER_FLOOR_SLACK = 64.0            # native units a posed person's MM9 foot may lie under its floor before it is a miss
JUST_UNDER_FLOOR = 8                # native units under its props.json height that count as rounding off the floor

# The HD actor row (9000 + MM9 row, actors.yml) that draws a body: (model stem, skin letter) for the peasant bodies,
# whose skins are tiers of two models (PeasantM2 a/b: mm9_peasantm2; c/d: mm9_peasantm2d), else the model stem. The
# seated models (PeasantMS*, PeasantFS*) are the standing bodies' seated variants (MM9's PeasantSeated library).
PEASANT_ROWS = {
    ("peasantm2", "a"): 9050, ("peasantm2", "b"): 9044, ("peasantm2", "c"): 9024, ("peasantm2", "d"): 9026,
    ("peasantm1", "a"): 9043, ("peasantm1", "b"): 9056,
    ("peasantf2", "a"): 9031, ("peasantf2", "b"): 9032,
}
HERO_ROWS = {"bjarni": 9246, "sigmund": 9247, "markel": 9248, "sven": 9249, "sven_arg": 9249, "tryggva": 9250,
             "foraddarre": 9252,
             "ercc": 9050}           # Ercc.ABC: PeasantM2 in skin PeasantM2a with a cup (the cup: a held item)

# The clip each script loops (MM9's LoopAnim), by script; PropAnim.scr loops its first parameter.
SCRIPT_POSES = {"sturmgaardinn.scr": None,          # LoopAnim Params: its parameter (Innkeeper2)
                "propanim.scr": None,
                "tryggvaspeech.scr": "listen",       # :Anim LoopAnim listen
                "erccspeech.scr": "sitting",         # :Init LoopAnim sitting
                "ludwigvan.scr": "ludwig_writing",   # Loopanim Ludwig_writting
                "akeretainer.scr": "sitting",        # LoopAnim sitting
                "bjarni.scr": "Sit"}                 # loopanim Sit
# MM9 clip names -> the HD bodies' role names
CLIP_ROLES = {"ludwig_writting": "ludwig_writing", "ludwig_lookup": "ludwig_lookup", "conv": "conv_seated"}
# (MM9 model, clip) -> the HD body's clip, where a prop model's own animation is not the seated library's of that name:
# Ercc.ABC's `sitting` holds the cup at his chest (the townsman's `ercc_sitting`, with the hand closed round the cup:
# level_generation/props/mm9_held_items_claude/scripts/grip_clips.py), PeasantSeated's rests the hands in the lap.
MODEL_CLIP_ROLES = {("ercc", "sitting"): "ercc_sitting"}


def _file_name(path) -> str:
    """A DAT path's file name, whichever separator it uses (Thronheim's council has models/Sven_ARG.ABC)."""
    return str(path).replace("\\", "/").split("/")[-1]


def body_row(entry: dict) -> int | None:
    """The HD row that draws this posed person, or None (not a person this table knows)."""
    model = re.sub(r"\.abc$", "", _file_name(entry.get("source_model", "")), flags=re.I).lower()
    skin = _file_name(str(entry.get("source_skin", "")).split(";")[0]).lower()
    seated = {"peasantms2": "peasantm2", "peasantms1": "peasantm1", "peasantfs2": "peasantf2"}.get(model, model)
    match = re.match(r"peasant[mf]\d([a-d])\.dtx$", skin)
    if seated in {m for m, _ in PEASANT_ROWS} and match:
        return PEASANT_ROWS.get((seated, match[1]))
    return HERO_ROWS.get(model)


def mm9_clip(entry: dict) -> str | None:
    """The animation the script loops, as MM9's model names it."""
    script = str(entry.get("script") or "").split("\\")[-1].lower()
    if script not in SCRIPT_POSES:
        return None
    return SCRIPT_POSES[script] or str(entry.get("script_params") or "").split()[0]


def pose_clip(entry: dict) -> str | None:
    """The clip the script loops, as the HD bodies name it."""
    clip = mm9_clip(entry)
    if clip is None:
        return None
    model = re.sub(r"\.abc$", "", _file_name(entry.get("source_model", "")), flags=re.I).lower()
    return MODEL_CLIP_ROLES.get((model, clip.lower())) or CLIP_ROLES.get(clip.lower(), clip.lower())


def mm9_foot(content, o: dict, entry: dict) -> float | None:
    """The native height of the lowest point of the model MM9 draws for a posed person: its box where its initial
    update and MoveToFloor leave it (prop_pose.mm9_centres, devdocs/mm9_rework/MM9_PROP_PLACEMENT_RE.md), the model at
    that centre plus its translation, posed in the animation its script loops. The HD pose clips are grounded (their
    lowest point at the actor's position), so the actor stands there: Bjarni's Sit keeps his standing hips, his box
    dropped onto the throne's invisible step; the tavern's seated drinkers' boxes (the torso, the legs hang below) onto
    the benches' invisible seats. Snapped to the floor, Bjarni sank into his throne."""
    import numpy as np
    from dungeon import prop_pose

    if getattr(content, "mm9_centres", None) is None:
        # MoveToFloor's ray hits MM9's physics world: the solid surfaces, the invisible collision brushes too (the
        # tavern benches' seats 49 units over the floor, the step of Bjarni's throne), not only the visible floors
        up = []
        for polygon in content.polygons:
            if polygon.role != "nonsolid" and polygon.normal[1] >= 0.7:
                ring = content.project.native(polygon.points)
                up += [(ring[0], ring[i], ring[i + 1]) for i in range(1, len(ring) - 1)]
        up = np.array(up, float).reshape(-1, 3, 3)

        def floor_z(x: float, y: float, z_max: float):
            z = prop_pose.surface_heights(up, np.array([[x, y]]), z_max)[0]
            return float(z) if np.isfinite(z) else None

        content.mm9_centres = prop_pose.mm9_centres(content.source.objects, content.project.native, floor_z)
    centre = content.mm9_centres.get(o["index"])
    if centre is None:
        return None
    mesh = prop_pose.mm9_mesh(o["properties"], centre, mm9_clip(entry))
    return None if mesh is None else float(mesh[:, 2].min())


def is_posed_person(entry: dict) -> bool:
    return entry.get("kind") == "npc" and body_row(entry) is not None and pose_clip(entry) is not None


def actor(content, o: dict, entry: dict, sector_of_room: dict, names: dict, group: int, bodies) -> dict:
    """The scene actor of a posed person: friendly, immobile, passive (no wander, chat or fidget of its own), never
    hurt, never moved (posed: it sits in its seat's collision), at its DAT plan position and at the height where MM9
    draws its posed model (mm9_foot); without the ABC, on the floor (MoveToFloor 1) or at its props.json height."""
    p = o["properties"]
    row = body_row(entry)
    rude = entry.get("rude_npc_id") or 0
    # MM9's RUDE name; one without a dialogue (Ercc, a DAT "RUDEProp1") is called by its model
    stem = re.sub(r"\.abc$", "", _file_name(entry.get("source_model", "")), flags=re.I)
    unnamed = re.fullmatch(r"(RUDE)?Prop\d*", entry["source_name"], re.I) is not None
    name = names.get(rude, entry["source_name"]) if rude else stem.capitalize() if unnamed else entry["source_name"]
    base = {"name": name, "attributes": 0, "hp": 20,
            "hostility_type": 0, "monster_info_id": row, "monster_id": row, "radius": 43, "height": 120,
            "move_speed": 0}
    extents = bodies.model_extents(str(p.get("Filename", "")))
    if extents is not None:
        base["height"], base["radius"] = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
    record = content.actor(o, base, sector_of_room, group=group, friendly=True, floor_query_lt=p["Pos"][1] + 24)
    record["mm9_source_object_index"] = o["index"]      # its RUDE use and exit hooks (53000 / 50000 + index)
    record["immobile"] = True
    record["posed"] = True              # never moved: it sits in its seat's collision (MapDeltaActor::posed)
    record["mm9_civilian"] = True
    record["mm9_can_receive_damage"] = False
    record["mm9_ai"] = {"profile": {"passive": True}, "script": str(entry.get("script") or "").split("\\")[-1]}
    if rude:
        record["mm9_rude_id"] = int(rude)
    foot = mm9_foot(content, o, entry)
    # never far under the floor the actor would stand on (content.actor puts it 1 over that floor, which for a seated
    # body can be its bench's seat, so only a clear miss counts): Thronheim's council Sven (Sven_ARG.ABC, his chair
    # modelled in) came out 164 units under the hall's floor (2026-11-08)
    floor = record["position"]["z"] - 1
    if foot is not None:
        record["position"]["z"] = int(round(floor if foot < floor - UNDER_FLOOR_SLACK else foot))
    if p.get("MoveToFloor", 1) and entry.get("z") is not None:
        # nor a few units under the props project's height (props.json z: the compiled floor for a body on the floor,
        # a seat for the seated townsfolk, who stay well under it): a body just under the compiled floor is in the
        # room below for the game, which drops it onto that room's floor (Sven: 3272 under the hall's 3277)
        z, top = record["position"]["z"], int(round(entry["z"]))
        if top - JUST_UNDER_FLOOR <= z < top:
            record["position"]["z"] = top
    elif not p.get("MoveToFloor", 1):
        record["position"]["z"] = int(round(entry["z"]))
    record["mm9_pose_clip"] = pose_clip(entry)        # read back by load_lines (removed from the scene by finish())
    return record


def load_lines(record: dict) -> list[str]:
    """Lua for the map's load handler: the pose loops, the body keeps its placed facing."""
    import math
    index, x, y = record["actor_index"], record["position"]["x"], record["position"]["y"]
    yaw = record["initial_yaw_units"] / 2048 * 2 * math.pi
    fx, fy = round(x + 256 * math.cos(yaw)), round(y + 256 * math.sin(yaw))
    clip = record["mm9_pose_clip"]
    return [f"    evt.PlayActorClip({index}, \"{clip}\", true); evt.FaceActorTo({index}, {fx}, {fy}, 0)"
            f"   -- {record['name']}: LoopAnim {clip}"]


def use_voice(entry: dict) -> str | None:
    """The voice line its script plays when used (`:OnUse ... Playsound voices\\NPC\\NPC_057.wav`), as a sound path."""
    from pathlib import Path
    script = str(entry.get("script") or "").split("\\")[-1]
    folder = Path(__file__).resolve().parents[3] / "mm9/extracted/SCRIPTS/SCRIPTS"
    path = next((f for f in folder.iterdir() if f.name.lower() == script.lower()), None) if script else None
    if path is None:
        return None
    text = re.sub(r";.*", "", path.read_text(errors="ignore"))
    use = re.search(r"^:OnUse\b(.*?)^:", text, re.S | re.M | re.I)
    voice = use and re.search(r"Playsound\s+\\?(voices\\npc\\npc_\d+\.wav)", use[1], re.I)
    return voice[1].replace("\\", "/").lower() if voice else None


def finish(record: dict) -> dict:
    """The scene record without the converter's own fields."""
    record.pop("mm9_pose_clip", None)
    return record
