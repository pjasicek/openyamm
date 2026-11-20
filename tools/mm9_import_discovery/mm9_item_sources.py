#!/usr/bin/env python3
from __future__ import annotations

import math
import re
import struct
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable

import yaml


MM9_QBIT_BASE = 90000
MM9_MECHANISM_EVENT_ID_BASE = 30000
MM9_BARREL_LIQUID_COG_BASE = 20000
MM9_BARREL_LIQUID_TEXTURES = (
    "skins/props/liquid-red.dtx",
    "skins/props/liquid-blue.dtx",
    "skins/props/liquid-green.dtx",
    "skins/props/liquid-purple.dtx",
    "skins/props/liquid-white.dtx",
    "skins/props/liquid-yellow.dtx",
    "skins/props/liquid-swamp.dtx",
    "skins/props/barrel_water.dtx",
)


class Mm9ItemSourceError(ValueError):
    pass


@dataclass(frozen=True)
class SourceProvenance:
    source_id: str
    source_object_index: int
    source_class: str
    source_name: str
    source_model: str
    source_skin: str
    source_position_lt: tuple[float, float, float]
    position: tuple[int, int, int]
    script_name: str
    script_params: str


@dataclass(frozen=True)
class FixedContainerItem:
    slot: int
    raw_mm9_item_id: int
    item_id: int


@dataclass(frozen=True)
class ItemGrant:
    raw_mm9_item_id: int
    item_id: int
    quantity: int = 1


@dataclass(frozen=True)
class WorldItemSource:
    provenance: SourceProvenance
    kind: str
    raw_primary_item_id: int
    item_id: int
    required_qbits: tuple[int, ...]
    forbidden_qbits: tuple[int, ...]
    required_items: tuple[int, ...]
    forbidden_items: tuple[int, ...]
    grant_items: tuple[ItemGrant, ...]
    take_items: tuple[int, ...]
    set_qbits: tuple[int, ...]
    clear_qbits: tuple[int, ...]
    random_item_pool: tuple[int, ...]
    on_pickup_event: str
    consume_on_success: bool


@dataclass(frozen=True)
class UnresolvedItemReference:
    source_id: str
    source_object_index: int
    raw_mm9_item_id: int
    reason: str
    blocks_generation: bool = True


@dataclass(frozen=True)
class LootContainerSource:
    provenance: SourceProvenance
    container_id: int
    kind: str
    presentation: str
    random_treasure_level: int
    treasure_type: int
    gold: int
    gold_only: bool
    random: bool
    ai_drop: bool
    trap_level: int
    should_repopulate: bool
    fixed_items: tuple[FixedContainerItem, ...]
    remove_when_empty: bool


@dataclass(frozen=True)
class SearchableLootPropSource:
    provenance: SourceProvenance
    kind: str
    random_treasure_level: int
    loot_rolls: int
    disease_chance: int
    source_disease_power: int
    keep_visual_after_search: bool


@dataclass(frozen=True)
class ActorLootOverride:
    source_object_index: int
    procedural_death_loot: bool


@dataclass(frozen=True)
class SpawnedLootContainerSource:
    provenance: SourceProvenance
    kind: str
    presentation: str
    random_treasure_level: int
    treasure_type: int
    gold: int
    gold_only: bool
    random: bool
    ai_drop: bool
    fixed_items: tuple[FixedContainerItem, ...]
    remove_when_empty: bool


@dataclass(frozen=True)
class PersistentItemMechanismSource:
    provenance: SourceProvenance
    kind: str
    handler: str
    required_items: tuple[int, ...]
    grant_items: tuple[ItemGrant, ...]
    random_item_pool: tuple[int, ...]
    model_variants: tuple[str, ...]
    model_variant_skins: tuple[str, ...]


@dataclass
class Mm9BarrelSource:
    provenance: SourceProvenance
    interaction_event_id: int
    liquid_texture_cog: int
    bmodel_index: int = 0xFFFFFFFF
    liquid_faces: tuple[int, ...] = ()
    liquid_texture_aliases: tuple[str, ...] = ()


@dataclass
class Mm9ItemSourceManifest:
    map_id: str
    world_items: list[WorldItemSource] = field(default_factory=list)
    loot_containers: list[LootContainerSource] = field(default_factory=list)
    searchable_loot_props: list[SearchableLootPropSource] = field(default_factory=list)
    actor_loot_overrides: list[ActorLootOverride] = field(default_factory=list)
    spawned_loot_containers: list[SpawnedLootContainerSource] = field(default_factory=list)
    persistent_item_mechanisms: list[PersistentItemMechanismSource] = field(default_factory=list)
    barrels: list[Mm9BarrelSource] = field(default_factory=list)
    unresolved_item_references: list[UnresolvedItemReference] = field(default_factory=list)

    def excluded_baked_object_indices(self) -> set[int]:
        return {
            source.provenance.source_object_index
            for source in self.world_items
        } | {
            source.provenance.source_object_index
            for source in self.loot_containers
            if source.kind == "treasure_bag"
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def require_resolved_item_references(self) -> None:
        blocking_references = [
            source for source in self.unresolved_item_references if source.blocks_generation
        ]
        if not blocking_references:
            return
        references = ", ".join(
            f"object {source.source_object_index}:raw item {source.raw_mm9_item_id}"
            for source in blocking_references
        )
        raise Mm9ItemSourceError(f"{self.map_id}: unresolved item-source references: {references}")

    def scene_data(self) -> dict[str, Any]:
        return {
            "world_items": [world_item_scene_data(source) for source in self.world_items],
            "loot_containers": [loot_container_scene_data(source) for source in self.loot_containers],
            "searchable_loot_props": [
                searchable_loot_prop_scene_data(source) for source in self.searchable_loot_props
            ],
            "actor_loot_overrides": [asdict(source) for source in self.actor_loot_overrides],
            "spawned_loot_containers": [
                spawned_loot_container_scene_data(source) for source in self.spawned_loot_containers
            ],
            "persistent_item_mechanisms": [
                persistent_item_mechanism_scene_data(source)
                for source in self.persistent_item_mechanisms
            ],
            "barrels": [mm9_barrel_scene_data(source) for source in self.barrels],
            "unresolved_item_references": [asdict(source) for source in self.unresolved_item_references],
        }


@dataclass(frozen=True)
class AuditedPickupRule:
    raw_item_ids: tuple[int, ...]
    kind: str = "world_item"
    required_qbits: tuple[int, ...] = ()
    forbidden_qbits: tuple[int, ...] = ()
    required_items: tuple[int, ...] = ()
    forbidden_items: tuple[int, ...] = ()
    take_items: tuple[int, ...] = ()
    set_qbits: tuple[int, ...] = ()
    clear_qbits: tuple[int, ...] = ()
    random_item_range: tuple[int, int] | None = None
    on_pickup_event: str = ""


@dataclass(frozen=True)
class AuditedPersistentItemMechanismRule:
    kind: str
    handler: str
    required_raw_items: tuple[int, ...] = ()
    grant_raw_items: tuple[int, ...] = ()
    random_raw_items: tuple[int, ...] = ()
    model_variants: tuple[str, ...] = ()
    model_variant_skins: tuple[str, ...] = ()


def pickup_rule(raw_item_id: int, **kwargs: Any) -> AuditedPickupRule:
    return AuditedPickupRule(raw_item_ids=(raw_item_id,), **kwargs)


GENIE_LAMP_RANDOM_RAW_ITEMS = (
    2, 359, 81, 420, 86, 510, 285, 318, 71, 319, 96, 97, 320, 26, 519, 76, 87, 61, 36, 18,
    41, 297, 296, 295, 2, 56, 421, 66, 292, 291, 290, 415, 288, 287, 294, 155, 332, 518, 150,
    547, 538, 333, 142, 334, 552, 553, 554, 335, 160, 548, 346, 349, 134, 327, 133, 422, 126,
    127, 530, 350, 254,
)


AUDITED_PICKUP_RULES: dict[tuple[str, int], AuditedPickupRule] = {
    ("1000terrors", 2037): pickup_rule(598),
    ("afterworld", 124): pickup_rule(567, forbidden_items=(567,)),
    ("afterworld", 125): pickup_rule(565, forbidden_items=(565,)),
    ("afterworld", 126): pickup_rule(566, forbidden_items=(566,)),
    ("afterworld", 127): pickup_rule(564, forbidden_items=(564,)),
    ("afterworld", 128): pickup_rule(563, forbidden_items=(563,)),
    ("arslegardcity", 449): pickup_rule(575, forbidden_items=(575,)),
    ("beethoven", 778): pickup_rule(248, kind="quest_world_item", on_pickup_event="beethoven_manuscript"),
    ("bootcamp", 205): pickup_rule(583, forbidden_items=(583,)),
    ("bootcamp", 206): pickup_rule(584, forbidden_items=(584,)),
    ("bootcamp", 212): pickup_rule(585, forbidden_items=(585,)),
    ("bootcamp", 213): pickup_rule(586, forbidden_items=(586,)),
    ("bootcamp", 214): pickup_rule(587, forbidden_items=(587,)),
    ("bootcamp", 215): pickup_rule(588, forbidden_items=(588,)),
    ("bootcamp", 218): pickup_rule(548),
    ("bootcamp", 219): pickup_rule(523),
    ("bootcamp", 220): pickup_rule(511),
    ("bootcamp", 221): pickup_rule(581, forbidden_items=(581,)),
    ("bootcamp", 222): pickup_rule(582, forbidden_items=(582,)),
    ("bootcamp", 223): pickup_rule(532),
    ("bootcamp", 224): pickup_rule(555),
    ("bootcamp", 225): pickup_rule(547),
    ("chasmofthedead", 1313): pickup_rule(447, kind="quest_world_item", forbidden_qbits=(296,), set_qbits=(296,)),
    ("chasmofthedead", 1314): pickup_rule(390, kind="quest_world_item", on_pickup_event="crona_kiga"),
    ("darkpassageway", 576): pickup_rule(483),
    ("drangheim", 25): pickup_rule(
        372,
        kind="quest_world_item",
        required_qbits=(128,),
        forbidden_qbits=(131,),
        set_qbits=(131,)),
    ("drangheim", 26): pickup_rule(
        371,
        kind="quest_world_item",
        required_qbits=(128,),
        forbidden_qbits=(130,),
        set_qbits=(130,)),
    ("drangheim", 27): pickup_rule(
        370,
        kind="quest_world_item",
        required_qbits=(128,),
        forbidden_qbits=(132,),
        set_qbits=(132,)),
    ("drangheim", 28): AuditedPickupRule(
        raw_item_ids=(347, 560),
        kind="quest_world_item",
        required_items=(244,),
        take_items=(244,),
        set_qbits=(283, 290),
        on_pickup_event="real_verhoffin_book"),
    ("guberland", 229): pickup_rule(240, forbidden_items=(240,)),
    ("inventastorca", 413): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 414): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 415): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 416): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 417): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 418): pickup_rule(252, forbidden_qbits=(337,)),
    ("inventastorca", 419): pickup_rule(252, forbidden_qbits=(337,)),
    ("klusoshouse", 247): pickup_rule(
        29,
        kind="quest_world_item",
        forbidden_qbits=(223,),
        set_qbits=(223,),
        on_pickup_event="blackheart_alarm"),
    ("lichlab", 1500): pickup_rule(378),
    ("lichlab", 1501): pickup_rule(378),
    ("lichlab", 1502): pickup_rule(378),
    ("lichlab", 1503): pickup_rule(378),
    ("lichlab", 1504): pickup_rule(378),
    ("lichlab", 1505): pickup_rule(378),
    ("lichlab", 1509): pickup_rule(358),
    ("lichlab", 1510): pickup_rule(358),
    ("lichlab", 1511): pickup_rule(358),
    ("lichlab", 1512): pickup_rule(358),
    ("lichlab", 1514): pickup_rule(378),
    ("lindisfarnemonastery", 407): pickup_rule(197, kind="quest_world_item", on_pickup_event="thjorad"),
    ("ruinedtemple", 5): pickup_rule(241, kind="quest_world_item", set_qbits=(256,)),
    ("tasaracademy", 692): AuditedPickupRule((), random_item_range=(285, 306)),
    ("tasaracademy", 693): AuditedPickupRule((), random_item_range=(285, 306)),
    ("tasaracademy", 694): AuditedPickupRule((), random_item_range=(285, 306)),
    ("tasaracademy", 695): pickup_rule(285),
    ("tasaracademy", 697): pickup_rule(391, kind="quest_world_item", on_pickup_event="book_of_rules"),
    ("tasaracademy", 700): AuditedPickupRule((), random_item_range=(285, 306)),
    ("tasaracademy", 701): AuditedPickupRule((), random_item_range=(285, 306)),
    ("templeofhonk", 61): pickup_rule(
        445,
        kind="quest_world_item",
        set_qbits=(7000,),
        on_pickup_event="accountant_key"),
    ("templeofhonk", 453): pickup_rule(369, kind="quest_world_item", on_pickup_event="golden_honk"),
    ("thjorgardcity", 1094): AuditedPickupRule(
        raw_item_ids=(560, 244, 347),
        kind="quest_world_item",
        required_qbits=(375,),
        forbidden_qbits=(374,),
        set_qbits=(374,),
        on_pickup_event="great_book_key"),
    ("thronheimcity", 55): pickup_rule(
        375,
        kind="quest_world_item",
        required_qbits=(214,),
        forbidden_qbits=(216,),
        set_qbits=(216,)),
    ("verhoffinruins", 229): pickup_rule(
        242,
        kind="quest_world_item",
        set_qbits=(281, 290,)),
    ("verhoffinruins", 232): pickup_rule(
        392,
        kind="quest_world_item",
        required_qbits=(99,),
        forbidden_qbits=(100,),
        set_qbits=(100,)),
    ("verhoffinruins", 651): pickup_rule(559),
    ("wizardslab", 877): pickup_rule(368, kind="quest_world_item", on_pickup_event="saints_relic"),
    ("yanmirsfort", 617): pickup_rule(
        570,
        kind="quest_world_item",
        set_qbits=(7001,),
        on_pickup_event="yanmirs_key"),
}


# Raw item 386 has no source definition anywhere in the shipped item table. Keep the authored prop and the broken
# reference visible, but do not manufacture a semantic pickup or exclude its original geometry.
AUDITED_UNSUPPORTED_PICKUPS: dict[tuple[str, int], tuple[int, str]] = {
    ("wizardslab", 592): (
        386,
        "reviewed unsupported pickup: raw MM9 item id is absent from MASTERITEMLIST.csv",
    ),
}


AUDITED_PERSISTENT_ITEM_MECHANISMS: dict[
    tuple[str, int], AuditedPersistentItemMechanismRule
] = {
    ("1000terrors", 1953): AuditedPersistentItemMechanismRule(
        kind="reusable_random_dispenser",
        handler="genie_lamp",
        random_raw_items=GENIE_LAMP_RANDOM_RAW_ITEMS,
    ),
    ("lichlab", 1506): AuditedPersistentItemMechanismRule(
        kind="reusable_converter",
        handler="elixir_burner",
        required_raw_items=(358, 561),
        grant_raw_items=(246,),
    ),
    ("lichlab", 1507): AuditedPersistentItemMechanismRule(
        kind="reusable_converter",
        handler="elixir_cookpot",
        required_raw_items=(378,),
        grant_raw_items=(561,),
    ),
    ("thjoradmine", 1464): AuditedPersistentItemMechanismRule(
        kind="persistent_model_variant",
        handler="slag_extractor",
        required_raw_items=(399,),
        grant_raw_items=(398,),
        model_variants=(
            "models/PickUpItems/Quest/Machine-Part_Whole.ABC",
        ),
        model_variant_skins=("skins/PickUpItems/Quest/MachinePart_Whole.dtx",),
    ),
    ("thjoradmine", 762): AuditedPersistentItemMechanismRule(
        kind="persistent_socket_controller",
        handler="slag_extractor_socket",
        required_raw_items=(399,),
    ),
    ("verhoffinruins", 527): AuditedPersistentItemMechanismRule(
        kind="persistent_socket_controller",
        handler="capstone_pedestal",
        required_raw_items=(396,),
    ),
    ("verhoffinruins", 650): AuditedPersistentItemMechanismRule(
        kind="persistent_socket",
        handler="capstone_socket",
        required_raw_items=(396,),
    ),
}

for _object_index, _location in (
    (708, "Defense"),
    (709, "Offense"),
    (710, "Intelligence"),
    (711, "Strategy"),
    (712, "Start"),
    (738, "Defense"),
):
    AUDITED_PERSISTENT_ITEM_MECHANISMS[("tasaracademy", _object_index)] = (
        AuditedPersistentItemMechanismRule(
            kind="staged_item_table",
            handler="tasar_textbook_table",
            required_raw_items=(435, 436, 437, 438),
        )
    )

for _object_index in range(714, 734):
    AUDITED_PERSISTENT_ITEM_MECHANISMS[("tasaracademy", _object_index)] = (
        AuditedPersistentItemMechanismRule(
            kind="staged_item_position",
            handler="tasar_textbook",
            grant_raw_items=(435 + ((_object_index - 714) % 4),),
        )
    )


class Mm9ItemIdMap:
    def __init__(self, raw_to_runtime: dict[int, int]) -> None:
        self._raw_to_runtime = dict(raw_to_runtime)

    @classmethod
    def load(cls, path: Path) -> "Mm9ItemIdMap":
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        mappings = document.get("mappings")
        if not isinstance(mappings, list):
            raise Mm9ItemSourceError(f"{path}: missing mappings list")

        raw_to_runtime: dict[int, int] = {}
        for mapping in mappings:
            if not isinstance(mapping, dict):
                raise Mm9ItemSourceError(f"{path}: invalid item-id mapping")
            raw_id = int(mapping.get("raw_mm9_id", 0))
            item_id = int(mapping.get("item_id", 0))
            if raw_id <= 0 or item_id <= 0:
                raise Mm9ItemSourceError(f"{path}: invalid mapping {mapping!r}")
            if raw_id in raw_to_runtime:
                raise Mm9ItemSourceError(f"{path}: duplicate raw MM9 item id {raw_id}")
            raw_to_runtime[raw_id] = item_id
        return cls(raw_to_runtime)

    def translate(self, raw_mm9_item_id: int, source_description: str) -> int:
        if raw_mm9_item_id <= 0:
            raise Mm9ItemSourceError(f"{source_description}: item id must be positive")
        item_id = self._raw_to_runtime.get(raw_mm9_item_id)
        if item_id is None:
            raise Mm9ItemSourceError(
                f"{source_description}: raw MM9 item id {raw_mm9_item_id} has no canonical mapping"
            )
        return item_id

    def try_translate(self, raw_mm9_item_id: int) -> int | None:
        return self._raw_to_runtime.get(raw_mm9_item_id)


def canonical_map_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def mm9_qbit(raw_qbit: int) -> int:
    if raw_qbit < 0:
        raise Mm9ItemSourceError(f"MM9 QBit must not be negative: {raw_qbit}")
    return MM9_QBIT_BASE + raw_qbit


def property_nodes(world_object: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for prop in world_object.properties:
        if getattr(prop, "decoded", True):
            result[str(prop.name).lower()] = prop
    return result


def property_values(world_object: Any) -> dict[str, Any]:
    return {name: prop.value for name, prop in property_nodes(world_object).items()}


def integral_property(world_object: Any, name: str, default: int = 0) -> int:
    prop = property_nodes(world_object).get(name.lower())
    if prop is None:
        return default

    value = prop.value
    raw_data = getattr(prop, "raw_data", b"")
    code = int(getattr(prop, "code", -1))
    if code in {4, 6, 9} and isinstance(raw_data, bytes) and len(raw_data) == 4:
        float_value = struct.unpack("<f", raw_data)[0]
        if math.isfinite(float_value):
            rounded = int(round(float_value))
            if abs(float_value - rounded) <= 0.001:
                return rounded

    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return int(round(float(value)))
    if isinstance(value, str):
        try:
            return int(value.strip(), 0)
        except ValueError:
            pass
    raise Mm9ItemSourceError(f"{world_object.name}.{name}: expected an integral property, got {value!r}")


def boolean_property(world_object: Any, name: str, default: bool = False) -> bool:
    nodes = property_nodes(world_object)
    if name.lower() not in nodes:
        return default
    value = nodes[name.lower()].value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off", "none"}
    return bool(value)


def string_property(world_object: Any, name: str, default: str = "") -> str:
    prop = property_nodes(world_object).get(name.lower())
    if prop is None or prop.value is None:
        return default
    return str(prop.value)


def source_position_lt(world_object: Any) -> tuple[float, float, float]:
    value = property_values(world_object).get("pos")
    if not isinstance(value, list) or len(value) != 3:
        return (0.0, 0.0, 0.0)
    return (float(value[0]), float(value[1]), float(value[2]))


def converted_position(position_lt: tuple[float, float, float], scale: float) -> tuple[int, int, int]:
    return (
        int(round(position_lt[0] * scale)),
        int(round(position_lt[2] * scale)),
        int(round(position_lt[1] * scale)),
    )


def build_provenance(map_id: str, object_index: int, world_object: Any, scale: float) -> SourceProvenance:
    position_lt = source_position_lt(world_object)
    return SourceProvenance(
        source_id=f"mm9:{map_id}:object:{object_index}",
        source_object_index=object_index,
        source_class=str(world_object.name),
        source_name=string_property(world_object, "Name", f"{world_object.name}{object_index}"),
        source_model=string_property(world_object, "Filename"),
        source_skin=string_property(world_object, "Skin"),
        source_position_lt=position_lt,
        position=converted_position(position_lt, scale),
        script_name=string_property(world_object, "ScriptName"),
        script_params=string_property(world_object, "ScriptParams"),
    )


def scene_provenance(provenance: SourceProvenance) -> dict[str, Any]:
    return {
        "source_id": provenance.source_id,
        "source_object_index": provenance.source_object_index,
        "source_class": provenance.source_class,
        "source_name": provenance.source_name,
        "source_model": provenance.source_model,
        "source_skin": provenance.source_skin,
        "source_position_lt": list(provenance.source_position_lt),
        "position": {
            "x": provenance.position[0],
            "y": provenance.position[1],
            "z": provenance.position[2],
        },
        "script_name": provenance.script_name,
        "script_params": provenance.script_params,
    }


def fixed_items_scene_data(items: tuple[FixedContainerItem, ...]) -> list[dict[str, int]]:
    return [asdict(item) for item in items]


def world_item_scene_data(source: WorldItemSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "kind": source.kind,
        "raw_primary_item_id": source.raw_primary_item_id,
        "item_id": source.item_id,
        "required_qbits": list(source.required_qbits),
        "forbidden_qbits": list(source.forbidden_qbits),
        "required_items": list(source.required_items),
        "forbidden_items": list(source.forbidden_items),
        "grant_items": [asdict(item) for item in source.grant_items],
        "take_items": list(source.take_items),
        "set_qbits": list(source.set_qbits),
        "clear_qbits": list(source.clear_qbits),
        "random_item_pool": list(source.random_item_pool),
        "on_pickup_event": source.on_pickup_event,
        "consume_on_success": source.consume_on_success,
    })
    return result


def loot_container_scene_data(source: LootContainerSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "container_id": source.container_id,
        "kind": source.kind,
        "presentation": source.presentation,
        "world_visual": {
            "kind": "bmodel" if source.kind == "chest" else "billboard",
            "source_object_index": source.provenance.source_object_index,
        },
        "random_treasure_level": source.random_treasure_level,
        "treasure_type": source.treasure_type,
        "gold": source.gold,
        "gold_only": source.gold_only,
        "random": source.random,
        "ai_drop": source.ai_drop,
        "trap_level": source.trap_level,
        "should_repopulate": source.should_repopulate,
        "fixed_items": fixed_items_scene_data(source.fixed_items),
        "remove_when_empty": source.remove_when_empty,
    })
    return result


def searchable_loot_prop_scene_data(source: SearchableLootPropSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "kind": source.kind,
        "world_visual": {
            "kind": "bmodel",
            "source_object_index": source.provenance.source_object_index,
        },
        "random_treasure_level": source.random_treasure_level,
        "loot_rolls": source.loot_rolls,
        "hazard": {
            "condition": "disease",
            "chance": source.disease_chance,
            "comparison": "roll_1_100_strictly_less_than",
            "severity": "mm9_native_fixed",
        },
        "source_disease_power": source.source_disease_power,
        "keep_visual_after_search": source.keep_visual_after_search,
    })
    return result


def spawned_loot_container_scene_data(source: SpawnedLootContainerSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "kind": source.kind,
        "presentation": source.presentation,
        "spawn_on_destroy": True,
        "random_treasure_level": source.random_treasure_level,
        "treasure_type": source.treasure_type,
        "gold": source.gold,
        "gold_only": source.gold_only,
        "random": source.random,
        "ai_drop": source.ai_drop,
        "fixed_items": fixed_items_scene_data(source.fixed_items),
        "remove_when_empty": source.remove_when_empty,
    })
    return result


def persistent_item_mechanism_scene_data(source: PersistentItemMechanismSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "kind": source.kind,
        "handler": source.handler,
        "world_visual": {
            "kind": "bmodel_group",
            "source_object_index": source.provenance.source_object_index,
        },
        "required_items": list(source.required_items),
        "grant_items": [asdict(item) for item in source.grant_items],
        "random_item_pool": list(source.random_item_pool),
        "model_variants": list(source.model_variants),
        "model_variant_skins": list(source.model_variant_skins),
    })
    return result


def mm9_barrel_scene_data(source: Mm9BarrelSource) -> dict[str, Any]:
    result = scene_provenance(source.provenance)
    result.update({
        "kind": "barrel",
        "interaction_event_id": source.interaction_event_id,
        "liquid_texture_cog": source.liquid_texture_cog,
        "bmodel_index": source.bmodel_index,
        "liquid_faces": list(source.liquid_faces),
        "has_liquid_surface": bool(source.liquid_faces),
        "liquid_texture_aliases": list(source.liquid_texture_aliases),
    })
    return result


def fixed_container_items(
    world_object: Any,
    item_ids: Mm9ItemIdMap,
    source_description: str,
    slots: Iterable[int] = range(1, 6),
) -> tuple[FixedContainerItem, ...]:
    result: list[FixedContainerItem] = []
    for slot in slots:
        raw_id = integral_property(world_object, f"Item{slot}")
        if raw_id <= 0:
            continue
        result.append(FixedContainerItem(
            slot=slot,
            raw_mm9_item_id=raw_id,
            item_id=item_ids.translate(raw_id, f"{source_description}.Item{slot}"),
        ))
    return tuple(result)


def loot_container_from_object(
    map_id: str,
    object_index: int,
    world_object: Any,
    container_id: int,
    item_ids: Mm9ItemIdMap,
    scale: float,
) -> LootContainerSource:
    kind = "chest" if str(world_object.name).lower() == "treasurechest" else "treasure_bag"
    source_description = f"{map_id} object {object_index} ({world_object.name})"
    return LootContainerSource(
        provenance=build_provenance(map_id, object_index, world_object, scale),
        container_id=container_id,
        kind=kind,
        presentation="mm9_chest" if kind == "chest" else "mm9_treasure_bag",
        random_treasure_level=integral_property(world_object, "TreasureLevel"),
        treasure_type=integral_property(world_object, "TreasureType0_7"),
        gold=integral_property(world_object, "Gold"),
        gold_only=boolean_property(world_object, "GoldOnly"),
        random=boolean_property(world_object, "Random"),
        ai_drop=boolean_property(world_object, "AIDrop"),
        trap_level=integral_property(world_object, "TrapLevel"),
        should_repopulate=boolean_property(world_object, "ShouldRepopulate"),
        fixed_items=fixed_container_items(world_object, item_ids, source_description),
        remove_when_empty=kind == "treasure_bag",
    )


def parse_spawn_properties(value: str, source_description: str) -> tuple[str, dict[str, str]]:
    chunks = [chunk.strip() for chunk in value.split(";") if chunk.strip()]
    if not chunks:
        raise Mm9ItemSourceError(f"{source_description}: empty SpawnObject")
    first = chunks[0].split(None, 1)
    class_name = first[0]
    assignments = chunks[1:]
    if len(first) == 2:
        assignments.insert(0, first[1])

    properties: dict[str, str] = {}
    for assignment in assignments:
        parts = assignment.split(None, 1)
        if len(parts) != 2:
            raise Mm9ItemSourceError(f"{source_description}: malformed SpawnObject field {assignment!r}")
        properties[parts[0].lower()] = parts[1].strip()
    return class_name, properties


def spawned_container_from_object(
    map_id: str,
    object_index: int,
    world_object: Any,
    item_ids: Mm9ItemIdMap,
    scale: float,
) -> SpawnedLootContainerSource | None:
    spawn_value = string_property(world_object, "SpawnObject").strip()
    if not spawn_value:
        return None
    source_description = f"{map_id} object {object_index} SpawnObject"
    class_name, values = parse_spawn_properties(spawn_value, source_description)
    if class_name.lower() != "treasurebag":
        return None

    def int_value(name: str, default: int = 0) -> int:
        raw = values.get(name.lower())
        if raw is None:
            return default
        try:
            return int(float(raw))
        except ValueError as exc:
            raise Mm9ItemSourceError(f"{source_description}: invalid {name} value {raw!r}") from exc

    fixed_items: list[FixedContainerItem] = []
    for slot in range(1, 6):
        raw_id = int_value(f"Item{slot}")
        if raw_id > 0:
            fixed_items.append(FixedContainerItem(
                slot=slot,
                raw_mm9_item_id=raw_id,
                item_id=item_ids.translate(raw_id, f"{source_description}.Item{slot}"),
            ))

    return SpawnedLootContainerSource(
        provenance=build_provenance(map_id, object_index, world_object, scale),
        kind="treasure_bag",
        presentation="mm9_treasure_bag",
        random_treasure_level=int_value("TreasureLevel"),
        treasure_type=int_value("TreasureType0_7"),
        gold=int_value("Gold"),
        gold_only=bool(int_value("GoldOnly")),
        random=bool(int_value("Random")),
        ai_drop=bool(int_value("AIDrop")),
        fixed_items=tuple(fixed_items),
        remove_when_empty=True,
    )


def translate_rule_item(
    raw_item_id: int,
    provenance: SourceProvenance,
    item_ids: Mm9ItemIdMap,
    unresolved: list[UnresolvedItemReference],
    blocks_generation: bool = True,
) -> int:
    item_id = item_ids.try_translate(raw_item_id)
    if item_id is not None:
        return item_id
    unresolved.append(UnresolvedItemReference(
        source_id=provenance.source_id,
        source_object_index=provenance.source_object_index,
        raw_mm9_item_id=raw_item_id,
        reason="raw MM9 item id has no canonical mapping",
        blocks_generation=blocks_generation,
    ))
    return 0


def world_item_from_rule(
    map_id: str,
    object_index: int,
    world_object: Any,
    rule: AuditedPickupRule,
    item_ids: Mm9ItemIdMap,
    scale: float,
    unresolved: list[UnresolvedItemReference],
) -> WorldItemSource:
    provenance = build_provenance(map_id, object_index, world_object, scale)
    translated_grants = tuple(
        ItemGrant(raw_item_id, translate_rule_item(raw_item_id, provenance, item_ids, unresolved))
        for raw_item_id in rule.raw_item_ids
    )
    random_item_pool: list[int] = []
    if rule.random_item_range is not None:
        # A random pool keeps the items that are imported: one left out (MM9's spell books and scrolls, excluded on
        # purpose) is listed but does not block, unless nothing of the pool is left.
        pool_unresolved: list[UnresolvedItemReference] = []
        for raw_item_id in range(rule.random_item_range[0], rule.random_item_range[1] + 1):
            item_id = translate_rule_item(raw_item_id, provenance, item_ids, pool_unresolved,
                                          blocks_generation=False)
            if item_id > 0:
                random_item_pool.append(item_id)
        if not random_item_pool:
            pool_unresolved = [replace(source, blocks_generation=True) for source in pool_unresolved]
        unresolved.extend(pool_unresolved)

    def translate_list(raw_item_ids: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(
            item_id
            for raw_item_id in raw_item_ids
            if (item_id := translate_rule_item(raw_item_id, provenance, item_ids, unresolved)) > 0
        )

    primary_item_id = translated_grants[0].item_id if translated_grants else 0
    return WorldItemSource(
        provenance=provenance,
        kind=rule.kind,
        raw_primary_item_id=rule.raw_item_ids[0] if rule.raw_item_ids else 0,
        item_id=primary_item_id,
        required_qbits=tuple(mm9_qbit(qbit) for qbit in rule.required_qbits),
        forbidden_qbits=tuple(mm9_qbit(qbit) for qbit in rule.forbidden_qbits),
        required_items=translate_list(rule.required_items),
        forbidden_items=translate_list(rule.forbidden_items),
        grant_items=translated_grants,
        take_items=translate_list(rule.take_items),
        set_qbits=tuple(mm9_qbit(qbit) for qbit in rule.set_qbits),
        clear_qbits=tuple(mm9_qbit(qbit) for qbit in rule.clear_qbits),
        random_item_pool=tuple(random_item_pool),
        on_pickup_event=rule.on_pickup_event,
        consume_on_success=True,
    )


def persistent_item_mechanism_from_rule(
    map_id: str,
    object_index: int,
    world_object: Any,
    rule: AuditedPersistentItemMechanismRule,
    item_ids: Mm9ItemIdMap,
    scale: float,
    unresolved: list[UnresolvedItemReference],
) -> PersistentItemMechanismSource:
    provenance = build_provenance(map_id, object_index, world_object, scale)
    if len(rule.model_variants) != len(rule.model_variant_skins):
        raise Mm9ItemSourceError(
            f"{provenance.source_id}: model variant and skin counts do not match")

    def translate(raw_item_id: int) -> int:
        return translate_rule_item(raw_item_id, provenance, item_ids, unresolved)

    # The random pool (GiveRandom.scr, the 1000 Terrors' genie lamp) keeps the imported items: one left out on purpose
    # (MM9's spell books and scrolls) is listed without blocking, unless nothing of the pool is left.
    pool_unresolved: list[UnresolvedItemReference] = []
    random_item_pool = tuple(
        translated
        for raw_item_id in rule.random_raw_items
        if (translated := translate_rule_item(raw_item_id, provenance, item_ids, pool_unresolved,
                                              blocks_generation=False)) > 0
    )
    if rule.random_raw_items and not random_item_pool:
        pool_unresolved = [replace(source, blocks_generation=True) for source in pool_unresolved]
    unresolved.extend(pool_unresolved)

    return PersistentItemMechanismSource(
        provenance=provenance,
        kind=rule.kind,
        handler=rule.handler,
        required_items=tuple(
            translated
            for raw_item_id in rule.required_raw_items
            if (translated := translate(raw_item_id)) > 0
        ),
        grant_items=tuple(
            ItemGrant(raw_item_id, translate(raw_item_id))
            for raw_item_id in rule.grant_raw_items
        ),
        random_item_pool=random_item_pool,
        model_variants=rule.model_variants,
        model_variant_skins=rule.model_variant_skins,
    )


def build_mm9_item_source_manifest(
    map_name: str,
    objects: Iterable[Any],
    item_ids: Mm9ItemIdMap,
    scale: float,
) -> Mm9ItemSourceManifest:
    map_id = canonical_map_id(map_name)
    manifest = Mm9ItemSourceManifest(map_id=map_id)
    container_objects: list[tuple[int, Any]] = []
    object_list = list(objects)

    for (rule_map_id, object_index), rule in sorted(AUDITED_PICKUP_RULES.items()):
        if rule_map_id != map_id or object_index < 0:
            continue
        if object_index >= len(object_list):
            raise Mm9ItemSourceError(f"{map_id}: audited pickup object {object_index} is missing")
        manifest.world_items.append(world_item_from_rule(
            map_id,
            object_index,
            object_list[object_index],
            rule,
            item_ids,
            scale,
            manifest.unresolved_item_references,
        ))

    for (rule_map_id, object_index), (raw_item_id, reason) in sorted(AUDITED_UNSUPPORTED_PICKUPS.items()):
        if rule_map_id != map_id or object_index < 0:
            continue
        if object_index >= len(object_list):
            raise Mm9ItemSourceError(f"{map_id}: audited unsupported pickup object {object_index} is missing")
        provenance = build_provenance(map_id, object_index, object_list[object_index], scale)
        manifest.unresolved_item_references.append(UnresolvedItemReference(
            source_id=provenance.source_id,
            source_object_index=object_index,
            raw_mm9_item_id=raw_item_id,
            reason=reason,
            blocks_generation=False,
        ))

    for (rule_map_id, object_index), rule in sorted(AUDITED_PERSISTENT_ITEM_MECHANISMS.items()):
        if rule_map_id != map_id or object_index < 0:
            continue
        if object_index >= len(object_list):
            raise Mm9ItemSourceError(f"{map_id}: audited persistent item mechanism {object_index} is missing")
        manifest.persistent_item_mechanisms.append(persistent_item_mechanism_from_rule(
            map_id,
            object_index,
            object_list[object_index],
            rule,
            item_ids,
            scale,
            manifest.unresolved_item_references,
        ))

    for object_index, world_object in enumerate(object_list):
        class_name = str(world_object.name).lower()
        if class_name in {"treasurechest", "treasurebag"}:
            container_objects.append((object_index, world_object))
        elif class_name == "bonepile":
            manifest.searchable_loot_props.append(SearchableLootPropSource(
                provenance=build_provenance(map_id, object_index, world_object, scale),
                kind="bone_pile",
                random_treasure_level=integral_property(world_object, "TreasureLevel"),
                loot_rolls=1,
                disease_chance=integral_property(world_object, "DiseaseChance"),
                source_disease_power=integral_property(world_object, "DiseasePower"),
                keep_visual_after_search=True,
            ))
        elif class_name == "barrel":
            barrel_ordinal = len(manifest.barrels)
            provenance = build_provenance(map_id, object_index, world_object, scale)
            manifest.barrels.append(Mm9BarrelSource(
                provenance=replace(provenance, source_id=f"mm9:{map_id}:barrel:{object_index}"),
                interaction_event_id=MM9_MECHANISM_EVENT_ID_BASE + object_index,
                liquid_texture_cog=MM9_BARREL_LIQUID_COG_BASE + barrel_ordinal,
            ))

        if "givetreasure" in property_nodes(world_object):
            manifest.actor_loot_overrides.append(ActorLootOverride(
                source_object_index=object_index,
                procedural_death_loot=boolean_property(world_object, "GiveTreasure"),
            ))

        spawned = spawned_container_from_object(map_id, object_index, world_object, item_ids, scale)
        if spawned is not None:
            manifest.spawned_loot_containers.append(spawned)

    for container_id, (object_index, world_object) in enumerate(container_objects):
        manifest.loot_containers.append(loot_container_from_object(
            map_id,
            object_index,
            world_object,
            container_id,
            item_ids,
            scale,
        ))

    return manifest
