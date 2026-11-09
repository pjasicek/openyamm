/* Table-coordinate proposals only. Native assets and tables are never changed here. */
((root) => {
  "use strict";
  const bodySlots = new Set(["Armor", "Helm", "Belt", "Boots", "Cloak", "Gauntlets"]);
  function describe(layer, item, type, complex, types = {}) {
    if (bodySlots.has(layer.slot)) {
      return { key: `complex:${item.id}:${type}`, table: "complex_item_pictures.txt", item_id: item.id,
        doll_type: type, fields: ["x", "y"], base: complex[item.id]?.[type] || [0, 0],
        scope: "This item and body type; both arm poses share these coordinates." };
    }
    return { key: `fit:${item.id}:${type}:${layer.slot}`, table: null, item_id: item.id,
      doll_type: type, slot: layer.slot, fields: ["screenX", "screenY"], base: [0, 0],
      basis: { equip: [item.equipX, item.equipY], doll: types[type] || null },
      scope: "Only this item, body type and slot. Requires per-item/type placement support when applied to the game." };
  }
  function screenDelta(description, delta, rotated) {
    return delta;
  }
  function tableDelta(description, dx, dy, rotated) {
    return [dx, dy];
  }

  root.PaperdollPlacement = { describe, screenDelta, tableDelta };
})(typeof window === "undefined" ? globalThis : window);
