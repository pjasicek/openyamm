// Landmarks describe the unchanged actor canvas. Display transforms are reversible;
// fitting is an explicit proposal and never updates source pixels or native metadata.
const landmarkColors = {eye1: '#5ef6ff', eye2: '#ffd45e', head: '#96ff85', head_top: '#aab4ff', groin: '#ff8cdc'};
const landmarkUndo = [];
let landmarkDrag = null;

function landmarkPoint(name, side, kind) {
  const saved = state.fixups.landmarks?.[name]?.[side];
  if (saved && Object.hasOwn(saved, kind)) return {xy: saved[kind], source: 'recorded', recorded: true};
  return state.manifest?.review_landmark_suggestions?.frames?.[name]?.[side]?.[kind] || null;
}

function landmarkActorPoint(name, side, point, inverse = false) {
  if (side === 'original') return [...point];
  const frame = state.manifest.frames[name], geometry = restoredGeometry(name);
  const crop = frame.crop_origin_px.map(value => value / tier());
  const position = [geometry.x / tier(), geometry.y / tier()];
  return point.map((value, i) => value === null ? null : inverse
    ? crop[i] + (value - position[i]) / geometry.scale
    : position[i] + (value - crop[i]) * geometry.scale);
}

function landmarkScreenPoint(step, side, point) {
  const actor = landmarkActorPoint(step.frame, side, point);
  const scale = frameScale(step), zoom = Number($('zoom').value);
  const pivot = state.manifest.logical_pivot, origin = [state.layout.originX, state.layout.originY];
  return actor.map((value, i) => value === null ? null : origin[i] + zoom *
    (pivot[i] + (value - pivot[i]) * scale * (i === 0 && step.mirrored ? -1 : 1)));
}

function landmarkFromPointer(event, canvas, step, side) {
  const rect = canvas.getBoundingClientRect(), zoom = Number($('zoom').value), scale = frameScale(step);
  const screen = [(event.clientX - rect.left) * canvas.width / rect.width,
    (event.clientY - rect.top) * canvas.height / rect.height];
  const origin = [state.layout.originX, state.layout.originY], pivot = state.manifest.logical_pivot;
  const actor = screen.map((value, i) => pivot[i] + ((value - origin[i]) / zoom - pivot[i]) /
    (scale * (i === 0 && step.mirrored ? -1 : 1)));
  const point = landmarkActorPoint(step.frame, side, actor, true).map(value => Math.round(value * 100) / 100);
  if ($('landmarkKind').value === 'head') point[1] = null;
  return point;
}

function drawLandmarks(context, canvas, step, original) {
  if (!$('showLandmarks')?.checked) return;
  const side = original ? 'original' : 'restored';
  context.save();
  context.font = '12px sans-serif';
  for (const [kind, color] of Object.entries(landmarkColors)) {
    const point = landmarkPoint(step.frame, side, kind);
    if (!point?.xy) continue;
    const [x, y] = landmarkScreenPoint(step, side, point.xy);
    context.strokeStyle = color; context.fillStyle = color; context.lineWidth = 1.5;
    context.setLineDash(point.recorded ? [] : [3, 3]);
    context.beginPath();
    if (kind === 'head') {
      context.moveTo(x, 28); context.lineTo(x, canvas.height - 10); context.stroke();
      context.fillText('head X', x + 5, 44);
    } else {
      if (point.recorded) {
        context.moveTo(x - 6, y); context.lineTo(x + 6, y);
        context.moveTo(x, y - 6); context.lineTo(x, y + 6);
      } else context.arc(x, y, 5, 0, Math.PI * 2);
      context.stroke();
      context.strokeStyle = '#19241c'; context.lineWidth = 3; context.setLineDash([]);
      const label = {groin: 'groin', eye1: 'E1', eye2: 'E2', head_top: 'head top'}[kind];
      context.strokeText(label, x + 8, y - 6); context.fillText(label, x + 8, y - 6);
    }
  }
  context.restore();
}

function updateLandmarkControls() {
  if (!state.manifest || !$('landmarkReadout')) return;
  const step = currentStep();
  if (!step) { $('landmarkReadout').textContent = 'No sprite in this animation.'; return; }
  const kind = $('landmarkKind').value;
  $('landmarkReadout').textContent = ['original', 'restored'].map(side => {
    const point = landmarkPoint(step.frame, side, kind);
    if (!point) return `${side}: uncertain / unrecorded`;
    if (!point.xy) return `${side}: hidden / not applicable`;
    const xy = point.xy.filter(value => value !== null).map(value => Number(value.toFixed(2))).join(', ');
    return `${side}: ${xy} (${point.recorded ? 'recorded' :
      `suggested · ${point.source}`})`;
  }).join('   |   ');
  const warning = state.manifest.review_landmark_suggestions?.warning;
  if (warning) $('landmarkReadout').textContent += `   |   ${warning}`;
  updateHeadActions(step);
}

function updateHeadActions(step) {
  const busy = !step || state.switching || $('play').disabled;
  const head = ['original', 'restored'].map(side => step && landmarkPoint(step.frame, side, 'head')?.xy);
  const top = ['original', 'restored'].map(side => step && landmarkPoint(step.frame, side, 'head_top')?.xy);
  const format = (points, axis) => points.map((point, i) => `${i ? 'Restored' : 'Original'}: ` +
    (point ? `${landmarkActorPoint(step.frame, i ? 'restored' : 'original', point)[axis].toFixed(2)} px`
      : 'unrecorded')).join('\n');
  $('headXReadout').textContent = format(head, 0);
  $('headTopReadout').textContent = format(top, 1);
  $('headCenterGuide').disabled = busy || !head[0];
  $('headAlignX').disabled = busy || !head.every(Boolean);
  $('headTopGuide').disabled = busy || !top[0];
  $('headAlignY').disabled = busy || !top.every(Boolean);
  $('headFitFeet').disabled = busy || !top.every(Boolean) ||
    !nativeHeightBounds(state.manifest, step.frame) || !state.manifest.review_restored_bounds[step.frame];
  $('editHeadTop').disabled = busy;
  $('landmarkUndoPlacement').disabled = busy || !state.undo.get(step.frame)?.length;
  $('landmarkUndoGuide').disabled = busy || !state.guideUndo.length;
}

function headActionStep() {
  if (!state.manifest || state.switching || $('play').disabled) return null;
  const step = currentStep();
  if (step) pauseForEdit();
  return step;
}

function headActionStatus(text) {
  $('landmarkActionStatus').textContent = text;
}

function moveGuideToLandmark(kind, axis) {
  const step = headActionStep();
  const point = step && landmarkPoint(step.frame, 'original', kind)?.xy;
  if (!point) return;
  $(axis === 0 ? 'centerGuide' : 'topGuides').checked = true;
  const position = landmarkScreenPoint(step, 'original', point)[axis] / Number($('zoom').value);
  changeGuide(axis === 0 ? 'x' : 'y', position);
  headActionStatus(`Guide moved to original ${kind === 'head' ? 'head X' : 'head top'}.`);
}

function alignLandmarkAxis(kind, axis) {
  const step = headActionStep();
  const pair = step && landmarkPairs(step.frame, kind)[0];
  if (!pair) return;
  $('previewFixups').checked = true; $('previewScale').checked = true;
  const actual = landmarkActorPoint(step.frame, 'restored', pair.restored);
  const offset = [...frameFixup(step.frame).offset_px];
  offset[axis] += Math.round(tier() * (pair.original[axis] - actual[axis]));
  if (Math.abs(offset[axis]) > 16384) { headActionStatus('Adjustment exceeds the offset range.'); return; }
  changeFrame(step.frame, {offset_px: offset});
  headActionStatus(`Restored ${axis === 0 ? 'X' : 'Y'} aligned to original ${kind === 'head' ? 'head X' : 'head top'}.`);
  return true;
}

function headTopBottomFit(nativeTop, nativeBottom, restoredTop, restoredBottom) {
  const originalSpan = nativeBottom - nativeTop, restoredSpan = restoredBottom - restoredTop;
  if (![nativeTop, nativeBottom, restoredTop, restoredBottom].every(Number.isFinite) ||
      originalSpan <= 1 || restoredSpan <= 1) throw new Error('Need a head top above both bottom lines.');
  const scale = originalSpan / restoredSpan;
  if (scale < .5 || scale > 1.5) throw new Error('Head-to-bottom fit exceeds the allowed size range.');
  return {scale, offsetY: nativeBottom - restoredBottom};
}

function fitHeadTopToBottom(remember = true) {
  const step = headActionStep();
  const pair = step && landmarkPairs(step.frame, 'head_top')[0];
  if (!pair) return;
  const nativeBounds = nativeHeightBounds(state.manifest, step.frame);
  const bounds = state.manifest.review_restored_bounds[step.frame];
  if (!nativeBounds || !bounds) return;
  try {
    $('previewFixups').checked = true; $('previewScale').checked = true;
    const frame = state.manifest.frames[step.frame], old = frameFixup(step.frame);
    const restoredBottom = (frame.crop_origin_px[1] + bounds[3]) / tier();
    const fit = headTopBottomFit(pair.original[1], nativeBounds[1], pair.restored[1], restoredBottom);
    const head = landmarkPoint(step.frame, 'restored', 'head')?.xy || pair.restored;
    const oldX = landmarkActorPoint(step.frame, 'restored', head)[0];
    const geometry = restoredGeometry(step.frame, fit.scale, 'bottom');
    const newX = geometry.x / tier() + fit.scale * (head[0] - frame.crop_origin_px[0] / tier());
    const offset = [old.offset_px[0] + Math.round((oldX - newX) * tier()), Math.round(fit.offsetY * tier())];
    if (offset.some(value => Math.abs(value) > 16384)) throw new Error('Adjustment exceeds the offset range.');
    changeFrame(step.frame, {scale_factor: fit.scale, scale_anchor: 'bottom', offset_px: offset}, remember);
    headActionStatus(`Size ${((fit.scale - 1) * 100).toFixed(3)}% · head top and original bottom matched. Head X retained.`);
    return true;
  } catch (error) { headActionStatus(error.message); }
}

function alignHeadAndFit() {
  const step = headActionStep();
  if (!step) return;
  const canAlign = landmarkPairs(step.frame, 'head').length > 0;
  const canFit = landmarkPairs(step.frame, 'head_top').length > 0 &&
    nativeHeightBounds(state.manifest, step.frame) && state.manifest.review_restored_bounds[step.frame];
  if (!canAlign && !canFit) { headActionStatus('No paired head X or head-top references for this frame.'); return; }
  const messages = [];
  let aligned = false;
  if (canAlign) {
    aligned = alignLandmarkAxis('head', 0);
    messages.push($('landmarkActionStatus').textContent);
  }
  if (canFit) {
    fitHeadTopToBottom(!aligned);
    messages.push($('landmarkActionStatus').textContent);
  }
  headActionStatus(messages.join(' '));
}

function changeLandmark(name, side, kind, point, remember = true, reset = false) {
  state.fixups.landmarks ||= {};
  if (remember) {
    landmarkUndo.push({family: currentFamily().id, name, before: structuredClone(state.fixups.landmarks[name] || {})});
    if (landmarkUndo.length > 200) landmarkUndo.shift();
  }
  state.fixups.landmarks[name] ||= {};
  state.fixups.landmarks[name][side] ||= {};
  if (reset) delete state.fixups.landmarks[name][side][kind];
  else state.fixups.landmarks[name][side][kind] = point;
  markDirty(); renderStage();
}

function landmarkPairs(name, selected = null) {
  const pairs = [];
  for (const kind of selected ? [selected] : Object.keys(landmarkColors)) {
    const original = landmarkPoint(name, 'original', kind)?.xy;
    const restored = landmarkPoint(name, 'restored', kind)?.xy;
    if (original && restored) pairs.push({kind, original, restored});
  }
  return pairs;
}

function fitLandmarkPairs(pairs) {
  // Least squares for one uniform scale and two translations. Head contributes X
  // only. Missing coordinates never become zero or infer a hidden second eye.
  const axes = [0, 1].map(axis => pairs.filter(pair => pair.original[axis] !== null && pair.restored[axis] !== null));
  const means = axes.map((items, axis) => items.length ? [
    items.reduce((sum, pair) => sum + pair.restored[axis], 0) / items.length,
    items.reduce((sum, pair) => sum + pair.original[axis], 0) / items.length] : null);
  let covariance = 0, variance = 0;
  axes.forEach((items, axis) => items.forEach(pair => {
    const r = pair.restored[axis] - means[axis][0], n = pair.original[axis] - means[axis][1];
    covariance += r * n; variance += r * r;
  }));
  // Avoid unstable size changes based only on a close eye pair or almost identical points.
  if (variance < 16 || axes[1].length < 2) throw new Error('Need at least two separated 2D landmarks to fit size.');
  const scale = covariance / variance;
  if (!Number.isFinite(scale) || scale < .5 || scale > 1.5) throw new Error('Landmark fit exceeds the allowed size range.');
  const translation = means.map(mean => mean ? mean[1] - scale * mean[0] : 0);
  let squares = 0, count = 0;
  axes.forEach((items, axis) => items.forEach(pair => {
    squares += (scale * pair.restored[axis] + translation[axis] - pair.original[axis]) ** 2; count++;
  }));
  return {scale, translation, residual: Math.sqrt(squares / count)};
}

function applyLandmarkAlignment(fitSize) {
  if (!state.manifest || state.switching || $('play').disabled) return;
  const step = currentStep();
  if (!step) return;
  pauseForEdit();
  $('previewFixups').checked = true; $('previewScale').checked = true;
  const pairs = landmarkPairs(step.frame, fitSize ? null : $('landmarkKind').value);
  if (!pairs.length) { message('This point must be visible on both sprites to align it.', true); return; }
  try {
    const old = frameFixup(step.frame);
    let factor = old.scale_factor, delta;
    let residual = 0;
    if (fitSize) {
      const fit = fitLandmarkPairs(pairs); factor = fit.scale; residual = fit.residual;
      const geometry = restoredGeometry(step.frame, factor);
      const crop = state.manifest.frames[step.frame].crop_origin_px;
      delta = fit.translation.map((value, i) =>
        (factor * crop[i] / tier() + value) * tier() - (i === 0 ? geometry.x : geometry.y));
    } else {
      const pair = pairs[0], actual = landmarkActorPoint(step.frame, 'restored', pair.restored);
      delta = actual.map((value, i) => value === null ? 0 : tier() * (pair.original[i] - value));
    }
    changeFrame(step.frame, {scale_factor: factor,
      offset_px: old.offset_px.map((value, i) => value + Math.round(delta[i]))});
    message(`${fitSize ? 'Size and offset' : 'Offset'} proposal applied to ${step.frame}` +
      (fitSize ? ` · RMS point residual ${residual.toFixed(2)} original px.` : '.'));
  } catch (error) { message(error.message, true); }
}

function bindLandmarks() {
  $('headCenterGuide').onclick = () => moveGuideToLandmark('head', 0);
  $('headAlignX').onclick = () => alignLandmarkAxis('head', 0);
  $('headTopGuide').onclick = () => moveGuideToLandmark('head_top', 1);
  $('headAlignY').onclick = () => alignLandmarkAxis('head_top', 1);
  $('headFitFeet').onclick = () => fitHeadTopToBottom();
  $('landmarkUndoPlacement').onclick = () => {
    const step = headActionStep(), stack = step && state.undo.get(step.frame);
    if (!stack?.length) return;
    changeFrame(step.frame, stack.pop(), false);
    headActionStatus('Sprite adjustment undone.');
  };
  $('landmarkUndoGuide').onclick = () => {
    if (!headActionStep() || !state.guideUndo.length) return;
    state.fixups.guides = state.guideUndo.pop(); markDirty(); renderStage();
    headActionStatus('Guide adjustment undone.');
  };
  $('editHeadTop').onclick = () => {
    if (!headActionStep()) return;
    $('landmarkPanel').open = true;
    $('landmarkKind').value = 'head_top'; $('editLandmarks').checked = true;
    $('editLandmarks').onchange();
    headActionStatus('Click the head top on each sprite. Arrows refine the selected point.');
  };
  for (const id of ['showLandmarks', 'landmarkKind', 'landmarkSide']) $(id).onchange = renderStage;
  $('editLandmarks').onchange = () => {
    if ($('editLandmarks').checked) { pauseForEdit(); $('showLandmarks').checked = true; }
    for (const id of ['native', 'restored']) $(id).style.cursor = $('editLandmarks').checked ? 'crosshair' : '';
    renderStage();
  };
  const edit = operation => {
    if (!state.manifest || state.switching || !currentStep()) return;
    pauseForEdit();
    operation(currentStep().frame, $('landmarkSide').value, $('landmarkKind').value);
  };
  $('landmarkKeep').onclick = () => edit((name, side, kind) => {
    const point = landmarkPoint(name, side, kind);
    if (point?.xy) changeLandmark(name, side, kind, [...point.xy]);
  });
  $('landmarkAbsent').onclick = () => edit((name, side, kind) => changeLandmark(name, side, kind, null));
  $('landmarkReset').onclick = () => edit((name, side, kind) => changeLandmark(name, side, kind, null, true, true));
  $('landmarkUndo').onclick = () => {
    if (!state.manifest || state.switching) return;
    const index = landmarkUndo.findLastIndex(item => item.family === currentFamily().id);
    if (index < 0) return;
    const item = landmarkUndo.splice(index, 1)[0];
    state.fixups.landmarks[item.name] = item.before; markDirty(); renderStage();
  };
  $('landmarkAlign').onclick = () => applyLandmarkAlignment(false);
  $('landmarkFit').onclick = () => applyLandmarkAlignment(true);
  $('exportLandmarks').onclick = async event => {
    event.preventDefault();
    try { await flushFixups(); location.href = '/api/landmarks/export'; }
    catch (error) { message(error.message, true); }
  };
  for (const side of ['original', 'restored']) {
    const canvas = $(side === 'original' ? 'native' : 'restored');
    canvas.addEventListener('pointerdown', event => {
      if (!$('editLandmarks').checked || event.button !== 0 || !state.manifest || state.switching) return;
      const step = currentStep(); if (!step) return;
      event.preventDefault(); event.stopImmediatePropagation(); pauseForEdit(); canvas.focus({preventScroll: true});
      $('landmarkSide').value = side;
      landmarkDrag = {pointer: event.pointerId, side, step, kind: $('landmarkKind').value};
      changeLandmark(step.frame, side, landmarkDrag.kind, landmarkFromPointer(event, canvas, step, side));
      canvas.setPointerCapture(event.pointerId);
    }, true);
    canvas.addEventListener('pointermove', event => {
      if (!$('editLandmarks').checked) return;
      event.stopImmediatePropagation(); canvas.style.cursor = 'crosshair';
      if (landmarkDrag?.pointer !== event.pointerId || landmarkDrag.side !== side) return;
      changeLandmark(landmarkDrag.step.frame, side, landmarkDrag.kind,
        landmarkFromPointer(event, canvas, landmarkDrag.step, side), false);
    }, true);
    for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, event => {
      if (!landmarkDrag || landmarkDrag.side !== side) return;
      event.stopImmediatePropagation(); landmarkDrag = null; flushFixups().catch(() => {});
    }, true);
  }
  window.addEventListener('keydown', event => {
    if (!state.manifest || state.switching || !$('editLandmarks').checked ||
        event.ctrlKey || event.metaKey || event.altKey ||
        (event.shiftKey && ['ArrowLeft', 'ArrowRight'].includes(event.key)) ||
        !['native', 'restored'].includes(document.activeElement?.id) ||
        !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key) || !currentStep()) return;
    event.preventDefault(); event.stopImmediatePropagation(); pauseForEdit();
    const step = currentStep(), side = document.activeElement.id === 'native' ? 'original' : 'restored';
    const kind = $('landmarkKind').value, current = landmarkPoint(step.frame, side, kind);
    if (!current?.xy) return;
    const axis = ['ArrowLeft', 'ArrowRight'].includes(event.key) ? 0 : 1;
    if (kind === 'head' && axis === 1) return;
    const sign = (['ArrowLeft', 'ArrowUp'].includes(event.key) ? -1 : 1) *
      (axis === 0 && step.mirrored ? -1 : 1);
    const point = [...current.xy];
    point[axis] += sign * ($('nudgeStep').value === 'native' ? 1 : 1 / tier()) * (event.shiftKey ? 10 : 1);
    changeLandmark(step.frame, side, kind, point);
  }, true);
}

document.addEventListener('DOMContentLoaded', bindLandmarks);
