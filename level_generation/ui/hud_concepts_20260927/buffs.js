"use strict";

// One entry per current PartyBuffId, in enum order. Durations are visual-review examples.
// Sources: game/party/Party.h, SpellIds.h and assets_dev/engine/data_tables/spells.txt.
// Personal buffs remain with their owner; they do not multiply the party strip.
const partyBuffCatalog = [
  { id: "TorchLight", name: "Torch Light", art: "sbf01a", seconds: 300,
    detail: "Illuminates the area around the party." },
  { id: "WizardEye", name: "Wizard Eye", art: "sba01a", seconds: 2280,
    detail: "Minimap awareness follows the spell’s mastery and the existing visibility rules." },
  { id: "FeatherFall", name: "Feather Fall", art: "sba02a", seconds: 2280,
    detail: "Protects the party from falling damage." },
  { id: "DetectLife", name: "Detect Life", art: "sbs01a", seconds: 540,
    detail: "Reveals an inspected creature’s exact hit points." },
  { id: "WaterWalk", name: "Water Walk", art: "sbw05a", seconds: 1020,
    detail: "Allows travel across water. Existing movement and spell-point rules still apply." },
  { id: "Fly", name: "Fly", art: "sba10a", seconds: 1440,
    detail: "Enables outdoor flight using the existing movement controls." },
  { id: "Invisibility", name: "Invisibility", art: "sba08a", seconds: 120,
    detail: "Conceals the party. Existing restrictions and actions that break the effect still apply." },
  { id: "Stoneskin", name: "Stone Skin", art: "sbe05a", seconds: 1500,
    detail: "Increases the party’s armour class." },
  { id: "DayOfGods", name: "Day of the Gods", art: "sbl06a", seconds: 7200,
    detail: "Increases the party’s seven primary statistics." },
  { id: "ProtectionFromMagic", name: "Protection from Magic", art: "sbb09a", seconds: 2700,
    detail: "Protects against debilitating conditions. Remaining protections must also appear in the runtime inspector." },
  { id: "FireResistance", name: "Fire Resistance", art: "sbf03a", seconds: 2280,
    detail: "Increases the party’s resistance to fire." },
  { id: "WaterResistance", name: "Water Resistance", art: "sbw03a", seconds: 2280,
    detail: "Increases the party’s resistance to water magic." },
  { id: "AirResistance", name: "Air Resistance", art: "sba03a", seconds: 2280,
    detail: "Increases the party’s resistance to air magic." },
  { id: "EarthResistance", name: "Earth Resistance", art: "sbe03a", seconds: 2280,
    detail: "Increases the party’s resistance to earth magic." },
  { id: "MindResistance", name: "Mind Resistance", art: "sbm03a", seconds: 2280,
    detail: "Increases the party’s resistance to mind magic." },
  { id: "BodyResistance", name: "Body Resistance", art: "sbb03a", seconds: 2280,
    detail: "Increases the party’s resistance to body magic." },
  { id: "Shield", name: "Shield", art: "sba06a", seconds: 720,
    detail: "Protects the party against incoming ranged attacks." },
  { id: "Heroism", name: "Heroism", art: "sbs07a", seconds: 1500,
    detail: "Increases successful attack damage." },
  { id: "Haste", name: "Haste", art: "sbf05a", seconds: 42,
    detail: "Shortens action recovery. The warm lower edge flags the approaching expiry." },
  { id: "Immolation", name: "Immolation", art: "sbf08a", seconds: 180,
    detail: "Damages nearby enemies over time." },
  { id: "Glamour", name: "Glamour", art: "sbde01a", seconds: 3600,
    detail: "The party-scoped Glamour slot. Character-scoped Glamour stays on its owner’s inspection panel." },
  { id: "Levitate", name: "Levitate", art: "sbv02a", seconds: 1800,
    detail: "The party-scoped Levitate effect. Its component Water Walk and Feather Fall effects have their own slots." },
];

const partyBuffPresets = {
  0: [],
  4: ["Shield", "WizardEye", "Haste", "Fly"],
  // Day of Protection + Hour of Power: 8 + 4 party effects. Bless is character-specific.
  12: ["BodyResistance", "MindResistance", "FireResistance", "WaterResistance", "AirResistance",
    "EarthResistance", "FeatherFall", "WizardEye", "Heroism", "Shield", "Stoneskin", "Haste"],
  // Capacity demonstration of every distinct slot; not a claim that every effect normally coexists.
  22: partyBuffCatalog.map(buff => buff.id),
};
