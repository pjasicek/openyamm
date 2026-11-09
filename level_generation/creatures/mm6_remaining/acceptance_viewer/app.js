const $ = id => document.getElementById(id);
const state = {
  families: [], familyIndex: 0, manifest: null, playlist: [], clipIndex: 0,
  action: '', view: '0', palette: '', elapsed: 0, clipElapsed: 0,
  frameIndex: -1, playing: true, lastTime: performance.now(), loadToken: 0,
  images: new Map(), busy: false, layout: null, viewerRevision: 0, clipToken: 0,
  fixups: {revision: 0, frames: {}}, edits: 0, savedEdits: 0, savePromise: null,
  saveTimer: null, undo: new Map(), manualStep: null, drag: null, switching: false,
  guideUndo: [],
  scaleDrag: null, familyMatchUndo: null,
  guideColumnCanvas: null, guideColumn: null,
  colorCache: new Map(), colorCacheBytes: 0,
};
const actionOrder = ['walk', 'standing', 'fidget', 'attack', 'hit', 'death', 'corpse'];

async function jsonRequest(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function message(text, error = false) {
  $('message').textContent = text;
  $('message').classList.toggle('error', error);
  if (error) setReviewFooterHidden(false);
}

function setReviewFooterHidden(hidden, remember = false) {
  $('reviewFooter').hidden = hidden;
  const toggle = $('toggleReviewFooter');
  toggle.textContent = hidden ? 'Show review' : 'Hide review';
  toggle.setAttribute('aria-expanded', String(!hidden));
  toggle.title = `${hidden ? 'Show' : 'Hide'} family acceptance, saved status, and help`;
  if (remember) {
    try { localStorage.setItem('mm6-review-footer-hidden', String(hidden)); }
    catch { /* Keep the toggle usable when browser storage is disabled. */ }
  }
}

function currentFamily() { return state.families[state.familyIndex]; }
function actions() { return state.manifest?.animations_by_palette[state.palette] || {}; }
function action() { return actions()[state.action]; }
function steps() { return state.manualStep ? [state.manualStep] : action()?.views[state.view] || []; }
function currentStep() { return steps()[state.frameIndex] || steps()[0]; }
function tier() { return state.manifest.pixels_per_logical_pixel; }
function frameFixup(name) {
  return {offset_px: [0, 0], scale_factor: 1, scale_anchor: 'bottom',
    regenerate: false, note: '', guide_offset_px: 0, center_guide_offset_px: 0,
    ...state.fixups.frames[name]};
}
function previewOffset(name) {
  return $('previewFixups').checked ? frameFixup(name).offset_px : [0, 0];
}

function restoredGeometry(name, factor = null, anchorMode = null) {
  const frame = state.manifest.frames[name];
  const fixup = frameFixup(name);
  const visible = $('previewFixups').checked && $('previewScale').checked;
  const scale = factor ?? (visible ? fixup.scale_factor : 1);
  const mode = anchorMode ?? fixup.scale_anchor;
  const [x, y] = frame.crop_origin_px;
  const [, , width, height] = frame.atlas_xywh;
  const bounds = state.manifest.review_restored_bounds[name] || [0, 0, width, height];
  const anchor = mode === 'pivot' ? state.manifest.logical_pivot.map(value => value * tier())
    : [x + (bounds[0] + bounds[2]) / 2, y + bounds[mode === 'top' ? 1 : 3]];
  const offset = previewOffset(name);
  return {x: anchor[0] + scale * (x - anchor[0]) + offset[0],
    y: anchor[1] + scale * (y - anchor[1]) + offset[1], width: width * scale, height: height * scale, scale};
}

function imagePath(relative) {
  return '/media/' + encodeURIComponent(currentFamily().id) + '/' +
    relative.split('/').map(encodeURIComponent).join('/');
}

function getImage(relative) {
  let image = state.images.get(relative);
  if (!image) {
    image = new Image();
    image.onload = renderStage;
    image.onerror = () => message(`Could not load ${relative}`, true);
    image.src = relative.startsWith('/mask/') ? relative : imagePath(relative);
    state.images.set(relative, image);
  }
  return image;
}

function colorSettings() {
  const regions = state.manifest.review_color_regions || {};
  const skin = Object.keys(regions).find(key => /skin/i.test(regions[key]));
  return state.fixups.colors?.[state.palette] ||
    {region: skin || 'all', saturation: 1, brightness: 1, enabled: true};
}

function clearColorCache() {
  state.colorCache.clear();
  state.colorCacheBytes = 0;
}

function colorMaskPath(page) {
  return `/mask/${encodeURIComponent(currentFamily().id)}/${page}/${colorSettings().region}`;
}

function updateColorControls() {
  const settings = colorSettings();
  $('colorRegion').replaceChildren(new Option('Whole sprite', 'all'));
  for (const [key, label] of Object.entries(state.manifest.review_color_regions || {})) {
    $('colorRegion').add(new Option(label.replace(/;.*$/, ''), key));
  }
  $('colorRegion').value = settings.region;
  for (const field of ['saturation', 'brightness']) {
    $(field).value = String(Math.round(settings[field] * 100));
    $(field + 'Value').value = `${$(field).value}%`;
  }
  $('previewColor').checked = settings.enabled;
}

function changeColor(changes) {
  if (!state.manifest) return;
  state.fixups.colors ||= {};
  state.fixups.colors[state.palette] = {...colorSettings(), ...changes};
  clearColorCache();
  updateColorControls();
  markDirty();
  renderStage();
}

function coloredSprite(image, frame) {
  const settings = colorSettings();
  if (!settings.enabled || (settings.saturation === 1 && settings.brightness === 1)) return null;
  const key = `${state.palette}/${frame.page}/${frame.atlas_xywh.join(',')}`;
  if (state.colorCache.has(key)) return state.colorCache.get(key);
  let mask = null;
  if (settings.region !== 'all') {
    mask = getImage(colorMaskPath(frame.page));
    if (!mask.complete || !mask.naturalWidth) return false;
  }
  const [x, y, width, height] = frame.atlas_xywh;
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const context = canvas.getContext('2d', {willReadFrequently: true});
  context.drawImage(image, x, y, width, height, 0, 0, width, height);
  const pixels = context.getImageData(0, 0, width, height);
  let coverage = null;
  if (mask) {
    context.clearRect(0, 0, width, height);
    context.drawImage(mask, x, y, width, height, 0, 0, width, height);
    coverage = context.getImageData(0, 0, width, height).data;
  }
  const data = pixels.data;
  for (let i = 0; i < data.length; i += 4) {
    if (!data[i + 3]) continue;
    const weight = coverage ? coverage[i] / 255 : 1;
    if (!weight) continue;
    const luma = .2126 * data[i] + .7152 * data[i + 1] + .0722 * data[i + 2];
    for (let c = 0; c < 3; c++) {
      const value = Math.max(0, Math.min(255,
        (luma + settings.saturation * (data[i + c] - luma)) * settings.brightness));
      data[i + c] = Math.round(data[i + c] + weight * (value - data[i + c]));
    }
  }
  context.putImageData(pixels, 0, 0);
  const bytes = width * height * 4;
  // Cache only current-palette frame crops, capped at 64 MiB even for large families.
  while (state.colorCache.size && state.colorCacheBytes + bytes > 64 * 1024 * 1024) {
    const oldest = state.colorCache.keys().next().value;
    const removed = state.colorCache.get(oldest);
    state.colorCacheBytes -= removed.width * removed.height * 4;
    state.colorCache.delete(oldest);
  }
  if (bytes <= 64 * 1024 * 1024) {
    state.colorCache.set(key, canvas);
    state.colorCacheBytes += bytes;
  }
  return canvas;
}

function drawBackdrop(context, width, height) {
  const background = $('background').value;
  if (background === 'checker') {
    context.fillStyle = '#89908b';
    context.fillRect(0, 0, width, height);
    context.fillStyle = '#c2c9c2';
    for (let y = 0; y < height; y += 24) {
      for (let x = (y / 24) % 2 ? 0 : 24; x < width; x += 48) {
        context.fillRect(x, y, 24, 24);
      }
    }
  } else if (background === 'light') {
    context.fillStyle = '#cbd1c7';
    context.fillRect(0, 0, width, height);
  } else {
    const gradient = context.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#273833');
    gradient.addColorStop(0.7, '#343b32');
    gradient.addColorStop(1, '#242b25');
    context.fillStyle = gradient;
    context.fillRect(0, 0, width, height);
  }
}

function referenceScale() {
  const animation = actions().standing || Object.values(actions())[0];
  const step = animation && Object.values(animation.views).flat()[0];
  return step?.native_scale || 1;
}

function frameScale(step) {
  return $('frameScale').checked ? (step.native_scale || referenceScale()) / referenceScale() : 1;
}

function configureCanvas(keepGuideAlignment = false) {
  if (!state.manifest) return;
  const zoom = Number($('zoom').value);
  const [width, height] = state.manifest.logical_canvas;
  const pivotX = state.manifest.logical_pivot[0];
  const pivotY = state.manifest.logical_pivot[1];
  let minX = pivotX;
  let minY = pivotY;
  let maxX = pivotX;
  let maxY = pivotY;
  function include(left, top, right, bottom, scale, mirrored) {
    let scaledLeft = pivotX + (left - pivotX) * scale;
    let scaledRight = pivotX + (right - pivotX) * scale;
    if (mirrored) {
      [scaledLeft, scaledRight] = [2 * pivotX - scaledRight, 2 * pivotX - scaledLeft];
    }
    minX = Math.min(minX, scaledLeft);
    maxX = Math.max(maxX, scaledRight);
    minY = Math.min(minY, pivotY + (top - pivotY) * scale);
    maxY = Math.max(maxY, pivotY + (bottom - pivotY) * scale);
  }
  for (const step of steps()) {
    const frame = state.manifest.frames[step.frame];
    const scale = frameScale(step);
    const geometry = restoredGeometry(step.frame);
    include(geometry.x / tier(), geometry.y / tier(),
      (geometry.x + geometry.width) / tier(), (geometry.y + geometry.height) / tier(), scale, step.mirrored);
    const [sourceWidth, sourceHeight] = frame.source_canvas;
    const correctionX = (width - sourceWidth) / 2 - Math.floor((width - sourceWidth) / 2);
    const bottomY = height - sourceHeight;
    const correctionY = state.manifest.anchor === 'center' ? bottomY / 2 - bottomY : 0;
    const nativeBounds = state.manifest.review_native_bounds[step.frame];
    if (nativeBounds) {
      include(nativeBounds[0] + correctionX, nativeBounds[1] + correctionY,
        nativeBounds[2] + correctionX, nativeBounds[3] + correctionY, scale, step.mirrored);
    }
  }
  const margin = 24;
  const contentWidth = (maxX - minX + margin * 2) * zoom;
  const contentHeight = (maxY - minY + margin * 2) * zoom;
  const canvasWidth = Math.ceil(Math.max(620, contentWidth));
  const canvasHeight = Math.ceil(Math.max(600, contentHeight));
  const oldLayout = state.layout;
  state.layout = {
    originX: (margin - minX) * zoom + (canvasWidth - contentWidth) / 2,
    originY: (margin - minY) * zoom + (canvasHeight - contentHeight) / 2,
    zoom,
  };
  // Zoom guides with the artwork; changing frames/clips at the same zoom leaves them stationary.
  if (oldLayout && (oldLayout.zoom !== zoom || keepGuideAlignment === true) && state.fixups.guides) {
    for (const guides of [state.fixups.guides, ...state.guideUndo]) {
      guides.x += state.layout.originX / zoom - oldLayout.originX / oldLayout.zoom;
      guides.y += state.layout.originY / zoom - oldLayout.originY / oldLayout.zoom;
      guides.zoom = zoom;
    }
    markDirty();
  }
  for (const canvas of [$('native'), $('restored')]) {
    canvas.width = canvasWidth;
    canvas.height = canvasHeight;
    canvas.style.width = `${canvasWidth}px`;
    canvas.style.height = `${canvasHeight}px`;
  }
  renderStage();
}

function drawSprite(context, step, original) {
  const zoom = Number($('zoom').value);
  const {originX, originY} = state.layout;
  const manifest = state.manifest;
  const anchorX = originX + manifest.logical_pivot[0] * zoom;
  const anchorY = originY + manifest.logical_pivot[1] * zoom;
  context.save();
  const scale = frameScale(step);
  context.translate(anchorX, anchorY);
  context.scale(step.mirrored ? -scale : scale, scale);
  context.translate(-anchorX, -anchorY);
  if (original) {
    const frame = manifest.frames[step.frame];
    const [sourceWidth, sourceHeight] = frame.source_canvas;
    const floorX = Math.floor((manifest.logical_canvas[0] - sourceWidth) / 2);
    const exactX = (manifest.logical_canvas[0] - sourceWidth) / 2;
    const bottomY = manifest.logical_canvas[1] - sourceHeight;
    const exactY = manifest.anchor === 'center' ? bottomY / 2 : bottomY;
    const image = getImage(`native_variants/${step.frame}_${state.palette}.png`);
    if (image.complete && image.naturalWidth) {
      context.imageSmoothingEnabled = false;
      context.drawImage(image, originX + (exactX - floorX) * zoom,
        originY + (exactY - bottomY) * zoom,
        manifest.logical_canvas[0] * zoom, manifest.logical_canvas[1] * zoom);
    }
  } else {
    const frame = manifest.frames[step.frame];
    const page = manifest.pages[frame.page];
    const image = getImage(page.variant_previews[state.palette]);
    if (image.complete && image.naturalWidth) {
      const [sourceX, sourceY, width, height] = frame.atlas_xywh;
      const geometry = restoredGeometry(step.frame);
      context.imageSmoothingEnabled = geometry.scale !== 1 || (!$('editMode').checked && zoom * scale !== tier());
      context.imageSmoothingQuality = 'high';
      const colored = coloredSprite(image, frame);
      if (colored !== false) {
        context.drawImage(colored || image, colored ? 0 : sourceX, colored ? 0 : sourceY, width, height,
          originX + geometry.x * zoom / tier(), originY + geometry.y * zoom / tier(),
          geometry.width * zoom / tier(), geometry.height * zoom / tier());
      }
    }
  }
  context.restore();
}

function drawCanvas(canvas, step, original) {
  const context = canvas.getContext('2d');
  const zoom = Number($('zoom').value);
  const {originX, originY} = state.layout;
  const manifest = state.manifest;
  drawBackdrop(context, canvas.width, canvas.height);
  if (!manifest) return;
  const anchorX = originX + manifest.logical_pivot[0] * zoom;
  const anchorY = originY + manifest.logical_pivot[1] * zoom;
  if (step) {
    drawSprite(context, step, original);
    if ($('topGuides').checked) drawHeightGuides(context, canvas, step, original);
  }
  if ($('guides').checked) {
    context.strokeStyle = '#e9c871';
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(0, anchorY + .5);
    context.lineTo(canvas.width, anchorY + .5);
    context.moveTo(anchorX + .5, anchorY - 14);
    context.lineTo(anchorX + .5, anchorY + 14);
    context.stroke();
  }
  if (step && $('centerGuide').checked) drawCenterGuide(context, canvas, step);
  if (step && typeof drawLandmarks === 'function') drawLandmarks(context, canvas, step, original);
}

function renderStage() {
  if (!state.manifest) return;
  state.guideColumn = null;
  const sequence = steps();
  const step = sequence[state.frameIndex] || sequence[0] || null;
  drawCanvas($('native'), step, true);
  drawCanvas($('restored'), step, false);
  $('clip').textContent = step
    ? `${state.manualStep ? 'Master · canonical view' : `${state.action} · view ${state.view}`} · ${step.frame} · frame ${state.frameIndex + 1}/${sequence.length}` +
      ` · native scale ${step.native_scale}` + (step.mirrored ? ' · mirrored' : '')
    : `${state.action} · view ${state.view} · native no-image action`;
  updateEditor();
  if (typeof updateLandmarkControls === 'function') updateLandmarkControls();
}

function selectFrame() {
  const sequence = steps();
  if (!sequence.length) {
    if (state.frameIndex !== -1) { state.frameIndex = -1; renderStage(); }
    return;
  }
  const total = sequence.reduce((sum, step) => sum + Math.max(step.duration_ms, 1), 0);
  const time = state.elapsed % total;
  let sum = 0;
  let index = sequence.length - 1;
  for (let i = 0; i < sequence.length; i++) {
    sum += Math.max(sequence[i].duration_ms, 1);
    if (time < sum) { index = i; break; }
  }
  if (index !== state.frameIndex) { state.frameIndex = index; renderStage(); }
}

function buildPlaylist() {
  const list = [];
  const seen = new Set();
  const names = Object.keys(actions()).sort((left, right) => {
    const leftIndex = actionOrder.indexOf(left);
    const rightIndex = actionOrder.indexOf(right);
    return (leftIndex < 0 ? 100 : leftIndex) - (rightIndex < 0 ? 100 : rightIndex);
  });
  for (const name of names) {
    const animation = actions()[name];
    const views = animation.single_view ? ['0'] : Object.keys(animation.views);
    for (const view of views) {
      const sequence = animation.views[view] || [];
      if (!sequence.length) continue;
      const signature = JSON.stringify(sequence.map(step =>
        [step.frame, step.duration_ms, step.mirrored]));
      if (seen.has(signature)) continue;
      seen.add(signature);
      list.push({action: name, view});
    }
  }
  state.playlist = list;
  state.clipIndex = Math.max(0, list.findIndex(clip =>
    clip.action === state.action && clip.view === state.view));
}

function resetPlayback() {
  state.elapsed = 0;
  state.clipElapsed = 0;
  state.frameIndex = -1;
  state.playing = !$('editMode').checked;
  $('play').textContent = state.playing ? 'Pause' : 'Play';
  selectFrame();
}

async function prepareClip() {
  if (!state.manifest) return;
  const token = ++state.clipToken;
  const manifest = state.manifest;
  state.playing = false;
  state.frameIndex = 0;
  $('play').disabled = true;
  $('play').textContent = 'Loading…';
  renderStage();
  const paths = new Set();
  for (const step of steps()) {
    paths.add(`native_variants/${step.frame}_${state.palette}.png`);
    const frame = manifest.frames[step.frame];
    paths.add(manifest.pages[frame.page].variant_previews[state.palette]);
    if (colorSettings().enabled && colorSettings().region !== 'all' &&
        (colorSettings().saturation !== 1 || colorSettings().brightness !== 1)) {
      paths.add(colorMaskPath(frame.page));
    }
  }
  try {
    await Promise.all([...paths].map(path => getImage(path).decode()));
    if (token !== state.clipToken || manifest !== state.manifest) return;
    $('play').disabled = false;
    resetPlayback();
  } catch (error) {
    if (token !== state.clipToken) return;
    $('play').textContent = 'Load failed';
    message(`Animation image failed to load: ${error.message}`, true);
  }
}

function populateActions() {
  const select = $('action');
  const previous = state.action;
  select.replaceChildren();
  for (const name of Object.keys(actions())) select.add(new Option(name, name));
  state.action = actions()[previous] ? previous : (actions().walk ? 'walk' : select.value);
  select.value = state.action;
  populateViews();
}

function populateViews() {
  const select = $('view');
  const previous = state.view;
  select.replaceChildren();
  for (const view of Object.keys(action()?.views || {})) {
    const suffix = Number(view) > 4 ? ' · mirrored' : '';
    select.add(new Option(`${view}${suffix}`, view));
  }
  state.view = action()?.views[previous] ? previous : select.value;
  select.value = state.view;
}

function manualClip() {
  state.manualStep = null;
  $('tour').checked = false;
  buildPlaylist();
  configureCanvas();
  prepareClip();
}

function moveClip(amount, nativeOnly = false) {
  if (!state.playlist.length) return;
  let index = state.clipIndex;
  for (let i = 0; i < state.playlist.length; i++) {
    index = (index + amount + state.playlist.length) % state.playlist.length;
    const clip = state.playlist[index];
    if (!nativeOnly || actions()[clip.action].views[clip.view].some(step => !step.mirrored)) break;
    if (i === state.playlist.length - 1) return;
  }
  state.manualStep = null;
  state.clipIndex = index;
  const clip = state.playlist[state.clipIndex];
  state.action = clip.action;
  state.view = clip.view;
  $('action').value = state.action;
  populateViews();
  $('view').value = state.view;
  configureCanvas();
  prepareClip();
}

function clipHoldTime() {
  const total = steps().reduce((sum, step) => sum + Math.max(step.duration_ms, 1), 0);
  return Math.max(2400, Math.min(6500, total * 2 + 500));
}

function decisionMatchesFixups(family) {
  return (family.decision?.fixups_revision || 0) === (family.fixups_revision || 0);
}

function updateDecisionUI(updateNote = true) {
  const accepted = state.families.filter(family => family.decision?.decision === 'accepted' &&
    decisionMatchesFixups(family)).length;
  const flagged = state.families.filter(family => family.decision?.decision === 'flagged' &&
    decisionMatchesFixups(family)).length;
  const prior = state.families.filter(family => family.decision &&
    (family.decision.viewer_revision !== state.viewerRevision || !decisionMatchesFixups(family))).length;
  $('counts').textContent = `${accepted} accepted · ${flagged} flagged · ` +
    `${state.families.length - accepted - flagged} to review` +
    (prior ? ` · ${prior} made in prior preview` : '');
  const select = $('family');
  for (let i = 0; i < state.families.length; i++) {
    const family = state.families[i];
    const mark = family.decision?.decision === 'accepted' ? '✓' :
      family.decision?.decision === 'flagged' ? '⚑' : '·';
    const priorMark = family.decision && (family.decision.viewer_revision !== state.viewerRevision ||
      !decisionMatchesFixups(family)) ? ' ↻' : '';
    select.options[i].textContent = `${mark} ${family.label}${priorMark}`;
  }
  const decision = currentFamily()?.decision;
  if (updateNote) $('note').value = decision?.note || '';
  if (decision) {
    const priorText = decision.viewer_revision !== state.viewerRevision
      ? ' · made in an earlier viewer version; review the current preview' : '';
    const fixupText = decisionMatchesFixups(currentFamily()) ? '' : ' · frame fixups changed; review again';
    message(`${decision.decision} · saved ${new Date(decision.updated_at).toLocaleString()}${priorText}${fixupText}`);
  }
  else message('No decision saved for this package.');
}

async function showFamily(index) {
  if (!state.families.length || state.switching) return;
  state.switching = true;
  try { await flushFixups(); }
  catch (error) {
    message(`Navigation stopped: ${error.message}. Your edits remain in this tab.`, true);
    $('family').value = String(state.familyIndex);
    state.switching = false;
    return;
  }
  state.familyIndex = (index + state.families.length) % state.families.length;
  const family = currentFamily();
  const token = ++state.loadToken;
  $('family').value = String(state.familyIndex);
  $('familyPosition').textContent = `${state.familyIndex + 1} / ${state.families.length}`;
  message(`Loading ${family.label}…`);
  state.manifest = null;
  state.clipToken++;
  state.images.clear();
  clearColorCache();
  try {
    const manifest = await jsonRequest(`/api/family/${encodeURIComponent(family.id)}`);
    if (token !== state.loadToken) return;
    state.manifest = manifest;
    state.fixups = manifest.review_fixups;
    if (state.fixups.guides) $('zoom').value = String(state.fixups.guides.zoom);
    family.fixups_revision = state.fixups.revision;
    state.edits = 0;
    state.savedEdits = 0;
    state.undo.clear();
    state.familyMatchUndo = null;
    $('familyMatchStatus').textContent = '';
    $('landmarkActionStatus').textContent = '';
    state.guideUndo = [];
    state.layout = null;
    state.manualStep = null;
    state.frameIndex = 0;
    state.drag = null;
    $('masterFrame').replaceChildren();
    for (const name of Object.keys(manifest.frames).sort()) $('masterFrame').add(new Option(name, name));
    saveStatus(state.fixups.revision ? `Saved checkpoint r${state.fixups.revision}` : 'No frame fixups yet');
    state.palette = Object.keys(manifest.variants).find(key => manifest.variants[key].exact_base_bypass) ||
      Object.keys(manifest.variants)[0];
    $('palette').replaceChildren();
    for (const [key, variant] of Object.entries(manifest.variants)) {
      $('palette').add(new Option(variant.name, key));
    }
    $('palette').value = state.palette;
    updateColorControls();
    state.action = 'walk';
    state.view = '0';
    populateActions();
    buildPlaylist();
    configureCanvas();
    document.querySelector('.viewport').scrollTo(0, 0);
    prepareClip();
    $('title').textContent = family.label;
    $('detail').textContent = `${family.minimum_sampling.toFixed(3)}× minimum detail · ` +
      `${family.frame_count} masters · ${family.source} · pipeline ${family.pipeline_status.replaceAll('_', ' ')}`;
    history.replaceState(null, '', '#' + encodeURIComponent(family.id));
    updateDecisionUI();
  } catch (error) {
    if (token === state.loadToken) message(error.message, true);
  } finally {
    state.switching = false;
  }
}

async function saveDecision(decision, advance) {
  if (state.busy || !state.manifest) return;
  state.busy = true;
  for (const id of ['accept', 'flag', 'clear']) $(id).disabled = true;
  const family = currentFamily();
  try {
    await flushFixups();
    const result = await jsonRequest('/api/decision', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({family: family.id, manifest_sha256: family.manifest_sha256,
        artifact_sha256: family.artifact_sha256, fixups_revision: state.fixups.revision,
        preview_fixups: $('previewFixups').checked, preview_scale: $('previewScale').checked,
        decision, note: $('note').value}),
    });
    family.decision = result.decision;
    updateDecisionUI();
    if (advance) await showFamily(state.familyIndex + 1);
  } catch (error) {
    message(error.message, true);
  } finally {
    state.busy = false;
    for (const id of ['accept', 'flag', 'clear']) $(id).disabled = false;
  }
}

function tick(now) {
  const delta = Math.max(0, Math.min(now - state.lastTime, 100));
  state.lastTime = now;
  if (state.manifest && state.playing) {
    state.elapsed += delta;
    state.clipElapsed += delta;
    if ($('tour').checked && state.playlist.length && state.clipElapsed >= clipHoldTime()) moveClip(1);
    else selectFrame();
  }
  requestAnimationFrame(tick);
}

function bindControls() {
  let hideFooter = true;
  try { hideFooter = localStorage.getItem('mm6-review-footer-hidden') !== 'false'; }
  catch { /* The default keeps the artwork area expanded. */ }
  setReviewFooterHidden(hideFooter);
  $('toggleReviewFooter').onclick = () => setReviewFooterHidden(!$('reviewFooter').hidden, true);
  $('family').onchange = () => showFamily(Number($('family').value));
  $('previousFamily').onclick = () => showFamily(state.familyIndex - 1);
  $('nextFamily').onclick = () => showFamily(state.familyIndex + 1);
  $('action').onchange = () => { state.action = $('action').value; populateViews(); manualClip(); };
  $('view').onchange = () => { state.view = $('view').value; manualClip(); };
  $('palette').onchange = () => {
    state.palette = $('palette').value;
    state.images.clear();
    clearColorCache();
    updateColorControls();
    populateActions();
    buildPlaylist();
    configureCanvas();
    prepareClip();
  };
  $('previousClip').onclick = () => moveClip(-1);
  $('nextClip').onclick = () => moveClip(1);
  $('play').onclick = () => {
    state.playing = !state.playing;
    $('play').textContent = state.playing ? 'Pause' : 'Play';
  };
  $('zoom').onchange = configureCanvas;
  $('frameScale').onchange = configureCanvas;
  $('background').onchange = renderStage;
  $('guides').onchange = renderStage;
  $('topGuides').onchange = renderStage;
  $('centerGuide').onchange = renderStage;
  for (const field of ['saturation', 'brightness']) {
    $(field).oninput = () => changeColor({[field]: Number($(field).value) / 100});
  }
  $('colorRegion').onchange = () => changeColor({region: $('colorRegion').value});
  $('previewColor').onchange = () => changeColor({enabled: $('previewColor').checked});
  $('resetColor').onclick = () => changeColor({saturation: 1, brightness: 1, enabled: true});
  bindEditor();
  $('accept').onclick = () => saveDecision('accepted', true);
  $('flag').onclick = () => saveDecision('flagged', true);
  $('clear').onclick = () => saveDecision('clear', false);
  document.addEventListener('keydown', event => {
    if (['TEXTAREA', 'INPUT', 'SELECT'].includes(document.activeElement.tagName)) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.shiftKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      if (!state.switching) {
        $('tour').checked = false;
        moveClip(event.key === 'ArrowLeft' ? -1 : 1, true);
      }
      return;
    }
    if (event.shiftKey && event.code === 'Space') {
      event.preventDefault();
      if (!event.repeat) alignHeadAndFit();
      return;
    }
    if (document.activeElement === $('toggleReviewFooter') && event.code === 'Space') return;
    const key = event.key.toLowerCase();
    const arrows = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]};
    if (arrows[event.key] && $('editMode').checked) {
      event.preventDefault();
      const [x, y] = arrows[event.key];
      if (document.activeElement === $('native')) moveGuide((y || x) * (event.shiftKey ? 10 : 1), y ? 'y' : 'x');
      else nudge(x, y, event.shiftKey ? 10 : 1);
    } else if (key === '[' || key === ']') {
      event.preventDefault(); stepFrame(key === '[' ? -1 : 1);
    } else if (key === 'n') showFamily(state.familyIndex + 1);
    else if (key === 'p') showFamily(state.familyIndex - 1);
    else if (key === 'a') saveDecision('accepted', true);
    else if (key === 'f') saveDecision('flagged', true);
    else if (event.code === 'Space') { event.preventDefault(); $('play').click(); }
  });
}

async function start() {
  bindControls();
  try {
    const queue = await jsonRequest('/api/families');
    if (queue.collection) {
      document.title = queue.collection.title;
      document.querySelector('h1').textContent = queue.collection.title;
    }
    state.families = queue.families;
    state.viewerRevision = queue.viewer_revision;
    if (!state.families.length) throw new Error('No complete master families are available.');
    $('family').replaceChildren();
    state.families.forEach((family, index) => $('family').add(new Option(family.label, index)));
    const excluded = $('excluded').querySelector('ul');
    for (const row of queue.excluded) {
      const item = document.createElement('li');
      item.textContent = `${row.label}: ${row.reason}`;
      excluded.append(item);
    }
    $('excluded').querySelector('summary').textContent =
      `Controls & queue scope · ${state.families.length} complete MM6 families · ${queue.excluded.length} excluded`;
    const initial = state.families.findIndex(family => family.id === decodeURIComponent(location.hash.slice(1)));
    await showFamily(initial < 0 ? 0 : initial);
    requestAnimationFrame(tick);
  } catch (error) {
    message(error.message, true);
  }
}

function nativeHeightBounds(manifest, name) {
  const native = manifest.review_native_bounds[name];
  if (!native) return null;
  const bottomY = manifest.logical_canvas[1] - manifest.frames[name].source_canvas[1];
  const correctionY = manifest.anchor === 'center' ? -bottomY / 2 : 0;
  return [native[1] + correctionY, native[3] + correctionY];
}

function heightBounds(step) {
  const restored = state.manifest.review_restored_bounds[step.frame];
  const geometry = restoredGeometry(step.frame);
  return {
    native: nativeHeightBounds(state.manifest, step.frame),
    restored: restored && [(geometry.y + geometry.scale * restored[1]) / tier(),
      (geometry.y + geometry.scale * restored[3]) / tier()],
  };
}

function automaticGuidePosition(step, axis) {
  const bounds = state.manifest.review_native_bounds[step.frame];
  if (!bounds) return null;
  const frame = state.manifest.frames[step.frame];
  const nativeX = (state.manifest.logical_canvas[0] - frame.source_canvas[0]) / 2;
  const coordinate = axis === 'x' ? (bounds[0] + bounds[2]) / 2 + nativeX - Math.floor(nativeX)
    : heightBounds(step).native[0];
  const pivot = state.manifest.logical_pivot[axis === 'x' ? 0 : 1];
  const factor = frameScale(step) * (axis === 'x' && step.mirrored ? -1 : 1);
  const origin = axis === 'x' ? state.layout.originX : state.layout.originY;
  return origin / Number($('zoom').value) + pivot + (coordinate - pivot) * factor;
}

function ensureGuides(step) {
  if (state.fixups.guides || !step) return;
  const x = automaticGuidePosition(step, 'x');
  const y = automaticGuidePosition(step, 'y');
  if (x === null || y === null) return;
  // One-time migration: retain this opening frame's old guide adjustments as fixed family references.
  const old = frameFixup(step.frame);
  const factor = frameScale(step) / tier();
  state.fixups.guides = {
    x: x + old.center_guide_offset_px * factor * (step.mirrored ? -1 : 1),
    y: y + old.guide_offset_px * factor,
    zoom: Number($('zoom').value),
  };
}

function guideScreenX(step) {
  ensureGuides(step);
  return state.fixups.guides ? state.fixups.guides.x * Number($('zoom').value) : null;
}

function guideIntersections(step, height) {
  const x = Math.floor(guideScreenX(step));
  const cacheKey = [x, height, step.frame, step.mirrored, frameScale(step), state.palette,
    Number($('zoom').value), state.layout.originX, state.layout.originY,
    ...previewOffset(step.frame), $('editMode').checked].join('|');
  if (state.guideColumn?.key === cacheKey) return state.guideColumn;
  const sample = state.guideColumnCanvas ||= document.createElement('canvas');
  sample.width = 1;
  sample.height = height;
  const sampleContext = sample.getContext('2d', {willReadFrequently: true});
  const alpha = [];
  for (const original of [true, false]) {
    sampleContext.clearRect(0, 0, 1, height);
    sampleContext.save();
    sampleContext.translate(-x, 0);
    // Render just the sprite into a transparent one-pixel column using the exact display transform.
    drawSprite(sampleContext, step, original);
    sampleContext.restore();
    alpha.push(sampleContext.getImageData(0, 0, 1, height).data);
  }
  const runs = [];
  let previous = -1;
  for (let y = 0; y < height; y++) {
    const bits = (alpha[0][y * 4 + 3] > 0 ? 1 : 0) | (alpha[1][y * 4 + 3] > 0 ? 2 : 0);
    if (bits !== previous) {
      runs.push({y, height: 1, bits});
      previous = bits;
    } else runs[runs.length - 1].height++;
  }
  state.guideColumn = {key: cacheKey, x, runs};
  return state.guideColumn;
}

function drawCenterGuide(context, canvas, step) {
  const x = guideScreenX(step);
  if (x === null) return;
  const column = guideIntersections(step, canvas.height);
  context.save();
  context.globalAlpha = 1;
  for (const run of column.runs) {
    if (run.bits === 3) {
      context.fillStyle = '#ff0000';
      context.fillRect(column.x, run.y, 1, run.height);
      context.fillStyle = '#ff69b4';
      context.fillRect(column.x + 1, run.y, 1, run.height);
    } else {
      context.fillStyle = ['#00ff00', '#ff0000', '#ff69b4'][run.bits];
      context.fillRect(column.x, run.y, 2, run.height);
    }
  }
  context.fillStyle = '#dce8df';
  context.font = '12px system-ui';
  context.fillText('fixed center', x + 7, 18);
  context.restore();
}

function drawHeightGuides(context, canvas, step, original) {
  const bounds = heightBounds(step);
  const zoom = Number($('zoom').value);
  const pivotY = state.manifest.logical_pivot[1];
  const project = y => state.layout.originY + (pivotY + (y - pivotY) * frameScale(step)) * zoom;
  const draw = (range, color, label, dashed) => {
    if (!range) return;
    context.save();
    context.strokeStyle = color;
    context.fillStyle = color;
    context.font = '12px system-ui';
    context.lineWidth = 1;
    for (let i = 0; i < 2; i++) {
      const y = range[i];
      if (y === null) continue;
      context.setLineDash(dashed ? [7, 5] : (i ? [2, 5] : []));
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(canvas.width, y);
      context.stroke();
      // Original and restored labels occupy opposite edges even when their lines coincide.
      const text = `${label} ${i ? 'bottom' : 'top'}`;
      const x = dashed ? canvas.width - context.measureText(text).width - 9 : 9;
      context.fillText(text, x, y + (i ? 14 : -6));
    }
    context.restore();
  };
  draw([guideScreenY(step), bounds.native ? project(bounds.native[1]) : null], '#77e5ed', 'reference', false);
  if (!original && bounds.restored) draw(bounds.restored.map(project), '#ff9bcd', 'restored', true);
}

function saveStatus(text, error = false) {
  $('saveStatus').textContent = text;
  $('saveStatus').classList.toggle('error', error);
  $('exportUnsaved').hidden = !error;
}

async function flushFixups() {
  clearTimeout(state.saveTimer);
  if (state.savePromise) return state.savePromise;
  if (state.edits === state.savedEdits) return;
  const family = currentFamily();
  state.savePromise = (async () => {
    while (state.edits !== state.savedEdits) {
      const edits = state.edits;
      saveStatus('Saving…');
      const result = await jsonRequest('/api/fixups', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({family: family.id, manifest_sha256: family.manifest_sha256,
          artifact_sha256: family.artifact_sha256, revision: state.fixups.revision, frames: state.fixups.frames,
          guides: state.fixups.guides, colors: state.fixups.colors || {}, landmarks: state.fixups.landmarks || {}}),
      });
      state.fixups.revision = result.revision;
      family.fixups_revision = result.revision;
      state.savedEdits = edits;
      updateDecisionUI(false);
      saveStatus(`Saved checkpoint r${result.revision} · ${Object.keys(result.frames).length} edited frames`);
    }
  })();
  try { await state.savePromise; }
  catch (error) { saveStatus(`UNSAVED: ${error.message}`, true); throw error; }
  finally { state.savePromise = null; }
}

function rememberUndo(name) {
  const stack = state.undo.get(name) || [];
  stack.push(structuredClone(frameFixup(name)));
  if (stack.length > 200) stack.shift();
  state.undo.set(name, stack);
}

function changeFrame(name, changes, remember = true) {
  if (remember) rememberUndo(name);
  state.fixups.frames[name] = {...frameFixup(name), ...changes};
  markDirty();
  renderStage();
}

function markDirty() {
  state.edits++;
  saveStatus('Unsaved changes…');
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(() => flushFixups().catch(() => {}), 300);
}

function changeGuide(axis, value, remember = true) {
  ensureGuides(currentStep());
  if (!state.fixups.guides) return;
  if (remember) {
    state.guideUndo.push({...state.fixups.guides});
    if (state.guideUndo.length > 200) state.guideUndo.shift();
  }
  state.fixups.guides[axis] = value;
  markDirty();
  renderStage();
}

function pauseForEdit() {
  state.playing = false;
  $('play').textContent = 'Play';
  $('tour').checked = false;
}

function editingStep() {
  if (!state.manifest || state.switching || $('play').disabled || !$('editMode').checked) return null;
  const step = currentStep();
  if (step) {
    pauseForEdit();
    $('previewFixups').checked = true;
  }
  return step;
}

function nudge(x, y, multiplier = 1) {
  const step = editingStep();
  if (!step) return;
  const amount = ($('nudgeStep').value === 'native' ? tier() : 1) * multiplier;
  const old = frameFixup(step.frame).offset_px;
  changeFrame(step.frame, {offset_px: [old[0] + x * amount * (step.mirrored ? -1 : 1),
    old[1] + y * amount]});
}

function moveGuide(amount, axis = 'y') {
  const step = editingStep();
  if (!step) return;
  const unit = $('nudgeStep').value === 'native' ? tier() : 1;
  ensureGuides(step);
  if (!state.fixups.guides) return;
  $(axis === 'x' ? 'centerGuide' : 'topGuides').checked = true;
  changeGuide(axis, state.fixups.guides[axis] + amount * unit / tier());
}

function guideScreenY(step) {
  ensureGuides(step);
  return state.fixups.guides ? state.fixups.guides.y * Number($('zoom').value) : null;
}

function chooseClipFrame(index) {
  if (!state.manifest || !steps().length || $('play').disabled) return;
  pauseForEdit();
  state.frameIndex = (index + steps().length) % steps().length;
  state.elapsed = steps().slice(0, state.frameIndex).reduce((sum, step) => sum + Math.max(step.duration_ms, 1), 0);
  renderStage();
}

function stepFrame(amount) {
  if (state.manualStep) {
    const select = $('masterFrame');
    select.selectedIndex = (select.selectedIndex + amount + select.options.length) % select.options.length;
    select.onchange();
  } else chooseClipFrame(state.frameIndex + amount);
}

function scaleHint() {
  return state.manifest?.review_scale_hints[currentStep()?.frame]?.[Number($('scaleHint').value)];
}

function scalePreviewClipped() {
  if (!state.layout) return false;
  const {originX, originY, zoom} = state.layout;
  const [px, py] = state.manifest.logical_pivot;
  return steps().some(step => {
    const g = restoredGeometry(step.frame);
    const scale = frameScale(step);
    const xs = [g.x, g.x + g.width].map(x => originX +
      (px + (x / tier() - px) * scale * (step.mirrored ? -1 : 1)) * zoom);
    const ys = [g.y, g.y + g.height].map(y => originY + (py + (y / tier() - py) * scale) * zoom);
    return Math.min(...xs) < 0 || Math.max(...xs) > $('restored').width ||
      Math.min(...ys) < 0 || Math.max(...ys) > $('restored').height;
  });
}

function updateScaleEditor(step, editing) {
  const clipped = step && scalePreviewClipped();
  $('fitScale').disabled = !clipped;
  $('fitScale').textContent = clipped ? 'Fit preview (cropped)' : 'Fit preview';
  const key = step ? `${currentFamily().id}/${step.frame}` : '';
  if ($('scaleHint').dataset.frame !== key) {
    $('scaleHint').dataset.frame = key;
    $('scaleHint').replaceChildren();
    const hints = state.manifest?.review_scale_hints[step?.frame] || [];
    hints.forEach((hint, index) => $('scaleHint').add(new Option(
      `${hint.name.replaceAll('_', ' ')} · ${hint.axis === 'y' ? 'height' : 'width'}`, index)));
  }
  const hint = scaleHint();
  const percent = value => `${value >= 1 ? '+' : ''}${((value - 1) * 100).toFixed(3)}%`;
  $('scaleHint').disabled = !step || !editing || !hint;
  $('applyScaleHint').disabled = !step || !editing || !hint || hint.correction < 0.5 || hint.correction > 1.5;
  $('scaleHintReadout').textContent = hint
    ? `Trial ${percent(hint.correction)} · range ${hint.correction_interval.map(percent).join(' to ')}`
    : 'No saved measurements for this frame; adjust manually.';
  $('scaleHintReadout').title = hint
    ? `${hint.native_length.toFixed(2)} original px / ${(hint.restored_length_px / tier()).toFixed(2)} restored ` +
      'logical px. Saved landmarks, not newly verified anatomy. Range assumes ±2 logical px per span. ' +
      'A measurement trial is not an approved whole-body correction.' : '';
  if (!step) return;
  const fixup = frameFixup(step.frame);
  if (document.activeElement !== $('scalePercent')) {
    $('scalePercent').value = Number(((fixup.scale_factor - 1) * 100).toFixed(4));
  }
  if (!state.scaleDrag) $('scaleSlider').value = (fixup.scale_factor - 1) * 100;
  $('scaleAnchor').value = fixup.scale_anchor;
}

function changeScale(factor, remember = true) {
  if (!Number.isFinite(factor) || factor < 0.5 || factor > 1.5) return;
  const step = editingStep();
  if (!step || frameFixup(step.frame).scale_factor === factor) return;
  $('previewScale').checked = true;
  changeFrame(step.frame, {scale_factor: factor}, remember);
}

function familyHeightMatch(manifest, name) {
  const native = nativeHeightBounds(manifest, name);
  const restored = manifest.review_restored_bounds[name];
  if (!native || !restored || native[1] <= native[0] || restored[3] <= restored[1]) {
    return {skip: 'empty silhouette'};
  }
  // Use the exported bounds, not the current preview, so repeated matches never compound.
  const factor = (native[1] - native[0]) * manifest.pixels_per_logical_pixel / (restored[3] - restored[1]);
  if (!Number.isFinite(factor) || factor < 0.5 || factor > 1.5) return {skip: 'outside size range'};
  const offsetY = Math.round(native[1] * manifest.pixels_per_logical_pixel -
    (manifest.frames[name].crop_origin_px[1] + restored[3]));
  if (Math.abs(offsetY) > 16384) return {skip: 'outside offset range'};
  return {factor, offsetY};
}

function matchFamilyHeightAndBottom() {
  if (!state.manifest || state.switching || !$('editMode').checked) return;
  pauseForEdit();
  $('previewFixups').checked = true;
  $('previewScale').checked = true;
  const undo = new Map();
  const skipped = new Map();
  let matched = 0;
  for (const name of Object.keys(state.manifest.frames)) {
    const match = familyHeightMatch(state.manifest, name);
    if (match.skip) {
      skipped.set(match.skip, (skipped.get(match.skip) || 0) + 1);
      continue;
    }
    matched++;
    const fixup = frameFixup(name);
    if (fixup.scale_factor === match.factor && fixup.scale_anchor === 'bottom' &&
        fixup.offset_px[1] === match.offsetY) continue;
    undo.set(name, {scale_factor: fixup.scale_factor, scale_anchor: fixup.scale_anchor,
      offsetY: fixup.offset_px[1]});
    rememberUndo(name);
    state.fixups.frames[name] = {...fixup, scale_factor: match.factor, scale_anchor: 'bottom',
      offset_px: [fixup.offset_px[0], match.offsetY]};
  }
  if (undo.size) {
    state.familyMatchUndo = undo;
    markDirty();
  }
  const total = Object.keys(state.manifest.frames).length;
  const skipText = [...skipped].map(([reason, count]) => `${count} skipped: ${reason}`).join(' · ');
  $('familyMatchStatus').textContent = `Matched ${matched}/${total} frames · ${undo.size} updated` +
    (skipText ? ` · ${skipText}` : '');
  renderStage();
}

function undoFamilyHeightMatch() {
  if (!state.manifest || state.switching || !$('editMode').checked || !state.familyMatchUndo) return;
  pauseForEdit();
  const undo = state.familyMatchUndo;
  for (const [name, previous] of undo) {
    const fixup = frameFixup(name);
    rememberUndo(name);
    state.fixups.frames[name] = {...fixup, scale_factor: previous.scale_factor, scale_anchor: previous.scale_anchor,
      offset_px: [fixup.offset_px[0], previous.offsetY]};
  }
  state.familyMatchUndo = null;
  markDirty();
  $('familyMatchStatus').textContent = `Restored size and bottom for ${undo.size} frames`;
  renderStage();
}

function updateEditor() {
  const step = currentStep();
  const editing = $('editMode').checked;
  $('restored').classList.toggle('editing', editing);
  $('frameScrubber').max = Math.max(0, steps().length - 1);
  $('frameScrubber').value = Math.max(0, state.frameIndex);
  $('returnClip').disabled = !state.manualStep;
  for (const id of ['nudgeLeft', 'nudgeRight', 'nudgeUp', 'nudgeDown', 'resetFrame', 'regenerate', 'frameNote',
    'guideOffset', 'resetGuide', 'centerOffset', 'resetCenter', 'scalePercent', 'scaleSlider',
    'scaleAnchor', 'resetScale']) {
    $(id).disabled = !step || !editing;
  }
  $('undoFrame').disabled = !step || !editing || !state.undo.get(step.frame)?.length;
  $('undoGuides').disabled = !step || !editing || !state.guideUndo.length;
  $('matchFamily').disabled = !state.manifest || !editing;
  $('undoFamilyMatch').disabled = !state.manifest || !editing || !state.familyMatchUndo;
  updateScaleEditor(step, editing);
  if (!step) {
    $('offsetReadout').textContent = 'No image in this action';
    $('heightReadout').textContent = '';
    return;
  }
  $('masterFrame').value = step.frame;
  const fixup = frameFixup(step.frame);
  ensureGuides(step);
  if (document.activeElement !== $('guideOffset')) $('guideOffset').value = state.fixups.guides?.y ?? '';
  if (document.activeElement !== $('centerOffset')) $('centerOffset').value = state.fixups.guides?.x ?? '';
  $('regenerate').checked = fixup.regenerate;
  if (document.activeElement !== $('frameNote')) $('frameNote').value = fixup.note;
  const [x, y] = fixup.offset_px;
  $('offsetReadout').textContent = `Offset X ${x > 0 ? '+' : ''}${x}, Y ${y > 0 ? '+' : ''}${y} atlas px`;
  $('offsetReadout').title = `${x / tier()}, ${y / tier()} original pixels, before mirroring`;
  const bounds = heightBounds(step);
  if (bounds.native && bounds.restored) {
    const pivot = state.manifest.logical_pivot[1];
    const guideY = (guideScreenY(step) - state.layout.originY) / Number($('zoom').value);
    const top = bounds.restored[0] - (pivot + (guideY - pivot) / frameScale(step));
    const nativeHeight = bounds.native[1] - bounds.native[0];
    const restoredHeight = bounds.restored[1] - bounds.restored[0];
    $('heightReadout').textContent = `Top vs guide ${top > 0 ? '+' : ''}${top.toFixed(1)} · height ` +
      `${nativeHeight.toFixed(1)} → ${restoredHeight.toFixed(1)} original px` +
      (!$('previewFixups').checked ? ' · fixups hidden' : '');
    $('heightReadout').title = 'Positive top delta means restored starts lower. Heights exclude transparent margins.';
  } else $('heightReadout').textContent = 'Empty silhouette';
}

function bindEditor() {
  $('editMode').onchange = () => {
    if ($('editMode').checked) pauseForEdit();
    renderStage();
  };
  $('previewFixups').onchange = renderStage;
  $('previewScale').onchange = renderStage;
  $('scalePercent').oninput = () => changeScale(1 + $('scalePercent').valueAsNumber / 100);
  $('scaleSlider').onpointerdown = event => {
    const step = editingStep();
    if (step) {
      state.scaleDrag = {frame: step.frame, changed: false};
      event.currentTarget.setPointerCapture(event.pointerId);
    }
  };
  $('scaleSlider').oninput = () => {
    const drag = state.scaleDrag;
    if (drag && drag.frame !== currentStep()?.frame) return;
    changeScale(1 + Number($('scaleSlider').value) / 100, !drag?.changed);
    if (drag) drag.changed = true;
  };
  const endScaleDrag = () => { state.scaleDrag = null; };
  $('scaleSlider').onchange = endScaleDrag;
  $('scaleSlider').onpointerup = endScaleDrag;
  $('scaleSlider').onpointercancel = endScaleDrag;
  $('scaleSlider').onlostpointercapture = endScaleDrag;
  $('scaleAnchor').onchange = () => {
    const step = editingStep();
    if (step) changeFrame(step.frame, {scale_anchor: $('scaleAnchor').value});
  };
  $('resetScale').onclick = () => changeScale(1);
  $('fitScale').onclick = () => configureCanvas(true);
  $('scaleHint').onchange = () => updateScaleEditor(currentStep(), $('editMode').checked);
  $('applyScaleHint').onclick = () => {
    const hint = scaleHint();
    if (hint) changeScale(hint.correction);
  };
  $('matchFamily').onclick = matchFamilyHeightAndBottom;
  $('undoFamilyMatch').onclick = undoFamilyHeightMatch;
  $('previousFrame').onclick = () => stepFrame(-1);
  $('nextFrame').onclick = () => stepFrame(1);
  $('frameScrubber').oninput = () => chooseClipFrame(Number($('frameScrubber').value));
  $('masterFrame').onchange = () => {
    const name = $('masterFrame').value;
    const bindings = Object.values(actions()).flatMap(animation => Object.values(animation.views).flat());
    const match = bindings.find(step => step.frame === name);
    state.manualStep = {frame: name, duration_ms: match?.duration_ms || 125,
      native_scale: match?.native_scale || referenceScale(), mirrored: false};
    state.frameIndex = 0;
    configureCanvas();
    prepareClip();
    pauseForEdit();
  };
  $('returnClip').onclick = manualClip;
  $('nudgeLeft').onclick = () => nudge(-1, 0);
  $('nudgeRight').onclick = () => nudge(1, 0);
  $('nudgeUp').onclick = () => nudge(0, -1);
  $('nudgeDown').onclick = () => nudge(0, 1);
  $('undoFrame').onclick = () => {
    const step = editingStep();
    const previous = step && state.undo.get(step.frame)?.pop();
    if (previous) changeFrame(step.frame, previous, false);
  };
  $('resetFrame').onclick = () => {
    const step = editingStep();
    if (step) changeFrame(step.frame, {offset_px: [0, 0]});
  };
  $('guideOffset').oninput = () => {
    const step = editingStep();
    const offset = $('guideOffset').valueAsNumber;
    if (step && Number.isFinite(offset) && Math.abs(offset) <= 1000000) {
      $('topGuides').checked = true;
      changeGuide('y', offset);
    }
  };
  $('resetGuide').onclick = () => {
    const step = editingStep();
    const value = step && automaticGuidePosition(step, 'y');
    if (step && value !== null) { $('topGuides').checked = true; changeGuide('y', value); }
  };
  $('centerOffset').oninput = () => {
    const step = editingStep();
    const offset = $('centerOffset').valueAsNumber;
    if (step && Number.isFinite(offset) && Math.abs(offset) <= 1000000) {
      $('centerGuide').checked = true;
      changeGuide('x', offset);
    }
  };
  $('resetCenter').onclick = () => {
    const step = editingStep();
    const value = step && automaticGuidePosition(step, 'x');
    if (step && value !== null) { $('centerGuide').checked = true; changeGuide('x', value); }
  };
  $('undoGuides').onclick = () => {
    if (!editingStep()) return;
    const previous = state.guideUndo.pop();
    if (previous) {
      state.fixups.guides = previous;
      markDirty();
      renderStage();
    }
  };
  $('regenerate').onchange = () => {
    const step = editingStep();
    if (step) changeFrame(step.frame, {regenerate: $('regenerate').checked});
  };
  $('frameNote').onfocus = pauseForEdit;
  $('frameNote').oninput = () => {
    const step = editingStep();
    if (step) changeFrame(step.frame, {note: $('frameNote').value});
  };
  $('saveFixups').onclick = () => flushFixups().catch(() => {});
  $('exportFixups').onclick = async event => {
    event.preventDefault();
    try { await flushFixups(); location.href = '/api/fixups/export'; }
    catch (error) { message(error.message, true); }
  };
  $('exportUnsaved').onclick = () => {
    const family = currentFamily();
    const draft = {schema_version: 1, unsaved: true, family: family.id,
      manifest_sha256: family.manifest_sha256, artifact_sha256: family.artifact_sha256,
      pixels_per_logical_pixel: tier(), ...state.fixups};
    const url = URL.createObjectURL(new Blob([JSON.stringify(draft, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url; link.download = `${family.id}-unsaved-fixups.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  window.addEventListener('beforeunload', event => {
    if (state.edits !== state.savedEdits) { event.preventDefault(); event.returnValue = ''; }
  });
  const canvas = $('restored');
  canvas.onpointerdown = event => {
    if (event.button !== 0) return;
    const step = editingStep();
    if (!step) return;
    event.preventDefault(); canvas.focus();
    state.drag = {pointer: event.pointerId, name: step.frame, x: event.clientX, y: event.clientY,
      offset: [...frameFixup(step.frame).offset_px], mirror: step.mirrored ? -1 : 1,
      pixels: Number($('zoom').value) * frameScale(step) / tier(), changed: false};
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add('dragging');
  };
  canvas.onpointermove = event => {
    const drag = state.drag;
    if (!drag || drag.pointer !== event.pointerId) return;
    const offset = [drag.offset[0] + Math.round((event.clientX - drag.x) / drag.pixels) * drag.mirror,
      drag.offset[1] + Math.round((event.clientY - drag.y) / drag.pixels)];
    if (offset.every((value, i) => value === frameFixup(drag.name).offset_px[i])) return;
    changeFrame(drag.name, {offset_px: offset}, !drag.changed);
    drag.changed = true;
  };
  const endDrag = () => {
    state.drag = null; canvas.classList.remove('dragging');
    flushFixups().catch(() => {});
  };
  canvas.onpointerup = endDrag;
  canvas.onpointercancel = endDrag;
  canvas.onlostpointercapture = endDrag;
  const native = $('native');
  let guideDrag = null;
  const guideAt = event => {
    if (!state.manifest || !$('editMode').checked) return null;
    const step = currentStep();
    if (!step) return null;
    const rect = native.getBoundingClientRect();
    const x = $('centerGuide').checked ? guideScreenX(step) : null;
    const y = $('topGuides').checked ? guideScreenY(step) : null;
    const dx = x === null ? Infinity : Math.abs(event.clientX - rect.left - x);
    const dy = y === null ? Infinity : Math.abs(event.clientY - rect.top - y);
    return Math.min(dx, dy) > 14 ? null : (dx <= dy ? 'x' : 'y');
  };
  native.onpointerdown = event => {
    if (event.button !== 0) return;
    const axis = guideAt(event);
    if (!axis) return;
    const step = editingStep();
    if (!step) return;
    event.preventDefault(); native.focus();
    guideDrag = {pointer: event.pointerId, axis,
      start: axis === 'x' ? event.clientX : event.clientY,
      offset: state.fixups.guides[axis],
      pixels: Number($('zoom').value) / tier(), changed: false};
    native.setPointerCapture(event.pointerId);
  };
  native.onpointermove = event => {
    if (!guideDrag) {
      const axis = guideAt(event);
      native.style.cursor = axis === 'x' ? 'ew-resize' : axis === 'y' ? 'ns-resize' : 'default';
      return;
    }
    if (guideDrag.pointer !== event.pointerId) return;
    const position = guideDrag.axis === 'x' ? event.clientX : event.clientY;
    const value = guideDrag.offset + Math.round((position - guideDrag.start) / guideDrag.pixels) / tier();
    if (value === state.fixups.guides[guideDrag.axis]) return;
    changeGuide(guideDrag.axis, value, !guideDrag.changed);
    guideDrag.changed = true;
  };
  const endGuideDrag = () => { guideDrag = null; flushFixups().catch(() => {}); };
  native.onpointerup = endGuideDrag;
  native.onpointercancel = endGuideDrag;
  native.onlostpointercapture = endGuideDrag;
}

start();
