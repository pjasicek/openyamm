(() => {
  "use strict";

  const data = window.PAPERDOLL_ESRGAN_DATA;
  const $ = (id) => document.getElementById(id);
  if (!data || !data.characters.length) {
    document.body.textContent = "Comparison data is missing. Run esrgan_baseline.py --all first.";
    return;
  }

  const modes = [
    { id: "native", label: "Original", note: "1× pixels, doubled without repainting" },
    { id: "esrgan", label: "Real-ESRGAN", note: "Exact 2× RGB with source alpha" },
    { id: "current", label: "Current candidate", note: "Existing restoration in the review browser" },
  ];
  const imagePromises = new Map();
  const query = new URLSearchParams(location.search);
  const firstId = Number(query.get("doll"));
  const state = {
    dollIndex: Math.max(0, data.characters.findIndex((entry) => entry.id === firstId)),
    pose: "empty", part: "", background: true, surface: "dark", zoom: 1,
  };
  let ticket = 0;

  function image(path) {
    if (!path) return Promise.resolve(null);
    if (!imagePromises.has(path)) {
      imagePromises.set(path, new Promise((resolve) => {
        const value = new Image();
        value.onload = () => resolve(value);
        value.onerror = () => resolve(null);
        value.src = path;
      }));
    }
    return imagePromises.get(path);
  }

  function character() { return data.characters[state.dollIndex]; }
  function poseList(entry) {
    return entry.poses.length ? entry.poses : [
      { pose: "body", layers: [[entry.body, entry.body_x, entry.body_y]] },
    ];
  }
  function chosenPose(entry) {
    const poses = poseList(entry);
    return poses.find((pose) => pose.pose === state.pose) || poses[0];
  }
  function assetPath(name, mode) {
    const item = data.assets[name];
    return mode === "current" ? item.current || item.native : item[mode];
  }
  function titleCase(value) {
    return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function changeDoll(index) {
    state.dollIndex = (index + data.characters.length) % data.characters.length;
    state.pose = poseList(character())[0].pose;
    state.part = character().body;
    const url = new URL(location.href);
    url.searchParams.set("doll", String(character().id));
    url.searchParams.delete("pose");
    url.searchParams.delete("part");
    history.replaceState(null, "", url);
    render();
  }

  function makeCard(mode) {
    const card = document.createElement("article");
    card.className = "compare-card";
    const heading = document.createElement("div");
    heading.className = "card-label";
    const strong = document.createElement("strong");
    strong.textContent = mode.label;
    const small = document.createElement("small");
    small.textContent = mode.note;
    heading.append(strong, small);
    const canvas = document.createElement("canvas");
    canvas.width = 350;
    canvas.height = 756;
    canvas.className = `sprite-canvas surface-${state.surface}`;
    canvas.style.width = `${350 * state.zoom}px`;
    card.append(heading, canvas);
    return { card, canvas };
  }

  async function drawPose(canvas, entry, pose, mode, renderId) {
    const layers = pose.layers;
    const paths = layers.map(([name]) => assetPath(name, mode));
    const [background, ...sprites] = await Promise.all([
      image(entry.background_native), ...paths.map(image),
    ]);
    if (renderId !== ticket) return;
    const context = canvas.getContext("2d");
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.imageSmoothingEnabled = false;
    if (state.background && background) {
      context.drawImage(background, 0, 0, canvas.width, canvas.height);
    }
    for (let index = 0; index < layers.length; index++) {
      const [name, x, y] = layers[index];
      const sprite = sprites[index];
      if (!sprite) continue;
      const [width, height] = data.assets[name].size;
      context.drawImage(sprite, x * 2, y * 2, width * 2, height * 2);
    }
  }

  function renderPoseButtons(entry) {
    const target = $("poseButtons");
    target.replaceChildren();
    for (const pose of poseList(entry)) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = titleCase(pose.pose);
      button.setAttribute("aria-pressed", String(chosenPose(entry).pose === pose.pose));
      button.onclick = () => {
        state.pose = pose.pose;
        const url = new URL(location.href);
        url.searchParams.set("pose", pose.pose);
        history.replaceState(null, "", url);
        render();
      };
      target.append(button);
    }
  }

  function renderParts(entry) {
    const target = $("partList");
    target.replaceChildren();
    $("partCount").textContent = `${entry.parts.length} distinct sprite${entry.parts.length === 1 ? "" : "s"}`;
    for (const name of entry.parts) {
      const asset = data.assets[name];
      const button = document.createElement("button");
      button.type = "button";
      button.setAttribute("aria-pressed", String(name === state.part));
      const thumb = document.createElement("img");
      thumb.src = asset.native;
      thumb.alt = "";
      const span = document.createElement("span");
      span.textContent = name;
      if (Object.keys(asset.registration_flags).length) {
        const warning = document.createElement("span");
        warning.className = "warn";
        warning.textContent = " ⚠";
        span.append(warning);
      }
      button.append(thumb, span);
      button.onclick = () => {
        state.part = name;
        const url = new URL(location.href);
        url.searchParams.set("part", name);
        history.replaceState(null, "", url);
        render();
      };
      target.append(button);
    }
  }

  async function renderDetails(renderId) {
    const name = state.part;
    const asset = data.assets[name];
    const [width, height] = asset.size;
    const flags = Object.entries(asset.registration_flags).flatMap(([profile, failures]) =>
      failures.map((failure) => `${profile}: ${failure}`));
    $("partMeta").textContent = `${name} · native ${width}×${height} · ESRGAN ${width * 2}×${height * 2}` +
      (flags.length ? ` · ${flags.join("; ")}` : " · registration check passed");
    $("partMeta").classList.toggle("notice", flags.length > 0);
    const grid = $("detailGrid");
    grid.replaceChildren();
    for (const mode of modes) {
      const card = document.createElement("article");
      card.className = "detail-card";
      const heading = document.createElement("h3");
      heading.textContent = mode.label;
      const note = document.createElement("p");
      note.textContent = mode.id === "current" && !asset.current
        ? "No current candidate; showing enlarged original" : mode.note;
      const surface = document.createElement("div");
      surface.className = `detail-surface surface-${state.surface}`;
      const picture = document.createElement("img");
      picture.alt = `${mode.label} ${name}`;
      picture.style.width = `${width * 4}px`;
      picture.src = assetPath(name, mode.id);
      surface.append(picture);
      card.append(heading, note, surface);
      grid.append(card);
      image(picture.src).then((loaded) => {
        if (renderId !== ticket || !loaded) return;
        if (mode.id === "current" && asset.current &&
            (loaded.width !== width * 2 || loaded.height !== height * 2)) {
          note.textContent = `Candidate source is ${loaded.width}×${loaded.height}; displayed at the 2× footprint`;
          note.classList.add("notice");
        }
      });
    }
  }

  function render() {
    const renderId = ++ticket;
    const entry = character();
    if (!entry.parts.includes(state.part)) state.part = entry.body;
    $("doll").value = String(entry.id);
    const bodyOnly = entry.kind === "body_only";
    $("background").disabled = bodyOnly;
    $("backgroundLabel").lastChild.textContent = bodyOnly
      ? " Scene is embedded in this sprite" : " Game background";
    $("poseDescription").textContent = bodyOnly
      ? "This original is one opaque full-canvas scene. Its backdrop is part of the source image."
      : "The body and separate limbs are layered at the character type's game table offsets.";
    const portrait = $("portrait");
    portrait.replaceChildren();
    for (const [path, label] of [[entry.portrait_native, "Assigned portrait"],
      [entry.portrait_current, "Restored portrait"]]) {
      if (!path) continue;
      const figure = document.createElement("figure");
      const picture = document.createElement("img");
      picture.src = path;
      picture.alt = `${entry.portrait} ${label}`;
      const caption = document.createElement("figcaption");
      caption.textContent = label;
      figure.append(picture, caption);
      portrait.append(figure);
    }
    renderPoseButtons(entry);
    const poseGrid = $("poseGrid");
    poseGrid.replaceChildren();
    for (const mode of modes) {
      const { card, canvas } = makeCard(mode);
      poseGrid.append(card);
      drawPose(canvas, entry, chosenPose(entry), mode.id, renderId);
    }
    renderParts(entry);
    renderDetails(renderId);
  }

  for (const entry of data.characters) {
    const option = document.createElement("option");
    option.value = String(entry.id);
    option.textContent = `#${entry.id} ${entry.label || entry.body} · ${entry.kind.replaceAll("_", " ")}`;
    $("doll").append(option);
  }
  $("coverage").textContent = `${data.characters.length} prepared dolls · ` +
    `${Object.keys(data.assets).length} unique bodies and limbs. Rows without original body or portrait are omitted.`;
  $("doll").onchange = (event) => changeDoll(data.characters.findIndex((entry) =>
    entry.id === Number(event.target.value)));
  $("previous").onclick = () => changeDoll(state.dollIndex - 1);
  $("next").onclick = () => changeDoll(state.dollIndex + 1);
  $("background").onchange = (event) => { state.background = event.target.checked; render(); };
  $("surface").onchange = (event) => { state.surface = event.target.value; render(); };
  $("zoom").onchange = (event) => { state.zoom = Number(event.target.value); render(); };
  state.pose = poseList(character()).find((pose) => pose.pose === query.get("pose"))?.pose ||
    poseList(character())[0].pose;
  state.part = character().parts.includes(query.get("part")) ? query.get("part") : character().body;
  render();
})();
