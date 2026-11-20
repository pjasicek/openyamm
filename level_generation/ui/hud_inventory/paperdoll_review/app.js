(() => {
  "use strict";

  const data = window.PAPERDOLL_REVIEW_DATA;
  if (!data) {
    document.body.textContent = "catalog.js is missing. Run build.py to prepare the viewer.";
    return;
  }

  const repairPass = window.PAPERDOLL_REPAIR_PASS;
  const inventoryFit = window.PAPERDOLL_INVENTORY_FIT;
  const inventoryFits = new Map((inventoryFit?.records || []).map((record) => [record.item_id, record]));
  const sharedImageGroups = new Map((inventoryFit?.groups || []).map((group) => [group.id, group]));
  const sharedTargets = new Map((inventoryFit?.records || []).map((record) =>
    [record.target, sharedImageGroups.get(record.shared_group)]));
  for (const entry of Object.values(data.assets)) {
    const repair = repairPass?.repairs[entry.id];
    if (!repair) continue;
    entry.repair = repair;
    entry.preparedAlternatives ||= [];
    for (const version of [...(repairPass.history?.[entry.id] || []), repair]) {
      entry.preparedAlternatives.push({ attempt: `repair:${version.sha256.slice(0, 12)}`,
        path: `${version.path}?v=${version.sha256.slice(0, 12)}`, sha256: version.sha256,
        issues: version.unresolved, repair: true,
        placementHashes: version.placement_compatible_hashes || [version.old_sha256] });
    }
  }
  // The final ledger import supplies the authoritative accepted file without rebuilding historical catalogs.
  for (const entry of Object.values(data.assets)) {
    const staged = repairPass?.staged[entry.id];
    if (!staged?.canonical_accepted) continue;
    entry.candidate = staged.staged_path;
    entry.candidateHash = staged.reviewed_sha256;
    entry.candidateStatus = "accepted";
  }

  const $ = (id) => document.getElementById(id);
  const items = new Map(data.items.map((item) => [item.id, item]));
  const itemByIcon = new Map(data.items.filter((item) => item.icon).map((item) => [item.icon, item]));
  // Base equipment icons have the same review identity in inventory and on the doll.
  const reviewTargets = [...data.reviewTargets];
  const knownTargets = new Set(reviewTargets.map((entry) => entry.id));
  for (const item of data.items) {
    if (!["Weapon", "Weapon1or2", "Weapon2", "Missile", "Shield", "WeaponW",
      "Gauntlets", "Amulet", "Ring"].includes(item.stat)) continue;
    if (inventoryFits.has(item.id) && inventoryFits.get(item.id).representative_item_id !== item.id) continue;
    const entry = data.assets[item.icon];
    if (!entry || knownTargets.has(entry.id)) continue;
    knownTargets.add(entry.id);
    reviewTargets.push({ id: entry.id, name: entry.name, treatment: entry.treatment,
      active: true, resolverSelected: true, itemId: item.id });
  }
  const targets = new Map(reviewTargets.map((target) => [target.id, target]));
  const targetByName = new Map(reviewTargets.map((target) => [target.name, target]));
  const assetsById = new Map(Object.values(data.assets).map((entry) => [entry.id, entry]));
  const magentaRecords = new Map([...(window.PAPERDOLL_MAGENTA_SCAN?.records || []),
    ...(window.PAPERDOLL_JEWELRY_MAGENTA_SCAN?.records || []),
    ...(repairPass?.magenta_scan?.records || [])]
    .map((record) => [`${record.target}:${record.candidate_hash}`, record]));
  const imageCache = new Map();
  const storageKey = "openyamm-paperdoll-context-review-v1";
  const attemptStorageKey = "openyamm-paperdoll-context-review-attempt-v1";
  const placementStorageKey = "openyamm-paperdoll-placement-v1";
  const hideAcceptedStorageKey = "openyamm-paperdoll-hide-accepted-v1";
  const placementModel = window.PaperdollPlacement;
  const typeLabels = ["Male", "Female", "Minotaur", "Troll", "Dwarf", "Dragon (no equipment)"];
  const twoHandStats = new Set(["Weapon2", "Weapon1or2"]);
  const oneHandStats = new Set(["Weapon", "WeaponW"]);
  const sharedSlots = ["Bow", "Cloak", "Armor", "Helm", "Boots", "Belt"];
  const jewelrySlots = ["Gauntlets", "Amulet", "Ring1", "Ring2", "Ring3", "Ring4", "Ring5", "Ring6"];
  const slotLayout = {
    Bow: "CharacterDollBowSlot", Cloak: "CharacterDollCloakSlot",
    Armor: "CharacterDollArmorSlot", Helm: "CharacterDollHelmetSlot",
    Boots: "CharacterDollBootsSlot", Belt: "CharacterDollBeltSlot",
    MainHand: "CharacterDollRightHandSlot", OffHand: "CharacterDollLeftHandSlot",
  };
  const bodySlots = new Set(["Armor", "Helm", "Belt", "Boots", "Cloak", "Gauntlets"]);
  const defaultOneHand = data.items.find((item) => oneHandStats.has(item.stat) && data.assets[item.icon])?.id || 0;
  const defaultTwoHand = data.items.find((item) => twoHandStats.has(item.stat) && data.assets[item.icon])?.id || 0;
  const defaultShield = data.items.find((item) => item.stat === "Shield" && data.assets[item.icon])?.id || 0;
  const keyboardModes = [
    { key: "F1", control: "oneHand", slot: "MainHand", label: "Main-hand weapon", pose: "one" },
    { key: "F2", control: "twoHand", slot: "MainHand", label: "Two-hand weapon", pose: "two" },
    { key: "F3", control: "OffHand", slot: "OffHand", label: "Shield", pose: "one" },
    { key: "F4", control: "Bow", slot: "Bow", label: "Bow" },
    { key: "F5", control: "Cloak", slot: "Cloak", label: "Cloak" },
    { key: "F6", control: "Armor", slot: "Armor", label: "Armor" },
    { key: "F7", control: "Helm", slot: "Helm", label: "Helm" },
    { key: "F8", control: "Boots", slot: "Boots", label: "Boots" },
    { key: "F9", control: "Belt", slot: "Belt", label: "Belt" },
    ...jewelrySlots.map((slot) => ({ key: slot, control: slot, slot,
      label: slot === "Gauntlets" ? "Gloves" : slot.replace("Ring", "Ring "), jewelry: true })),
  ];
  // Preserve the original storage keys and snapshot their exact values before the first shortcut-enabled load.
  try {
    const backupKey = "openyamm-paperdoll-before-shortcuts-v1";
    const previous = Object.fromEntries([storageKey, attemptStorageKey, placementStorageKey]
      .map((key) => [key, localStorage.getItem(key)]));
    if (!localStorage.getItem(backupKey) && Object.values(previous).some((value) => value !== null)) {
      localStorage.setItem(backupKey, JSON.stringify({ saved_at: new Date().toISOString(), storage: previous }));
    }
  } catch { /* Existing records are never overwritten by the backup operation. */ }
  // Import each immutable feedback round once, preserving newer browser edits by timestamp.
  // Snapshot every old value first. Never seed this round again after Clear/Reset.
  try {
    const marker = `openyamm-paperdoll-stage-import-${repairPass?.id}-v${repairPass?.import_revision}`;
    if (repairPass && !localStorage.getItem(marker)) {
      const before = Object.fromEntries([storageKey, attemptStorageKey, placementStorageKey]
        .map((key) => [key, localStorage.getItem(key)]));
      localStorage.setItem(`${marker}-backup`, JSON.stringify({ saved_at: new Date().toISOString(), storage: before }));
      const attempts = JSON.parse(localStorage.getItem(attemptStorageKey) || "{}");
      for (const [key, defaults] of [[storageKey, repairPass.decisions], [placementStorageKey, repairPass.placements]]) {
        const existing = JSON.parse(localStorage.getItem(key) || "{}");
        for (const [id, record] of Object.entries(defaults)) {
          if (existing[id] && (existing[id].updated_at || "") >= (record.updated_at || "")) continue;
          existing[id] = record;
          if (key === storageKey) {
            if (record.attempt) attempts[id] = record.attempt;
            else delete attempts[id];
          }
        }
        localStorage.setItem(key, JSON.stringify(existing));
      }
      localStorage.setItem(attemptStorageKey, JSON.stringify(attempts));
      localStorage.setItem(marker, "complete");
    }
  } catch { /* Immutable handoff files remain available if browser storage is blocked. */ }
  // An already-open tab imported the prior snapshot before its twelve offset approvals were finalized.
  // Migrate only exact old records at the authorized positions; never recreate Clear or replace newer edits.
  try {
    const patch = window.PAPERDOLL_APPROVAL_SNAPSHOT_SYNC;
    const marker = `openyamm-paperdoll-${patch?.id}`;
    if (patch && !localStorage.getItem(marker)) {
      const decisions = JSON.parse(localStorage.getItem(storageKey) || "{}");
      const placements = JSON.parse(localStorage.getItem(placementStorageKey) || "{}");
      const previous = {};
      for (const [id, change] of Object.entries(patch.records)) {
        const placement = change.after.placement;
        if (JSON.stringify(decisions[id]) !== JSON.stringify(change.before) ||
            JSON.stringify(placements[placement.key]?.delta) !== JSON.stringify(placement.delta)) continue;
        previous[id] = decisions[id];
        decisions[id] = change.after;
      }
      if (Object.keys(previous).length) {
        localStorage.setItem(`${marker}-backup`, JSON.stringify({ saved_at: new Date().toISOString(),
          receipt: patch.receipt, decisions: previous }));
        localStorage.setItem(storageKey, JSON.stringify(decisions));
      }
      localStorage.setItem(marker, "complete");
    }
  } catch { /* The immutable receipt and original browser capture remain available. */ }
  const initial = {
    characterId: data.characters[0].id, background: true, jewelry: false, artMode: "candidate",
    originalDoll: false, pose: "empty", keyboardMode: "F1",
    zoom: 2, spearMastery: "low", oneHand: defaultOneHand, twoHand: defaultTwoHand,
    offHand: 0, shared: {}, jewels: {}, selectedName: "", selectedTarget: "",
    targetScope: "pending", decisionFilter: "all", targetSearch: "", force: null,
    hideAccepted: false,
  };
  const state = { ...initial, decisions: loadDecisions(), attemptChoice: loadAttemptChoices(), placements: loadPlacements() };
  try { state.hideAccepted = localStorage.getItem(hideAcceptedStorageKey) === "true"; }
  catch { /* The toggle also works without persistent browser storage. */ }
  restoreDecisionAttempts(state.decisions);
  // Select new repairs once per content hash, while retaining explicit later selections.
  try {
    const key = "openyamm-paperdoll-repair-selection-20260926";
    const initialized = JSON.parse(localStorage.getItem(key) || "{}");
    for (const entry of Object.values(data.assets)) {
      if (!entry.repair || initialized[entry.id] === entry.repair.sha256) continue;
      const decision = state.decisions[entry.id];
      const newerArtDecision = decision && decision.updated_at > entry.repair.review_baseline_at &&
        decision.candidate_hash !== entry.repair.old_sha256;
      if (!newerArtDecision) state.attemptChoice[entry.id] = `repair:${entry.repair.sha256.slice(0, 12)}`;
      initialized[entry.id] = entry.repair.sha256;
    }
    localStorage.setItem(key, JSON.stringify(initialized));
    saveAttemptChoices();
  } catch { /* Review remains available without persistent selection. */ }
  let renderTicket = 0;
  let inventoryRenderTicket = 0;
  let currentPanels = [];

  function loadPlacements() {
    try { return JSON.parse(localStorage.getItem(placementStorageKey) || "{}"); }
    catch { return {}; }
  }

  function savePlacements() {
    try { localStorage.setItem(placementStorageKey, JSON.stringify(state.placements)); }
    catch { /* Export includes placement proposals when storage is unavailable. */ }
  }

  function placementDescription(entry) {
    return placementModel.describe(entry, item(entry.itemId), person().type, data.complex, data.types);
  }

  function validPlacement(record, description) {
    if (!record || /^(grip|preview):/.test(record.key) || JSON.stringify(record.base) !== JSON.stringify(description.base)) return false;
    const source = assetsById.get(record.reviewed_asset);
    const definition = item(record.item_id);
    if (!definition) return false;
    if (record.key.startsWith("fit:")) {
      const expected = placementModel.describe({ slot: record.slot }, definition, record.doll_type, data.complex, data.types);
      if (record.key !== expected.key || JSON.stringify(record.basis) !== JSON.stringify(expected.basis)) return false;
    }
    const currentBase = record.table === "items.txt" ? [definition.equipX, definition.equipY] :
      record.table === "complex_item_pictures.txt" ? (data.complex[record.item_id]?.[record.doll_type] || [0, 0]) : [0, 0];
    if (JSON.stringify(currentBase) !== JSON.stringify(record.base)) return false;
    return !!source && source.sourceHash === record.source_hash &&
      (candidateFor(source)?.sha256 === record.candidate_hash ||
       candidateFor(source)?.placementHashes?.includes(record.candidate_hash));
  }

  function placementSnapshot(description) {
    const record = state.placements[description.key];
    return { key: description.key, delta: validPlacement(record, description) ? record.delta : [0, 0] };
  }

  function adjustedLayer(entry) {
    if (entry.kind !== "item" || chosenArt(entry.asset)?.kind === "native") return entry;
    const description = placementDescription(entry);
    const record = state.placements[description.key];
    const delta = validPlacement(record, description) ? record.delta : [0, 0];
    const [dx, dy] = placementModel.screenDelta(description, delta, entry.rotated);
    const drawScale = jewelrySlots.includes(entry.slot) ? inventoryFits.get(entry.itemId)?.overlay_scale || 1 : 1;
    return { ...entry, baseX: entry.x, baseY: entry.y, drawScale,
      x: entry.x + dx + entry.width * (1 - drawScale) / 2,
      y: entry.y + dy + entry.height * (1 - drawScale) / 2,
      width: entry.width * drawScale, height: entry.height * drawScale };
  }

  function moveEquipment(entry, dx, dy, reset = false) {
    const description = placementDescription(entry);
    const previous = state.placements[description.key];
    const before = validPlacement(previous, description) ? previous.delta : [0, 0];
    const change = placementModel.tableDelta(description, dx, dy, entry.rotated);
    const delta = reset ? [0, 0] : before.map((value, index) => value + change[index]);
    if (delta.every((value) => value === 0)) delete state.placements[description.key];
    else state.placements[description.key] = { ...description, delta,
      proposed: description.base.map((value, index) => value + delta[index]),
      units: "native_game_pixels", reviewed_asset: entry.asset.id,
      source_hash: entry.asset.sourceHash, candidate_hash: candidateFor(entry.asset)?.sha256,
      character_id: state.characterId, slot: entry.slot, updated_at: new Date().toISOString() };
    savePlacements();
    state.selectedName = entry.name;
    update();
  }

  function loadDecisions() {
    try { return JSON.parse(localStorage.getItem(storageKey) || "{}"); }
    catch { return {}; }
  }

  function loadAttemptChoices() {
    try { return JSON.parse(localStorage.getItem(attemptStorageKey) || "{}"); }
    catch { return {}; }
  }

  function restoreDecisionAttempts(decisions) {
    for (const [targetId, decision] of Object.entries(decisions)) {
      if (decision.attempt && !state.attemptChoice[targetId]) state.attemptChoice[targetId] = decision.attempt;
    }
  }

  function saveAttemptChoices() {
    try { localStorage.setItem(attemptStorageKey, JSON.stringify(state.attemptChoice)); }
    catch { /* Exported decisions also include the selected attempt. */ }
  }

  function saveDecisions() {
    try { localStorage.setItem(storageKey, JSON.stringify(state.decisions)); }
    catch { /* Export remains available if file:// storage is blocked. */ }
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  }

  function roundAway(value) {
    return value < 0 ? -Math.round(-value) : Math.round(value);
  }

  function person() {
    return data.characters.find((entry) => entry.id === state.characterId) || data.characters[0];
  }

  function dollType() {
    return data.types[person().type];
  }

  function asset(name) {
    return data.assets[name?.toLowerCase()] || null;
  }

  function item(id) {
    return items.get(Number(id)) || null;
  }

  function itemLabel(entry) {
    const unusualStat = ["armor", "cloak"].includes(entry.stat) ? ` · ${entry.stat} table row` : "";
    const group = sharedImageGroups.get(inventoryFits.get(entry.id)?.shared_group);
    const aliases = group?.members.filter((id) => id !== entry.id).map((id) => item(id).name) || [];
    return `#${entry.id} ${entry.name || entry.icon} · ${entry.icon}${unusualStat}` +
      (aliases.length ? ` · also ${aliases.join(", ")}` : "");
  }

  function allowed(slot, type) {
    const map = {
      Bow: "bow", Armor: "armor", Helm: "helm", Belt: "belt",
      Boots: "boots", Cloak: "cloak", MainHand: "weapon", OffHand: "weapon",
    };
    return !map[slot] || !!type.can[map[slot]];
  }

  function optionsFor(slot) {
    if (jewelrySlots.includes(slot)) {
      const stat = slot.startsWith("Ring") ? "Ring" : slot;
      return data.items.filter((entry) => entry.stat === stat &&
        inventoryFits.get(entry.id)?.representative_item_id === entry.id);
    }
    switch (slot) {
      case "oneHand": return data.items.filter((entry) => oneHandStats.has(entry.stat));
      case "twoHand": return data.items.filter((entry) => twoHandStats.has(entry.stat));
      case "OffHand": return data.items.filter((entry) => entry.stat === "Shield" ||
        (oneHandStats.has(entry.stat) && ["Sword", "Dagger"].includes(entry.skill)));
      case "Bow": return data.items.filter((entry) => entry.stat === "Missile");
      default: return data.items.filter((entry) => entry.stat === slot ||
        (bodySlots.has(slot) && entry.stat.toLowerCase() === slot.toLowerCase()));
    }
  }

  function makeItemSelect(slot, label, value, container) {
    const wrapper = document.createElement("div");
    wrapper.className = "item-control";
    const caption = document.createElement("label");
    const labelText = document.createElement("span");
    labelText.textContent = label;
    const support = document.createElement("small");
    support.className = "unsupported";
    caption.append(labelText, support);
    const select = document.createElement("select");
    select.dataset.slot = slot;
    const empty = document.createElement("option");
    empty.value = "0";
    empty.textContent = "None";
    select.append(empty);
    for (const entry of optionsFor(slot)) {
      const option = document.createElement("option");
      option.value = String(entry.id);
      option.textContent = itemLabel(entry);
      select.append(option);
    }
    select.value = String(value || 0);
    const picker = document.createElement("div");
    picker.className = "item-picker";
    const previous = document.createElement("button");
    previous.type = "button";
    previous.textContent = "‹";
    previous.title = `Previous ${label}`;
    const next = document.createElement("button");
    next.type = "button";
    next.textContent = "›";
    next.title = `Next ${label}`;
    for (const [button, delta] of [[previous, -1], [next, 1]]) {
      button.addEventListener("click", () => {
        stepItemSelection(select, delta);
      });
    }
    select.addEventListener("change", () => {
      const chosen = Number(select.value);
      if (slot === "oneHand") { state.oneHand = chosen; state.pose = "one"; }
      else if (slot === "twoHand") { state.twoHand = chosen; state.pose = "two"; }
      else if (slot === "OffHand") { state.offHand = chosen; state.pose = "one"; }
      else if (jewelrySlots.includes(slot)) state.jewels[slot] = chosen;
      else state.shared[slot] = chosen;
      state.jewelry = jewelrySlots.includes(slot);
      state.force = null;
      const mode = keyboardModes.find((mode) => mode.control === slot);
      if (mode) state.keyboardMode = mode.key;
      focusKeyboardItem();
      update();
    });
    picker.append(previous, select, next);
    wrapper.append(caption, picker);
    container.append(wrapper);
    return { select, support, previous, next, slot };
  }

  const selectControls = [];
  selectControls.push(makeItemSelect("oneHand", "1H main hand", state.oneHand, $("handControls")));
  selectControls.push(makeItemSelect("twoHand", "2H main hand", state.twoHand, $("handControls")));
  selectControls.push(makeItemSelect("OffHand", "1H off hand", state.offHand, $("handControls")));
  for (const slot of sharedSlots) {
    selectControls.push(makeItemSelect(slot, slot, 0, $("sharedControls")));
  }
  for (const slot of jewelrySlots) {
    selectControls.push(makeItemSelect(slot, slot, 0, $("jewelryControls")));
  }

  for (const entry of data.characters) {
    const option = document.createElement("option");
    option.value = String(entry.id);
    option.textContent = `#${entry.id} ${entry.notes || entry.facePrefix || entry.body} · type ${entry.type}`;
    $("dollSelect").append(option);
  }

  function syncControls() {
    $("typeShortcuts").replaceChildren();
    for (const type of Object.values(data.types)) {
      const representatives = data.characters.filter((entry) => entry.type === type.id && asset(entry.body));
      const representative = representatives.find((entry) => entry.start) || representatives[0];
      if (!representative) continue;
      const button = document.createElement("button");
      button.textContent = typeLabels[type.id] || `Type ${type.id}`;
      button.dataset.type = type.id;
      button.className = person().type === type.id ? "active" : "";
      button.setAttribute("aria-pressed", String(person().type === type.id));
      button.onclick = () => { state.characterId = representative.id; state.force = null; focusKeyboardItem(); update(); };
      $("typeShortcuts").append(button);
    }
    $("dollSelect").value = String(state.characterId);
    $("showBackground").checked = state.background;
    $("showJewelry").checked = state.jewelry;
    $("originalDoll").checked = state.originalDoll;
    $("artMode").value = state.artMode;
    $("poseSelect").value = state.pose;
    $("zoom").value = String(state.zoom);
    $("spearMastery").value = state.spearMastery;
    $("targetScope").value = state.targetScope;
    $("decisionFilter").value = state.decisionFilter;
    $("targetSearch").value = state.targetSearch;
    $("hideAccepted").checked = state.hideAccepted;
    const type = dollType();
    for (const control of selectControls) {
      const slot = control.slot;
      const value = slot === "oneHand" ? state.oneHand : slot === "twoHand" ? state.twoHand :
        slot === "OffHand" ? state.offHand : jewelrySlots.includes(slot) ? state.jewels[slot] : state.shared[slot];
      control.select.value = String(value || 0);
      for (const option of control.select.options) {
        option.hidden = hideAcceptedItem(item(Number(option.value)), slot);
      }
      const supported = ["oneHand", "twoHand"].includes(slot) ? type.can.weapon : allowed(slot, type);
      control.support.textContent = supported ? "" : "unavailable to this doll type";
      control.select.disabled = !supported && !jewelrySlots.includes(slot);
      control.previous.disabled = control.select.disabled;
      control.next.disabled = control.select.disabled;
    }
    const entry = person();
    $("dollMeta").textContent = `Type ${entry.type} · ${entry.notes || entry.facePrefix || "character"} · ` +
      `background ${entry.background || "layout default"}`;
    const portrait = asset(entry.portrait);
    const portraitCandidate = candidateFor(portrait);
    $("portraitReference").innerHTML = portrait ? `
      <figure><img src="${escapeHtml(portrait.native)}" alt="Original ${escapeHtml(entry.portrait)} portrait">
        <figcaption>Assigned portrait · original</figcaption></figure>
      ${portraitCandidate ? `<figure><img src="${escapeHtml(portraitCandidate.path)}"
        alt="2× ${escapeHtml(entry.portrait)} portrait candidate">
        <figcaption>2× portrait · ${portrait.candidateStatus === "accepted" ? "accepted" : "review pending"}</figcaption>
        </figure>` : ""}
      <p class="subtle">${escapeHtml(entry.portrait)} is the face reference for this doll.</p>` :
      `<p class="warning">Assigned portrait ${escapeHtml(entry.portrait)} is missing.</p>`;
    $("stageTitle").textContent = `#${entry.id} ${entry.notes || entry.facePrefix || entry.body}`;
    $("stageNote").textContent = state.originalDoll || state.artMode === "native" ? "Original body and hands at game-table positions; equipment uses the selected Artwork mode."
        : state.jewelry ? "Jewelry panel over the doll, using the game’s slot anchors."
        : "Accepted Real-ESRGAN body and limbs at original game-table coordinates. Equipment follows Artwork mode.";
  }

  function resolvedTexture(itemDefinition, type, hasMain, slot) {
    if (!itemDefinition || !itemDefinition.icon) return "";
    if (!bodySlots.has(slot) || type.id >= 5) return itemDefinition.icon;
    let variant = type.id + 1;
    if (slot === "Cloak" && (type.id === 2 || type.id === 3)) variant = 1;
    const suffix = `v${variant}`;
    const candidates = slot === "Armor"
      ? (hasMain ? [suffix, suffix + "a"] : [suffix + "a", suffix])
      : slot === "Cloak" ? [suffix + "a"] : [suffix];
    for (const candidate of candidates) {
      if (asset(itemDefinition.icon + candidate)) return itemDefinition.icon + candidate;
    }
    return itemDefinition.icon;
  }

  function layer(name, x, y, kind, more = {}) {
    const imageAsset = asset(name);
    const size = imageAsset?.size || [0, 0];
    return { name, x, y, width: more.rotated ? size[1] : size[0],
      height: more.rotated ? size[0] : size[1], kind, asset: imageAsset, ...more };
  }

  function itemLayer(slot, itemDefinition, type, hasMain, pose, origin = { x: 0, y: 0, width: 0, height: 0 }) {
    if (!itemDefinition || !itemDefinition.icon) return null;
    const normalName = resolvedTexture(itemDefinition, type, hasMain, slot);
    const force = state.force && state.force.pose === pose && state.force.slot === slot &&
      state.force.itemId === itemDefinition.id;
    const name = force ? state.force.name : normalName;
    const imageAsset = asset(name);
    const width = imageAsset?.size[0] || 0;
    const height = imageAsset?.size[1] || 0;
    let x = origin.x;
    let y = origin.y;
    let rotated = false;
    if (bodySlots.has(slot)) {
      const point = data.complex[itemDefinition.id]?.[type.id] || [0, 0];
      x += point[0];
      y += point[1];
    } else if (slot === "Bow") {
      x = roundAway(x + type.bowOffsetX - width * 0.5);
      y = roundAway(y + type.bowOffsetY - height * 0.5);
    } else if (slot === "MainHand") {
      const fingers = asset(person().rightFingers);
      const gripX = fingers ? type.rightFingersX + roundAway(fingers.size[0] * 0.5) :
        type.rightClosedX + type.mainHandOffsetX;
      x = roundAway(x + gripX - itemDefinition.equipX);
      y = roundAway(y + type.rightClosedY + type.mainHandOffsetY - itemDefinition.equipY);
    } else if (slot === "OffHand" && itemDefinition.stat === "Shield") {
      x = roundAway(x + type.leftClosedX + type.shieldX - itemDefinition.equipX);
      y = roundAway(y + type.leftClosedY + type.shieldY - itemDefinition.equipY);
    } else if (slot === "OffHand") {
      x = roundAway(x + type.leftClosedX + type.offHandOffsetX + type.shieldX - itemDefinition.equipY);
      y = roundAway(y + type.leftClosedY + type.offHandOffsetY + type.shieldY -
        (width - itemDefinition.equipX));
      rotated = true;
    } else {
      x = roundAway(x + (origin.width - width) * 0.5);
      y = roundAway(y + (origin.height - height) * 0.5);
    }
    return layer(name, x, y, "item", { slot, itemId: itemDefinition.id, rotated,
      forced: (!!force && (normalName !== name || !allowed(slot, type) || state.force.unreachable)) ||
        (bodySlots.has(slot) && itemDefinition.stat !== slot), normalName });
  }

  function poseLayers(pose) {
    const entry = person();
    const type = dollType();
    const hasWeaponAbility = type.can.weapon;
    const main = hasWeaponAbility ? item(pose === "one" ? state.oneHand : pose === "two" ? state.twoHand : 0) : null;
    const off = hasWeaponAbility && pose === "one" ? item(state.offHand) : null;
    const hasMain = !!main;
    const leftHandDisabled = !!main && (main.stat === "Weapon2" ||
      (main.skill.toLowerCase() === "spear" && state.spearMastery !== "master"));
    const offHandWeaponGripAbove = !!off && off.stat !== "Shield";
    const output = [];
    if (state.background) output.push(layer(entry.background || "backdolm", 0, 0, "background"));
    const equipment = {
      Bow: item(state.shared.Bow), Cloak: item(state.shared.Cloak),
      Armor: item(state.shared.Armor), Helm: item(state.shared.Helm),
      Boots: item(state.shared.Boots), Belt: item(state.shared.Belt),
      MainHand: main, OffHand: off,
    };
    const layoutToSlot = Object.fromEntries(Object.entries(slotLayout).map(([slot, id]) => [id, slot]));
    for (const layoutEntry of data.layout.layers) {
      const id = layoutEntry.id;
      const slot = layoutToSlot[id];
      if (slot) {
        const selected = equipment[slot];
        const forced = state.force?.pose === pose && state.force?.slot === slot;
        if (selected && (allowed(slot, type) || forced)) {
          const result = itemLayer(slot, selected, type, hasMain, pose);
          if (result) output.push(result);
        }
      } else if (id === "CharacterDollBody") {
        if (entry.body) output.push(layer(entry.body, entry.bodyX, entry.bodyY, "body"));
      } else if (id === "CharacterDollRightHand") {
        const name = hasMain ? entry.rightHold : entry.rightOpen;
        if (name) output.push(layer(name, hasMain ? type.rightClosedX : type.rightOpenX,
          hasMain ? type.rightClosedY : type.rightOpenY, "hand"));
      } else if (id === "CharacterDollLeftHand") {
        if (off?.stat === "Shield" && entry.leftClosed) {
          output.push(layer(entry.leftClosed, type.leftClosedX, type.leftClosedY, "hand"));
        } else if (!off && !leftHandDisabled && entry.leftOpen) {
          output.push(layer(entry.leftOpen, type.leftFingersX, type.leftFingersY, "hand"));
        }
      } else if (id === "CharacterDollRightHandFingers") {
        if (main && entry.rightFingers) {
          output.push(layer(entry.rightFingers, type.rightFingersX, type.rightFingersY, "hand"));
        }
        if ((leftHandDisabled || offHandWeaponGripAbove) && entry.leftHold) {
          output.push(layer(entry.leftHold, type.leftOpenX, type.leftOpenY, "hand"));
        }
      }
    }
    return output;
  }

  function jewelryLayers() {
    const entry = person();
    const type = dollType();
    const output = poseLayers("empty");
    const overlay = data.layout.jewelry;
    output.push(layer(overlay.background, data.layout.width - overlay.width, 0, "jewelry background"));
    for (const slot of jewelrySlots) {
      const chosen = item(state.jewels[slot]);
      if (!chosen) continue;
      const box = overlay[`CharacterDoll${slot}Slot`];
      if (!box) continue;
      const placed = itemLayer(slot, chosen, type, false, "jewelry", box);
      if (placed) output.push(placed);
    }
    return output;
  }

  function imageFor(url) {
    if (!url) return Promise.resolve(null);
    if (!imageCache.has(url)) {
      imageCache.set(url, new Promise((resolve) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => resolve(null);
        image.src = url;
      }));
    }
    return imageCache.get(url);
  }

  function candidateFor(entry) {
    if (!entry?.candidate) return null;
    const alternatives = entry.preparedAlternatives || [];
    return alternatives.find((option) => option.attempt === state.attemptChoice[entry.id]) ||
      alternatives.find((option) => option.path === entry.candidate) ||
      { path: entry.candidate, sha256: entry.candidateHash };
  }

  function magentaScan(entry) {
    if (!entry) return null;
    const scan = magentaRecords.get(`${entry.id}:${candidateFor(entry)?.sha256}`);
    return scan?.source_hash === entry.sourceHash ? scan : null;
  }

  function magentaWarning(entry) {
    const scan = magentaScan(entry);
    if (!scan || scan.status === "no_spill_detected") return "";
    return scan.status === "purple_material_check" ?
      `AUTO CHECK: purple edge material (${scan.metrics.edge_pixels} pixels); may be intentional.` :
      `AUTO FLAG: suspected magenta spill (${scan.metrics.edge_pixels} edge pixels, ${scan.metrics.key_pixels} matte-colored pixels).`;
  }

  function chosenArt(entry) {
    if (!entry) return null;
    if (state.originalDoll && entry.treatment === "paperdoll_parts") {
      return { url: entry.native, kind: "native" };
    }
    const approved = ["accepted", "hud_approved"].includes(entry.candidateStatus);
    if (state.artMode === "accepted" && approved && entry.candidate) {
      return { url: entry.candidate, kind: "accepted" };
    }
    const candidate = state.artMode === "candidate" ? candidateFor(entry) : null;
    return candidate ? { url: candidate.path,
      kind: approved && candidate.sha256 === entry.candidateHash ? "accepted" : "candidate" } :
      { url: entry.native, kind: "native" };
  }

  async function renderStage() {
    const ticket = ++renderTicket;
    const poses = state.jewelry ? [{ id: "jewelry", title: "Jewelry overlay",
      note: "Backhand overlay, gauntlets, amulet, and six ring anchors." }] : [
      { id: "empty", title: "Empty hands", note: "Open hands · armor uses alternate pose when available." },
      { id: "one", title: "One-hand weapon", note: "Main-hand grip · optional shield or off-hand weapon." },
      { id: "two", title: "Two-hand weapon", note: "Main-hand item · left-hand support pose." },
    ].filter((pose) => pose.id === state.pose);
    const panels = poses.flatMap((pose) => {
      const layers = pose.id === "jewelry" ? jewelryLayers() : poseLayers(pose.id);
      return [
        { ...pose, original: true, title: "Original · enlarged 2×", layers,
          note: `${pose.title} · native doll and items, unchanged table positions.` },
        { ...pose, original: false, title: "Restored · 2× review", layers: layers.map(adjustedLayer),
          note: `${pose.title} · selected artwork and saved placement adjustments.` },
      ];
    });
    const panelArt = (panel, entry) => panel.original ? { url: entry.asset?.native, kind: "native" } : chosenArt(entry.asset);
    if (panels.some((panel) => panel.layers.some((entry) => entry.forced))) {
      $("stageNote").textContent = "Forced preview: this selected file is not drawn by the current item resolver for this doll and pose.";
    }
    const allUrls = [...new Set(panels.flatMap((panel) => panel.layers.map((entry) => panelArt(panel, entry)?.url).filter(Boolean)))];
    const images = new Map(await Promise.all(allUrls.map(async (url) => [url, await imageFor(url)])));
    if (ticket !== renderTicket) return;
    currentPanels = panels.filter((panel) => !panel.original);
    $("poseGrid").replaceChildren();
    const missing = new Set();
    for (const panel of panels) {
      const card = document.createElement("article");
      card.dataset.view = panel.original ? "original" : "restored";
      card.className = "pose-card" + (panel.layers.some((entry) => entry.forced) ? " forced" : "");
      const heading = document.createElement("h3");
      heading.textContent = panel.title;
      const note = document.createElement("p");
      note.className = "subtle";
      note.textContent = panel.note;
      const frame = document.createElement("div");
      frame.className = "canvas-frame";
      const canvas = document.createElement("canvas");
      canvas.width = data.layout.width * 2;
      canvas.height = data.layout.height * 2;
      canvas.style.width = `${data.layout.width * state.zoom}px`;
      canvas.style.height = `${data.layout.height * state.zoom}px`;
      canvas.setAttribute("aria-label", `${panel.title} for character ${state.characterId}`);
      const context = canvas.getContext("2d", { alpha: true });
      context.imageSmoothingEnabled = false;
      let acceptedCount = 0;
      let stagedCount = 0;
      let candidateCount = 0;
      let nativeCount = 0;
      const nativeNames = new Set();
      for (const entry of panel.layers) {
        const url = panelArt(panel, entry)?.url;
        const image = images.get(url);
        if (!entry.asset || !image) {
          missing.add(entry.name || "unnamed asset");
          continue;
        }
        if (panelArt(panel, entry)?.kind === "accepted") acceptedCount++;
        else if (panelArt(panel, entry)?.kind === "candidate") {
          if (acceptedForReview(entry.asset)) stagedCount++;
          else candidateCount++;
        }
        else {
          nativeCount++;
          nativeNames.add(entry.name);
        }
        context.save();
        context.imageSmoothingEnabled = !panel.original && (entry.drawScale || 1) < 1;
        if (entry.rotated) {
          context.translate(entry.x * 2, (entry.y + entry.asset.size[0]) * 2);
          context.rotate(-Math.PI / 2);
          context.drawImage(image, 0, 0, entry.asset.size[0] * 2, entry.asset.size[1] * 2);
        } else {
          context.drawImage(image, entry.x * 2, entry.y * 2,
            entry.width * 2, entry.height * 2);
        }
        context.restore();
      }
      frame.append(canvas);
      const summary = document.createElement("div");
      summary.className = "pose-summary";
      summary.textContent = `${acceptedCount} canonical 2× · ${stagedCount} staged 2× · ${candidateCount} pending 2× · ${nativeCount} native 1× layers` +
        (nativeNames.size ? ` (${[...nativeNames].join(", ")})` : "") +
        (card.classList.contains("forced") ? " · forced asset preview" : "");
      card.append(heading, note, frame, summary);
      $("poseGrid").append(card);
    }
    $("missingAssets").hidden = missing.size === 0;
    $("missingAssets").textContent = missing.size ? `Missing table asset or image: ${[...missing].join(", ")}` : "";
    renderLayerList();
    renderInspector();
    renderEquipmentReview();
    renderKeyboardStatus();
    renderInventoryPreview();
  }

  async function renderInventoryPreview() {
    const ticket = ++inventoryRenderTicket;
    const container = $("inventoryPreview");
    container.replaceChildren();
    container.hidden = !state.jewelry;
    const entry = keyboardItem();
    const fit = entry && inventoryFits.get(entry.itemId);
    if (!fit || fit.source_hash !== entry.asset?.sourceHash) return;
    const art = chosenArt(entry.asset);
    const image = await imageFor(art.url);
    if (ticket !== inventoryRenderTicket || !image) return;
    const [columns, rows] = fit.cells;
    const [width, height] = entry.asset.size;
    const cell = inventoryFit.cell_size * 2;
    const scale = Math.min(1, columns * cell / (width * 2), rows * cell / (height * 2));
    const drawWidth = width * 2 * scale;
    const drawHeight = height * 2 * scale;
    const canvas = document.createElement("canvas");
    canvas.width = columns * cell + 24;
    canvas.height = rows * cell + 24;
    canvas.dataset.itemId = entry.itemId;
    canvas.dataset.cells = fit.cells.join("x");
    canvas.dataset.drawSize = JSON.stringify([drawWidth, drawHeight]);
    canvas.dataset.artUrl = art.url;
    canvas.setAttribute("aria-label", `${item(entry.itemId).name}: ${columns} by ${rows} inventory cells at 2×`);
    const context = canvas.getContext("2d");
    context.fillStyle = "#263637";
    context.fillRect(12, 12, columns * cell, rows * cell);
    context.imageSmoothingEnabled = art.kind !== "native";
    context.drawImage(image, 12 + (columns * cell - drawWidth) / 2,
      12 + (rows * cell - drawHeight) / 2, drawWidth, drawHeight);
    context.strokeStyle = "#98dabf";
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < columns; x++) context.strokeRect(12.5 + x * cell, 12.5 + y * cell, cell - 1, cell - 1);
    }
    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `Inventory fit · ${columns}×${rows} · ${columns * rows} cell${rows * columns === 1 ? "" : "s"}`;
    const detail = document.createElement("p");
    detail.className = "subtle";
    detail.textContent = `${item(entry.itemId).name} · shown at 2× · ${Math.round(scale * 100)}% inventory drawing size. ` +
      "Staged inventory sizing; paperdoll artwork and offsets are unchanged.";
    text.append(title, detail);
    const group = sharedImageGroups.get(fit.shared_group);
    if (group?.members.length > 1) {
      const aliases = document.createElement("p");
      aliases.className = "subtle";
      aliases.textContent = "One image for inventory and jewelry: " +
        group.members.map((id) => `${item(id).name} (#${id})`).join(" · ");
      text.append(aliases);
      for (const id of group.members.filter((id) => id !== group.representative_item_id)) {
        const member = inventoryFits.get(id);
        const previous = state.decisions[member.target];
        if (!previous?.note) continue;
        const note = document.createElement("p");
        note.className = "subtle";
        note.textContent = `Saved alias note — ${member.name}: ${previous.note}`;
        text.append(note);
      }
    }
    if (fit.current_cells.join() !== fit.cells.join()) {
      const change = document.createElement("p");
      change.className = "subtle";
      change.textContent = `Current game footprint: ${fit.current_cells.join("×")}; staged footprint: ${fit.cells.join("×")}.`;
      text.append(change);
    }
    container.append(canvas, text);
  }

  function renderLayerList() {
    $("layerList").replaceChildren();
    for (const panel of currentPanels) {
      for (const entry of panel.layers) {
        if (!entry.name) continue;
        const button = document.createElement("button");
        button.type = "button";
        const displayedArt = chosenArt(entry.asset);
        const artKind = displayedArt?.kind;
        const geometryFlag = artKind === "candidate" && !candidateFor(entry.asset)?.repair &&
          (entry.asset?.candidateFlag === "geometry_flag" || entry.asset?.candidateFlag?.includes("registration_guard_flag"));
        button.className = "layer-chip " + (artKind === "accepted" || artKind === "candidate" ? "candidate" :
          artKind === "native" ? "native" : "missing") +
          (state.selectedName === entry.name ? " active" : "") +
          (geometryFlag ? " warning-border" : "");
        button.textContent = `${panel.title}: ${entry.name} · ${entry.x},${entry.y} · ` +
          (artKind === "accepted" ? (entry.asset.acceptanceMethod === "user_accepted_native_realesrgan" ? "accepted ESRGAN 2×" : "accepted 2×") :
            artKind === "candidate" ? (acceptedForReview(entry.asset) ? "staged accepted 2×" : "pending 2×") : "native 1×") +
          (geometryFlag ? " ⚠" : "");
        button.dataset.artUrl = displayedArt?.url || "";
        button.title = `${entry.kind}${entry.slot ? ` · ${entry.slot}` : ""} · ${panel.title}` +
          (artKind === "candidate" && !candidateFor(entry.asset)?.repair && entry.asset?.candidateFlag ? ` · ${entry.asset.candidateFlag}` : "") +
          (displayedArt ? ` · ${displayedArt.url}` : "");
        button.addEventListener("click", () => selectName(entry.name, entry.slot));
        $("layerList").append(button);
      }
    }
  }

  function decisionFor(entry) {
    const current = state.decisions[entry.id];
    if (!current) return null;
    const placement = current.placement;
    const placementRecord = placement && state.placements[placement.key];
    const currentDelta = placementRecord ? (validPlacement(placementRecord, placementRecord) ? placementRecord.delta : null) : [0, 0];
    const samePlacement = !placement || (!/^(grip|preview):/.test(placement.key) &&
      JSON.stringify(placement.delta) === JSON.stringify(currentDelta));
    return current.source_hash === entry.sourceHash && current.candidate_hash === (candidateFor(entry)?.sha256 || null) && samePlacement
      ? current : { ...current, stale: true };
  }

  function acceptedForReview(entry) {
    if (!entry) return false;
    const decision = decisionFor(entry);
    if (decision) return decision.decision === "approve" && !decision.stale;
    // Staged decisions are already imported into state. Do not resurrect them after Clear.
    return ["accepted", "hud_approved"].includes(entry.candidateStatus) &&
      candidateFor(entry)?.sha256 === entry.candidateHash;
  }

  function hideAcceptedItem(definition, controlSlot) {
    if (!state.hideAccepted || !definition) return false;
    const slot = ["oneHand", "twoHand"].includes(controlSlot) ? "MainHand" : controlSlot;
    const main = dollType().can.weapon && item(state.pose === "one" ? state.oneHand :
      state.pose === "two" ? state.twoHand : 0);
    return acceptedForReview(asset(resolvedTexture(definition, dollType(), !!main, slot)));
  }

  function stepItemSelection(select, delta, keyboard = false) {
    const options = [...select.options];
    for (let step = 1; step <= options.length; step++) {
      const index = (select.selectedIndex + step * delta + options.length) % options.length;
      const definition = item(Number(options[index].value));
      if (keyboard && (!definition || (keyboardMode().key === "F3" && definition.stat !== "Shield"))) continue;
      if (hideAcceptedItem(definition, select.dataset.slot)) continue;
      select.selectedIndex = index;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }
    return false;
  }

  function chooseDecision(value, name = state.selectedName, placedLayer = null, refresh = true) {
    const selected = asset(name);
    if (!selected) return;
    const candidate = candidateFor(selected);
    if (value === "approve" && (!candidate || chosenArt(selected)?.kind === "native")) return;
    const visible = placedLayer || currentPanels.flatMap((panel) => panel.layers)
      .find((entry) => entry.name === selected.name && entry.kind === "item");
    if (value === "clear") delete state.decisions[selected.id];
    else state.decisions[selected.id] = {
      target: selected.id, decision: value,
      note: (name === state.selectedName ? $("reviewNote")?.value : undefined) ?? state.decisions[selected.id]?.note ?? "", source_hash: selected.sourceHash,
      candidate_hash: candidate?.sha256 || null, attempt: candidate?.attempt || null,
      character_id: state.characterId,
      doll_type: person().type, asset_name: selected.name,
      placement: visible ? placementSnapshot(placementDescription(visible)) : null,
      forced_preview: state.force?.name === selected.name,
      updated_at: new Date().toISOString(),
    };
    saveDecisions();
    if (refresh) {
      syncControls();
      renderInspector();
      renderQueue();
      renderProgress();
      renderEquipmentReview();
    }
  }

  function saveReviewNote(selected, value, placedLayer = null) {
    // Typing on an automatic finding records the user's own flag without replacing its input node.
    if (!state.decisions[selected.id]) chooseDecision("flag", selected.name, placedLayer, false);
    const current = state.decisions[selected.id];
    if (!current) return;
    current.note = value;
    current.updated_at = new Date().toISOString();
    saveDecisions();
    for (const field of document.querySelectorAll("textarea[data-review-target]")) {
      if (field.dataset.reviewTarget === selected.id && field !== document.activeElement) field.value = value;
    }
    for (const row of document.querySelectorAll(".equipment-row")) {
      if (row.dataset.asset !== selected.name) continue;
      if (!decisionFor(selected)?.stale && current.decision === "flag") {
        row.querySelector(".decision-status").textContent = "Flagged here · note saved";
        row.querySelector('[data-decision="flag"]').classList.add("flagged");
      }
    }
    renderQueue();
    renderProgress();
  }

  function renderEquipmentReview() {
    const container = $("equipmentReview");
    container.replaceChildren();
    const layers = currentPanels.flatMap((panel) => panel.layers).filter((entry) => entry.kind === "item");
    const slots = state.jewelry ? jewelrySlots : ["MainHand", "OffHand", "Helm", "Armor", "Belt", "Boots", "Cloak", "Bow"];
    for (const slot of slots) {
      const entry = layers.find((layer) => layer.slot === slot);
      const row = document.createElement("article");
      row.className = "equipment-row" + (entry?.name === state.selectedName ? " active" : "");
      row.dataset.slot = slot;
      const title = document.createElement("h3");
      title.textContent = slot === "MainHand" ? "Main hand" : slot === "OffHand" ? "Off hand" : slot;
      row.append(title);
      if (!entry) {
        const empty = document.createElement("p");
        empty.className = "empty-slot";
        empty.textContent = allowed(slot, dollType()) ? "Not equipped in this pose" : "Unavailable for this body type";
        row.append(empty);
        container.append(row);
        continue;
      }
      row.dataset.asset = entry.name;
      row.dataset.x = entry.x;
      row.dataset.y = entry.y;
      row.dataset.width = entry.width;
      row.dataset.height = entry.height;
      row.dataset.drawScale = entry.drawScale || 1;
      const definition = item(entry.itemId);
      const description = placementDescription(entry);
      const candidate = candidateFor(entry.asset);
      const decision = decisionFor(entry.asset);
      const displayed = chosenArt(entry.asset);
      const canReview = candidate && displayed?.kind !== "native";
      row.dataset.artUrl = displayed?.url || "";
      const file = document.createElement("button");
      file.className = "asset-name";
      file.textContent = `${definition.name} · ${entry.name}`;
      file.onclick = () => { selectName(entry.name, slot); renderEquipmentReview(); };
      row.append(file);
      const scope = document.createElement("p");
      scope.className = "subtle";
      scope.textContent = bodySlots.has(slot) ? `Accept only ${entry.name}. Other body/pose files stay unchanged.` :
        "Shared inventory + equipped image across all dolls.";

      const status = document.createElement("p");
      status.className = "subtle decision-status";
      status.textContent = decision?.stale ? "Changed since decision — review again" :
        decision?.decision === "approve" ? (repairPass?.staged[entry.asset.id]?.reviewed_sha256 === candidate?.sha256 ?
          repairPass.staged[entry.asset.id].canonical_accepted ? "Accepted in icon ledger · staged for runtime" :
            "Staged accepted · original review preserved" : "Accepted here · local decision") :
        decision?.decision === "flag" ? "Flagged here" :
        ["accepted", "hud_approved"].includes(entry.asset.candidateStatus) ? "Canonical accepted" : "Awaiting acceptance";
      if (candidate?.repair && !acceptedForReview(entry.asset)) status.textContent = "Repaired candidate · needs re-review";
      if (!canReview) status.textContent += " · native shown; choose candidate artwork to accept/move";
      row.append(status);
      if (magentaWarning(entry.asset)) {
        const warning = document.createElement("p");
        warning.className = "warning magenta-warning";
        warning.textContent = magentaWarning(entry.asset);
        row.append(warning);
      }
      const actions = document.createElement("div");
      actions.className = "row-buttons";
      for (const [label, value] of [["Accept", "approve"], ["Flag", "flag"], ["Clear", "clear"]]) {
        const button = document.createElement("button");
        button.textContent = label;
        button.dataset.decision = value;
        button.disabled = value === "approve" && !canReview;
        if (decision?.decision === value && !decision.stale) button.className = value === "flag" ? "flagged" : "chosen";
        button.onclick = () => {
          chooseDecision(value, entry.name, entry);
          if (value === "flag") {
            const currentRow = [...document.querySelectorAll(".equipment-row")].find((row) => row.dataset.slot === slot);
            currentRow?.querySelector("textarea")?.focus({ preventScroll: true });
          }
        };
        actions.append(button);
      }
      const movement = document.createElement("div");
      movement.className = "row-buttons";
      for (const [label, dx, dy, reset] of [["↑", 0, -1], ["↓", 0, 1], ["←", -1, 0], ["→", 1, 0], ["Reset", 0, 0, true]]) {
        const button = document.createElement("button");
        button.textContent = label;
        button.dataset.move = reset ? "reset" : `${dx},${dy}`;
        button.title = reset ? "Reset this table adjustment" : `Move ${slot} ${dx}, ${dy} game pixels`;
        button.setAttribute("aria-label", button.title);
        button.disabled = !canReview;
        button.onclick = () => moveEquipment(entry, dx, dy, reset);
        movement.append(button);
      }
      const placement = document.createElement("p");
      placement.className = "subtle placement-readout";
      const record = state.placements[description.key];
      const delta = placementSnapshot(description).delta;
      const [dx, dy] = placementModel.screenDelta(description, delta, entry.rotated);
      placement.textContent = `Shift ${dx >= 0 ? "+" : ""}${dx}, ${dy >= 0 ? "+" : ""}${dy} · ` +
        (description.table ? `${description.table}: ${description.base.join(", ")} → ${description.base.map((v, i) => v + delta[i]).join(", ")}` : "Body-type / slot adjustment; later runtime support needed");
      const sharing = document.createElement("p");
      sharing.className = "subtle";
      sharing.textContent = description.scope;
      const toolbar = document.createElement("div");
      toolbar.className = "equipment-toolbar";
      toolbar.append(actions, movement);
      const details = document.createElement("details");
      details.className = "placement-details";
      const summary = document.createElement("summary");
      summary.className = "subtle";
      summary.textContent = `Placement ${dx >= 0 ? "+" : ""}${dx}, ${dy >= 0 ? "+" : ""}${dy} · scope / table details`;
      details.append(summary, placement, scope, sharing);
      row.append(toolbar, details);
      if (decision?.decision === "flag" || decision?.note || magentaWarning(entry.asset)) {
        const label = document.createElement("label");
        label.className = "equipment-note subtle";
        label.textContent = "Notes — what needs fixing? (saved automatically)";
        const note = document.createElement("textarea");
        note.dataset.reviewTarget = entry.asset.id;
        note.value = decision?.note || "";
        note.rows = 2;
        note.placeholder = "E.g. magenta fringe on blade, cropped tip, wrong shape…";
        note.addEventListener("input", () => saveReviewNote(entry.asset, note.value, entry));
        label.append(note);
        row.append(label);
      }
      if (entry.forced || candidate?.issues?.length || (!candidate?.repair && entry.asset.candidateFlag) || (record && !validPlacement(record, description))) {
        const warning = document.createElement("p");
        warning.className = "subtle warning";
        warning.textContent = record && !validPlacement(record, description) ? "Saved placement is stale and is not applied. Recheck artwork/table changes." :
          entry.forced ? "Forced variant: current game rules do not normally select this image." :
          "⚠ Extraction / fitting findings — inspect image details.";
        row.append(warning);
      }
      container.append(row);
    }
    const legacy = Object.keys(state.placements).filter((key) => /^(grip|preview):/.test(key)).length;
    $("placementSummary").textContent = `${Object.keys(state.placements).length - legacy} placement proposals · runtime tables unchanged` +
      (legacy ? ` · ${legacy} old global proposals retained for reference only; not applied. Recheck the affected items by body type.` : "");
  }

  function renderInspector() {
    const selected = asset(state.selectedName);
    if (!selected) {
      $("selectedInspector").innerHTML = "<h2>Selected asset</h2><p class='subtle'>Choose a target or visible layer.</p>";
      return;
    }
    const review = decisionFor(selected);
    const candidate = candidateFor(selected);
    const displayedArt = chosenArt(selected);
    const use = currentPanels.flatMap((panel) => panel.layers
      .filter((entry) => entry.name === selected.name)
      .map((entry) => `${panel.title}: (${entry.x}, ${entry.y}), ${entry.width}×${entry.height}`));
    const forcedUse = currentPanels.flatMap((panel) => panel.layers.filter((entry) =>
      entry.name === selected.name && entry.forced));
    const headOnly = person().head === selected.name && use.length === 0;
    const reviewTarget = targetByName.get(selected.name);
    const status = review?.decision === "approve" && !review.stale ?
      (repairPass?.staged[selected.id]?.reviewed_sha256 === candidate?.sha256 ?
        "Staged accepted · approved image and placement preserved; ledger unchanged" : "Accepted here · saved local decision") :
      selected.acceptanceMethod === "user_accepted_native_realesrgan" ? "Accepted Real-ESRGAN · user decision, 2026-09-24" :
      selected.candidateStatus === "accepted" ? "Canonical accepted" :
      selected.candidateStatus === "hud_approved" ? "HUD review approved" :
      selected.candidateStatus === "raw_prepared" ? "Prepared 2× raw return; visual review pending" :
      selected.candidateStatus === "new_prepared" ? "New 2× return; visual review pending" :
      selected.candidateStatus === "border_repaired" ? "Prepared 2× border repair; visual review pending" :
      selected.candidate ? "Exact-2× candidate; visual review pending" :
      selected.attempts ? `Native 1× source enlarged on stage; ${selected.attempts} retained raw attempt(s)` :
      "Native 1× source enlarged on stage; no 2× candidate";
    const alternatives = selected.preparedAlternatives || [];
    $("selectedInspector").innerHTML = `
      <h2>${escapeHtml(selected.name)}</h2>
      ${candidate?.repair && !acceptedForReview(selected) ? `<p class="warning">Repaired candidate · ${selected.repair.previously_approved ? "previous approved version preserved" : "review the corrected image"}.
        Saved offsets carried over; check the fit again.</p>` : ""}
      ${repairPass?.held_armor_bases?.[selected.id] ? `<p class="subtle">Derived from the
        <a href="${escapeHtml(repairPass.held_armor_bases[selected.id].base_path)}" target="_blank">accepted empty-hand armor</a>.
        ${repairPass.held_armor_bases[selected.id].method === "exact_approved_base_copy" ? "Both poses use identical artwork." :
          "Only the weapon arm region changes; the rest of the image is identical."}</p>` : ""}
      ${repairPass?.staged[selected.id]?.staged_path ? `<p class="subtle"><a href="${escapeHtml(repairPass.staged[selected.id].staged_path)}" target="_blank">Original staged approval</a> · not committed to the ledger</p>` : ""}
      <p class="${candidate ? "good" : "warning"}">${escapeHtml(status)}</p>
      ${alternatives.length ? `<label class="subtle" for="candidateAttempt">Raw return (${alternatives.length} available)</label>
        <select id="candidateAttempt">${alternatives.map((option) => `<option value="${escapeHtml(option.attempt)}"
          ${option.attempt === candidate?.attempt ? "selected" : ""}>${escapeHtml(option.attempt.slice(0, 8))} ·
          ${option.issues.length ? escapeHtml(option.issues.join(", ")) : "no technical flags"}</option>`).join("")}</select>` : ""}
      <div class="preview-pair">
        <figure><img src="${selected.native}" alt="Original ${escapeHtml(selected.name)}"><figcaption>Native original</figcaption></figure>
        ${candidate ? `<figure><img class="restored-preview" src="${candidate.path}" alt="2× artwork ${escapeHtml(selected.name)}"><figcaption>${acceptedForReview(selected) ? "Accepted 2×" : "2× candidate"}</figcaption></figure>` : ""}
      </div>
      ${magentaWarning(selected) ? `<p class="warning magenta-warning">${escapeHtml(magentaWarning(selected))}</p>` : ""}
      <dl class="metadata">
        <dt>Family</dt><dd>${escapeHtml(selected.treatment)}</dd>
        <dt>Native canvas</dt><dd>${selected.size[0]}×${selected.size[1]}</dd>
        <dt>Placement</dt><dd>${escapeHtml(use.join(" · ") || "Not visible in the current pose")}</dd>
        <dt>Artwork mode</dt><dd>${escapeHtml(displayedArt?.kind || "missing")} ·
          <a href="${escapeHtml(displayedArt?.url || "#")}" target="_blank" rel="noopener">${escapeHtml(displayedArt?.url || "missing")}</a></dd>
        ${forcedUse.length ? `<dt>Game selection</dt><dd class="warning">Forced asset preview. The resolver may choose ${escapeHtml(forcedUse[0].normalName)}, the doll may lack this slot, or the item's table stat may prevent equipping.</dd>` : ""}
        ${headOnly ? "<dt>Head field</dt><dd class='warning'>Listed in character_data.txt, but the current paperdoll renderer does not composite this field.</dd>" : ""}
        <dt>Source</dt><dd>${escapeHtml(selected.source)}</dd>
        <dt>Magenta scan</dt><dd>${escapeHtml(magentaScan(selected)?.status || "Not scanned for this image/hash")}
          · <a href="${escapeHtml(magentaScan(selected)?.report || "magenta_scan/report.json")}" target="_blank" rel="noopener">Scan report</a></dd>
        <dt>Candidate audit</dt><dd>${escapeHtml(candidate?.issues?.join(", ") || (!candidate?.repair && selected.candidateFlag) || "—")}</dd>
        ${candidate?.raw ? `<dt>Return source</dt><dd><a href="${candidate.raw}" target="_blank" rel="noopener">Open source image</a><br>
          Crop ${escapeHtml(candidate.rawRect.join(", "))} · sampling ${escapeHtml(candidate.sampling.join("×"))} pixels/native pixel ·
          ${escapeHtml(candidate.matte)}${candidate.reuseOf ? ` · reuse preview of ${escapeHtml(candidate.reuseOf)}` : ""}</dd>` : ""}
        <dt>Scope</dt><dd>${selected.active ? "Current active target" : "Outside current active scope"}</dd>
        ${reviewTarget ? `<dt>Resolver</dt><dd class="${reviewTarget.resolverSelected ? "good" : "warning"}">${reviewTarget.resolverSelected ? "Selected in a compatible doll/pose" : reviewTarget.treatment === "paperdoll_parts" ? "Head metadata; not composited" : "Manual preview only under current rules"}</dd>` : ""}
      </dl>
      ${review?.stale ? "<p class='danger'>Saved decision is stale: artwork or placement changed. Review and accept again.</p>" : ""}
      <div class="decision-actions">
        <button id="approveSelected" type="button" ${candidate && displayedArt?.kind !== "native" ? "" : "disabled"} class="${review?.decision === "approve" && !review.stale ? "selected-approve" : ""}">Accept image</button>
        <button id="flagSelected" type="button" class="${review?.decision === "flag" && !review.stale ? "selected-flag" : ""}">Flag</button>
        <button id="clearSelected" type="button">Clear</button>
      </div>
      <label class="subtle" for="reviewNote">Note for this asset</label>
      <textarea id="reviewNote" data-review-target="${escapeHtml(selected.id)}" placeholder="Placement, silhouette, alpha, pose, or item identity…">${escapeHtml(review?.note || "")}</textarea>
      <p class="subtle">Decisions stay in this browser until exported. Only the selected image is reviewed; native fallback cannot be approved as restored art.</p>`;
    $("approveSelected").onclick = () => chooseDecision("approve");
    $("flagSelected").onclick = () => chooseDecision("flag");
    $("clearSelected").onclick = () => chooseDecision("clear");
    if (alternatives.length) {
      $("candidateAttempt").onchange = (event) => {
        state.attemptChoice[selected.id] = event.target.value;
        saveAttemptChoices();
        update();
      };
    }
    $("reviewNote").oninput = () => saveReviewNote(selected, $("reviewNote").value);

  }

  function filteredTargets() {
    const query = state.targetSearch.trim().toLowerCase();
    return reviewTargets.filter((target) => {
      const entry = asset(target.name);
      if (!entry) return false;
      if (state.hideAccepted && acceptedForReview(entry)) return false;
      const pending = target.active && (entry.repair || !["accepted", "hud_approved"].includes(entry.candidateStatus));
      if (["pending", "resolver", "manual"].includes(state.targetScope) && !pending) return false;
      if (state.targetScope === "resolver" && !target.resolverSelected) return false;
      if (state.targetScope === "manual" && target.resolverSelected) return false;
      if (state.targetScope === "active" && !target.active) return false;
      const aliases = sharedTargets.get(target.id)?.members.map((id) => {
        const definition = item(id);
        return `${definition.name} ${definition.icon} ${id}`;
      }).join(" ") || "";
      if (query && !`${target.name} ${target.id} ${itemByIcon.get(target.name.replace(/v[1-5][ab]?$/, ""))?.name || ""} ${aliases}`.toLowerCase().includes(query)) return false;
      const decision = decisionFor(entry);
      switch (state.decisionFilter) {
        case "jewelry": return ["Gauntlets", "Amulet", "Ring"].includes(item(target.itemId)?.stat);
        case "held": return repairPass?.held_armor_scope?.includes(entry.id) && !acceptedForReview(entry);
        case "main": return repairPass?.completion_scope?.includes(entry.id) && !acceptedForReview(entry);
        case "latest": return repairPass?.new_targets?.includes(entry.id) && candidateFor(entry)?.repair &&
          (!decision || decision.stale || decision.decision !== "approve");
        case "repairs": return candidateFor(entry)?.repair && (!decision || decision.stale || decision.decision !== "approve");
        case "staged": return !!repairPass?.staged[entry.id]?.staged_path;
        case "unreviewed": return !decision || decision.stale;
        case "flag": return (decision?.decision === "flag" && !decision.stale) ||
          magentaScan(entry)?.status === "suspected_magenta_spill";
        case "magenta": return magentaScan(entry)?.status === "suspected_magenta_spill";
        case "purple": return magentaScan(entry)?.status === "purple_material_check";
        case "clean": return magentaScan(entry)?.status === "no_spill_detected";
        case "approve": return decision?.decision === "approve" && !decision.stale;
        case "candidate": return !!entry.candidate;
        case "native": return !entry.candidate;
        default: return true;
      }
    });
  }

  function renderQueue() {
    const filtered = filteredTargets();
    const current = filtered.findIndex((target) => target.id === state.selectedTarget);
    const start = current < 0 ? 0 : Math.max(0, Math.min(current - 35, filtered.length - 120));
    const visible = filtered.slice(start, start + 120);
    $("queueCount").textContent = `${filtered.length} matching targets` +
      (filtered.length > 120 ? ` · showing ${start + 1}–${start + visible.length}; use search or Next` : "");
    $("targetList").replaceChildren();
    for (const target of visible) {
      const entry = asset(target.name);
      const decision = decisionFor(entry);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "target-row" + (target.id === state.selectedTarget ? " selected" : "");
      const title = document.createElement("span");
      title.textContent = target.name;
      const group = sharedTargets.get(target.id);
      if (group?.members.length > 1) button.title = group.members.map((id) => itemLabel(item(id))).join("\n");
      const mark = document.createElement("span");
      mark.textContent = decision && !decision.stale ? decision.decision === "flag" ? "FLAG" : "OK" :
        entry.candidate ? ["raw_prepared", "new_prepared", "border_repaired"].includes(entry.candidateStatus)
          ? "review 2×" : "2×" : "native";
      if (!target.resolverSelected) mark.textContent += target.treatment === "paperdoll_parts" ? " · head" : " · manual";
      if (group?.members.length > 1) mark.textContent += ` · ${group.members.length} items`;
      if (decision && !decision.stale) mark.className = decision.decision === "flag" ? "flagged" : "approved";
      const scan = magentaScan(entry);
      if (scan?.status === "suspected_magenta_spill") { mark.textContent += " · MAGENTA"; mark.className = "flagged"; }
      else if (scan?.status === "purple_material_check") mark.textContent += " · purple?";
      button.append(title, mark);
      button.onclick = () => selectTarget(target);
      $("targetList").append(button);
    }
  }

  function renderProgress() {
    const jewelry = reviewTargets.filter((target) => ["Gauntlets", "Amulet", "Ring"].includes(item(target.itemId)?.stat));
    const acceptedJewelry = jewelry.filter((target) => acceptedForReview(asset(target.name))).length;
    const flaggedJewelry = jewelry.filter((target) => {
      const decision = decisionFor(asset(target.name));
      return decision?.decision === "flag" && !decision.stale;
    }).length;
    $("jewelryProgress").hidden = !state.jewelry;
    $("jewelryProgress").textContent = `Gloves / amulets / rings: ${inventoryFits.size} items / ${jewelry.length} distinct images · ` +
      `${acceptedJewelry} accepted · ${flaggedJewelry} flagged · ` +
      `${jewelry.length - acceptedJewelry - flaggedJewelry} unreviewed. Hide accepted / staged skips completed images.`;
    const pending = reviewTargets.filter((target) => target.active &&
      !["accepted", "hud_approved"].includes(asset(target.name)?.candidateStatus));
    const reviewed = pending.filter((target) => {
      const decision = decisionFor(asset(target.name));
      return decision && !decision.stale;
    }).length;
    const spillCount = pending.filter((target) => magentaScan(asset(target.name))?.status === "suspected_magenta_spill").length;
    if (repairPass) {
      const remaining = repairPass.completion_scope?.filter((id) => !acceptedForReview(assetsById.get(id))).length;
      const held = repairPass.held_armor_scope?.filter((id) => !acceptedForReview(assetsById.get(id))).length;
      $("repairPassSummary").textContent =
        (repairPass.canonical_acceptance
          ? `${repairPass.canonical_acceptance.targets} images accepted in icon ledger · `
          : `${Object.values(repairPass.staged).filter((r) => r.staged_path).length} approvals staged · `) +
        (remaining === undefined ? `${repairPass.new_targets.length} replacements in this round` :
          `${remaining} equipment images still to review, excluding held armor, gloves and jewelry`) +
        (held === undefined ? "" : ` · ${held} held-armor images to review`) +
        (repairPass.canonical_acceptance ? " · manual offsets preserved. Runtime integration pending." :
          " · manual offsets preserved. Ledger unchanged.");
    }
    $("progress").textContent = `${reviewed} / ${pending.length} reviewed here · ${spillCount} auto spill flags`;
  }

  function selectName(name, slot = null) {
    state.selectedName = name.toLowerCase();
    state.selectedTarget = targetByName.get(state.selectedName)?.id || "";
    const visible = currentPanels.flatMap((panel) => panel.layers).find((entry) => entry.name === state.selectedName &&
      entry.kind === "item" && (!slot || entry.slot === slot));
    const mode = keyboardModes.find((mode) => mode.slot === visible?.slot && (!mode.pose || mode.pose === state.pose));
    if (mode) state.keyboardMode = mode.key;
    renderKeyboardStatus();
    renderLayerList();
    renderInspector();
    renderQueue();
    renderInventoryPreview();
  }

  function selectTarget(target) {
    state.selectedName = target.name;
    state.selectedTarget = target.id;
    state.force = null;
    if (target.treatment === "paperdoll_parts") {
      state.pose = "empty";
      const fields = ["background", "body", "head", "leftClosed", "leftHold", "leftOpen",
        "rightFingers", "rightOpen", "rightHold"];
      const matching = data.characters.filter((entry) => fields.some((field) => entry[field] === target.name));
      const chosen = matching.find((entry) => entry.start) || matching[0];
      if (chosen) state.characterId = chosen.id;
      if (matching.some((entry) => entry.leftClosed === target.name)) state.offHand = defaultShield;
      if (matching.some((entry) => [entry.rightFingers, entry.rightHold].includes(target.name))) state.oneHand = defaultOneHand;
      if (matching.some((entry) => entry.leftHold === target.name)) state.twoHand = defaultTwoHand;
      if (matching.some((entry) => [entry.leftClosed, entry.rightFingers, entry.rightHold].includes(target.name))) {
        state.pose = "one";
      }
    } else if (target.itemId) {
      const related = item(target.itemId);
      const jewelrySlot = related.stat === "Ring" ?
        (keyboardMode().slot.startsWith("Ring") ? keyboardMode().slot : "Ring1") : related.stat;
      if (oneHandStats.has(related.stat)) { state.oneHand = related.id; state.pose = "one"; }
      else if (twoHandStats.has(related.stat)) { state.twoHand = related.id; state.pose = "two"; }
      else if (related.stat === "Missile") state.shared.Bow = related.id;
      else if (related.stat === "Shield") { state.offHand = related.id; state.pose = "one"; }
      state.jewelry = jewelrySlots.includes(jewelrySlot);
      if (state.jewelry) {
        state.jewels[jewelrySlot] = related.id;
        state.keyboardMode = jewelrySlot;
      } else if (!dollType().can.weapon) {
        state.characterId = data.characters.find((entry) => entry.type === 0).id;
      }
    } else {
      const match = target.name.match(/^(.*)v([1-5])([ab]?)$/);
      const related = match ? itemByIcon.get(match[1]) : null;
      if (match && related) {
        const typeId = Number(match[2]) - 1;
        const sameType = data.characters.filter((entry) => entry.type === typeId);
        const chosen = sameType.find((entry) => entry.start) || sameType[0];
        if (chosen) state.characterId = chosen.id;
        const slot = related.stat === "Shield" ? "OffHand" :
          related.stat[0].toUpperCase() + related.stat.slice(1);
        if (bodySlots.has(slot)) {
          state.shared[slot] = related.id;
          const pose = slot === "Armor" && match[3] === "a" ? "empty" : "one";
          state.pose = pose;
          state.force = { name: target.name, slot, pose, itemId: related.id,
            unreachable: related.stat !== slot };
          if (slot === "Gauntlets") {
            state.jewels.Gauntlets = related.id;
            state.jewelry = true;
            state.force.pose = "jewelry";
          } else state.jewelry = false;
        } else if (slot === "OffHand") {
          state.pose = "one";
          state.offHand = related.id;
          state.jewelry = false;
          state.force = { name: target.name, slot, pose: "one", itemId: related.id, unreachable: true };
        }
      }
    }
    update();
  }

  function stepDoll(delta) {
    const index = data.characters.findIndex((entry) => entry.id === state.characterId);
    state.characterId = data.characters[(index + delta + data.characters.length) % data.characters.length].id;
    state.force = null;
    update();
  }

  function stepTarget(delta) {
    const filtered = filteredTargets();
    if (!filtered.length) return;
    const index = filtered.findIndex((target) => target.id === state.selectedTarget);
    selectTarget(filtered[(index + delta + filtered.length) % filtered.length]);
  }

  function keyboardMode() {
    return keyboardModes.find((mode) => mode.key === state.keyboardMode) || keyboardModes[0];
  }

  function keyboardItem(fresh = false) {
    const mode = keyboardMode();
    if (state.jewelry !== !!mode.jewelry || (mode.pose && state.pose !== mode.pose)) return null;
    const layers = fresh ? (state.jewelry ? jewelryLayers() : poseLayers(state.pose)).map(adjustedLayer) :
      currentPanels.flatMap((panel) => panel.layers);
    return layers.find((entry) => entry.kind === "item" && entry.slot === mode.slot &&
      (mode.key !== "F3" || item(entry.itemId)?.stat === "Shield")) || null;
  }

  function focusKeyboardItem() {
    const entry = keyboardItem(true);
    state.selectedName = entry?.name || "";
    state.selectedTarget = entry?.asset?.id || "";
  }

  function renderKeyboardStatus(message = "") {
    const mode = keyboardMode();
    const entry = keyboardItem();
    $("keyboardMode").value = mode.key;
    $("keyboardStatus").textContent = message || `${mode.jewelry ? "" : mode.key + " · "}${mode.label} · ` +
      (entry ? `${item(entry.itemId).name} · ${entry.name}` :
        !allowed(mode.slot, dollType()) ? "Unavailable for this body type" : "No item visible in this mode / pose");
  }

  function setKeyboardMode(key) {
    state.keyboardMode = key;
    const mode = keyboardMode();
    state.jewelry = !!mode.jewelry;
    state.force = null;
    if (mode.pose) state.pose = mode.pose;
    if (key === "F3" && item(state.offHand)?.stat !== "Shield") state.offHand = defaultShield;
    focusKeyboardItem();
    update();
  }

  function nextKeyboardItem() {
    const mode = keyboardMode();
    if (!allowed(mode.slot, dollType())) {
      renderKeyboardStatus(`${mode.label} is unavailable for ${typeLabels[person().type]}. Tab switches body type.`);
      return;
    }
    const control = selectControls.find((control) => control.slot === mode.control).select;
    if (!stepItemSelection(control, 1, true)) {
      renderKeyboardStatus(`No unaccepted ${mode.label.toLowerCase()} images for this body type and pose.`);
    }
  }

  function cycleDollType(delta) {
    const types = Object.values(data.types).filter((type) => type.can.weapon).map((type) => type.id);
    const index = types.indexOf(person().type);
    const nextType = types[(index + delta + types.length) % types.length];
    const people = data.characters.filter((entry) => entry.type === nextType && asset(entry.body));
    state.characterId = (people.find((entry) => entry.start) || people[0]).id;
    state.force = null;
    focusKeyboardItem();
    update();
  }

  for (const mode of keyboardModes) {
    const option = document.createElement("option");
    option.value = mode.key;
    option.textContent = `${mode.jewelry ? "" : mode.key + " · "}${mode.label}`;
    $("keyboardMode").append(option);
  }
  $("keyboardMode").onchange = (event) => { setKeyboardMode(event.target.value); event.target.blur(); };

  function update() {
    // Prevent a previous doll/slot's controls from acting while the new images load.
    currentPanels = [];
    ++inventoryRenderTicket;
    $("inventoryPreview").replaceChildren();
    $("inventoryPreview").hidden = !state.jewelry;
    $("equipmentReview").textContent = "Loading comparison…";
    $("selectedInspector").replaceChildren();
    syncControls();
    renderKeyboardStatus();
    renderQueue();
    renderProgress();
    renderStage();
  }

  $("prevDoll").onclick = () => stepDoll(-1);
  $("nextDoll").onclick = () => stepDoll(1);
  $("dollSelect").onchange = (event) => { state.characterId = Number(event.target.value); state.force = null; update(); };
  $("showBackground").onchange = (event) => { state.background = event.target.checked; update(); };
  $("originalDoll").onchange = (event) => {
    state.originalDoll = event.target.checked;
    update();
  };
  $("showJewelry").onchange = (event) => {
    state.jewelry = event.target.checked;
    if (state.jewelry && !keyboardMode().jewelry) state.keyboardMode = "Gauntlets";
    else if (!state.jewelry && keyboardMode().jewelry) state.keyboardMode = "F1";
    state.force = null;
    focusKeyboardItem();
    update();
  };
  $("artMode").onchange = (event) => { state.artMode = event.target.value; update(); };
  $("poseSelect").onchange = (event) => { state.pose = event.target.value; state.force = null; update(); };
  $("zoom").onchange = (event) => { state.zoom = Number(event.target.value); update(); };
  $("spearMastery").onchange = (event) => { state.spearMastery = event.target.value; update(); };
  $("hideAccepted").onchange = (event) => {
    state.hideAccepted = event.target.checked;
    try { localStorage.setItem(hideAcceptedStorageKey, String(state.hideAccepted)); }
    catch { /* Filtering does not depend on persistent browser storage. */ }
    const url = new URL(location.href);
    if (url.searchParams.has("hide_accepted")) {
      url.searchParams.set("hide_accepted", state.hideAccepted ? "1" : "0");
      history.replaceState(null, "", url);
    }
    syncControls();
    renderQueue();
    renderKeyboardStatus();
  };
  $("targetScope").onchange = (event) => { state.targetScope = event.target.value; renderQueue(); };
  $("decisionFilter").onchange = (event) => {
    state.decisionFilter = event.target.value;
    if (["repairs", "staged", "held", "jewelry"].includes(state.decisionFilter)) {
      state.targetScope = "all";
      $("targetScope").value = "all";
    }
    renderQueue();
  };
  $("targetSearch").oninput = (event) => { state.targetSearch = event.target.value; renderQueue(); };
  $("prevTarget").onclick = () => stepTarget(-1);
  $("nextTarget").onclick = () => stepTarget(1);
  $("exportDecisions").onclick = () => {
    const exportData = { schema: data.schema, exported_at: new Date().toISOString(), decisions: state.decisions,
      repair_pass: repairPass?.id || null,
      placement_schema: "openyamm-paperdoll-placement-v1", placements: state.placements,
      inventory_fit_proposals: inventoryFit || null,
      inactive_legacy_placement_keys: Object.keys(state.placements).filter((key) => /^(grip|preview):/.test(key)),
      automatic_findings: [...magentaRecords.values()].filter((record) => record.status !== "no_spill_detected" &&
        magentaScan(assetsById.get(record.target)) === record),
      sources: data.sources, units: "native_game_pixels", runtime_tables_modified: false };
    const url = URL.createObjectURL(new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "openyamm-paperdoll-review.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  $("importDecisions").onchange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const imported = JSON.parse(await file.text());
      if (imported.schema !== data.schema || typeof imported.decisions !== "object" || !imported.decisions) {
        throw new Error("This is not a paperdoll review export.");
      }
      if (imported.placements) {
        if (imported.placement_schema !== "openyamm-paperdoll-placement-v1") throw new Error("Unknown placement schema.");
        for (const [key, record] of Object.entries(imported.placements)) {
          if (key !== record.key || !Array.isArray(record.delta) || record.delta.length !== 2 ||
              !record.delta.every(Number.isInteger) || !Array.isArray(record.base) || record.base.length !== 2 ||
              !record.base.every(Number.isInteger)) throw new Error("Invalid placement proposal.");
        }
        state.placements = { ...state.placements, ...imported.placements };
        savePlacements();
      }
      state.decisions = { ...state.decisions, ...imported.decisions };
      restoreDecisionAttempts(imported.decisions);
      saveAttemptChoices();
      saveDecisions();
      update();
    } catch (error) { alert(error.message); }
    event.target.value = "";
  };
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.altKey || event.metaKey || event.isComposing) return;
    const focused = document.activeElement;
    const editing = ["INPUT", "TEXTAREA", "SELECT"].includes(focused?.tagName) || focused?.isContentEditable;
    if (event.key === "Escape" && editing) { focused.blur(); return; }
    // Notes, search and dropdowns retain normal editing/navigation. Escape returns to review shortcuts.
    if (editing) return;
    if (keyboardModes.some((mode) => mode.key === event.key)) {
      event.preventDefault();
      if (!event.repeat) setKeyboardMode(event.key);
      return;
    }
    if (event.key === "Tab") {
      event.preventDefault();
      if (!event.repeat) cycleDollType(event.shiftKey ? -1 : 1);
      return;
    }
    if (event.code === "Space" || event.key === " ") {
      event.preventDefault();
      if (event.repeat) return;
      if (event.shiftKey) {
        const entry = keyboardItem();
        if (entry && candidateFor(entry.asset) && chosenArt(entry.asset)?.kind !== "native") {
          chooseDecision("approve", entry.name, entry);
          renderKeyboardStatus(`Accepted ${entry.name} · ${keyboardMode().label}`);
        } else renderKeyboardStatus("Nothing to accept: wait for the candidate to be visible in this mode.");
      } else nextKeyboardItem();
      return;
    }
    const direction = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key];
    if (direction) {
      event.preventDefault();
      const entry = keyboardItem(true);
      if (entry && candidateFor(entry.asset) && chosenArt(entry.asset)?.kind !== "native") moveEquipment(entry, ...direction);
      return;
    }
    if (event.key === "[") stepTarget(-1);
    if (event.key === "]") stepTarget(1);
  });

  const query = new URLSearchParams(location.search);
  if (["0", "1"].includes(query.get("hide_accepted"))) {
    state.hideAccepted = query.get("hide_accepted") === "1";
    try { localStorage.setItem(hideAcceptedStorageKey, String(state.hideAccepted)); }
    catch { /* Filtering remains available for this page. */ }
  }
  if (["clean", "magenta", "purple", "repairs", "latest", "main", "held", "staged", "jewelry"].includes(query.get("review"))) state.decisionFilter = query.get("review");
  if (["repairs", "latest", "main", "held", "staged", "jewelry"].includes(state.decisionFilter)) state.targetScope = "all";
  const requestedDoll = Number(query.get("doll"));
  if (data.characters.some((entry) => entry.id === requestedDoll)) state.characterId = requestedDoll;
  if (query.get("native") === "1") state.artMode = "native";
  const targetGroup = sharedTargets.get(query.get("target"));
  const requestedTarget = targets.get(targetGroup?.representative_target || query.get("target"));
  if (["empty", "one", "two"].includes(query.get("pose"))) state.pose = query.get("pose");
  if (query.get("originalDoll") === "1") {
    state.originalDoll = true;
    if (query.get("native") !== "1") state.artMode = "candidate";
  }
  if (["candidate", "accepted", "native"].includes(query.get("art"))) state.artMode = query.get("art");
  const requestedId = Number(query.get("item"));
  const requestedItem = items.get(inventoryFits.get(requestedId)?.representative_item_id || requestedId);
  if (requestedItem) {
    if (oneHandStats.has(requestedItem.stat)) { state.oneHand = requestedItem.id; state.pose = "one"; }
    else if (twoHandStats.has(requestedItem.stat)) { state.twoHand = requestedItem.id; state.pose = "two"; }
    else if (requestedItem.stat === "Missile") state.shared.Bow = requestedItem.id;
    else if (requestedItem.stat === "Shield") { state.offHand = requestedItem.id; state.pose = "one"; }
    else if (["Gauntlets", "Amulet", "Ring"].includes(requestedItem.stat)) {
      const slot = requestedItem.stat === "Ring" ? "Ring1" : requestedItem.stat;
      state.jewels[slot] = requestedItem.id;
      state.jewelry = true;
      state.keyboardMode = slot;
    }
    state.selectedName = requestedItem.icon;
  }
  if (requestedTarget) selectTarget(requestedTarget);
  else update();
})();
