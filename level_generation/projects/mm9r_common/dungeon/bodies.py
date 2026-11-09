"""
MM9's monster bodies for placed actors (devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md). MM9 sizes a monster by its
model's initial animation dims times its scale, and the scale is the MONSTERS.txt `Scale` unless the DAT object has
its own `Scale` other than 1.0, which then replaces it (it does not multiply). The MM9 monster table carries the body
at the row's Scale (tools/mm9_import_discovery/mm9_monster_body_overrides.tsv), so an object at Scale 1 keeps the
table's radius and height; only an object with its own Scale needs a body of its own. See ../DUNGEON_PLAYBOOK.md.
"""

from __future__ import annotations

from .source import ROOT  # noqa: F401 - puts tools/mm9_import_discovery on sys.path

from mm9_monster_bodies import MM9_TO_OPENYAMM_COORDINATE_SCALE, Mm9MonsterBodies  # noqa: E402

MM9_MONSTER_ID_BASE = 9000
_bodies: Mm9MonsterBodies | None = None


def mm9_bodies() -> Mm9MonsterBodies:
    global _bodies
    if _bodies is None:
        _bodies = Mm9MonsterBodies()
    return _bodies


def object_scale(properties: dict) -> float:
    return float(properties.get("Scale", 1.0) or 1.0)


def placed_body(monster_id: int, properties: dict) -> dict:
    """{radius, height} for a placed actor of MM9 monster row monster_id (9xxx) with these DAT properties: empty at
    DAT Scale 1 (the table's body applies) or for a row that is not an MM9 monster row with a shipped model; else
    the row's model at the DAT Scale. The row's model, not the DAT `Filename`: it is the model the actor is drawn
    with."""
    scale = object_scale(properties)
    source_number = int(monster_id) - MM9_MONSTER_ID_BASE
    if scale == 1.0 or source_number not in mm9_bodies().rows:
        return {}
    body = mm9_bodies().body(source_number, scale)
    if body is None:
        return {}
    return {"radius": body[1], "height": body[0]}


def draw_scale(monster_id: int, properties: dict) -> float | None:
    """The scene actor's `draw_scale` (the 3D model's size against its binding; openyamm-19 / openyamm-e1, user
    2026-11-06): MM9 draws a placement at its own DAT Scale when that is not 1.0, else at its MONSTERS.txt row Scale,
    and the model binding already carries the row Scale (100 x it), so the factor is DAT Scale / row Scale. None (no
    field) for an object at Scale 1 or a row that is not an MM9 monster row. The actor's height and radius stay MM9's
    collision body (placed_body); without this field the engine would size the model by body height / descriptor."""
    scale = object_scale(properties)
    source_number = int(monster_id) - MM9_MONSTER_ID_BASE
    if scale == 1.0 or source_number not in mm9_bodies().rows:
        return None
    factor = scale / (mm9_bodies().row_scale(source_number) or 1.0)
    return None if abs(factor - 1.0) < 1e-6 else round(factor, 4)


def half_extents_body(half_width_lt: float, half_height_lt: float, scale: float) -> dict:
    """{radius, height} of a body given by its half extents (LT) at an effective scale (an NPC or a model the table
    does not carry): MM9's rule for a map's own body constants."""
    return {"radius": int(round(half_width_lt * scale * MM9_TO_OPENYAMM_COORDINATE_SCALE)),
            "height": int(round(2 * half_height_lt * scale * MM9_TO_OPENYAMM_COORDINATE_SCALE))}
