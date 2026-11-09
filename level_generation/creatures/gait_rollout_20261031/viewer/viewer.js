// Composite viewer of the 2026-10-31 gait rollout: every changed MM6-MM8 model, its old and new walk/run/sprint
// clips side by side on a treadmill moving at the bound stride, and the in-game playback rates before and after.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const ROOT = '../../../../assets_source/';
const $ = (id) => document.getElementById(id);
const state = {
  models: [], filtered: [], current: null, group: 0, playing: true, speed: 1, sync: false, tread: true,
  showOld: true, view: 'side', world: 'all', kind: 'all', tiles: [], loadToken: 0, gltf: null, attachments: [],
};

const renderer = new THREE.WebGLRenderer({canvas: $('canvas'), antialias: true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setScissorTest(true);
renderer.outputColorSpace = THREE.SRGBColorSpace;
const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 1000);
const controls = new OrbitControls(camera, $('stage'));
controls.enableDamping = true;
let frame = {height: 1, depth: 0, center: new THREE.Vector3()};

// ---- model list -------------------------------------------------------------------------------------------------

function kinds(model) {
  const result = new Set();
  for (const group of model.groups) {
    const {old, new: now} = group;
    if (now.sprint && now.sprint !== old.sprint) result.add('sprint');
    if (now.run !== old.run || now.run_stride_length !== old.run_stride_length) result.add('run');
    if (now.walk !== old.walk || now.stride_length !== old.stride_length) result.add('walk');
  }
  if (!Object.values(model.clips).some((clip) => clip.new)) result.add('binding');
  return result;
}

function newClips(model) {
  return Object.entries(model.clips).filter(([, clip]) => clip.new).map(([name]) => name);
}

function buildChips() {
  const make = (box, values, key) => {
    box.innerHTML = '';
    for (const [value, label] of values) {
      const chip = document.createElement('span');
      chip.className = 'chip' + (state[key] === value ? ' on' : '');
      chip.textContent = label;
      chip.onclick = () => { state[key] = value; buildChips(); filterList(); };
      box.appendChild(chip);
    }
  };
  make($('worldChips'), [['all', 'All worlds'], ['mm6', 'MM6'], ['mm7', 'MM7'], ['mm8', 'MM8']], 'world');
  make($('kindChips'), [['all', 'Any change'], ['sprint', 'Sprint'], ['run', 'Run'], ['walk', 'Walk'],
    ['binding', 'Binding only']], 'kind');
}

function filterList() {
  const query = $('search').value.trim().toLowerCase();
  state.filtered = state.models.filter((model) => {
    if (state.world !== 'all' && !model.worlds.includes(state.world)) return false;
    if (state.kind !== 'all' && !model.kinds.has(state.kind)) return false;
    if (!query) return true;
    const text = [model.label, model.id, model.packages.join(' '), model.worlds.join(' '),
      model.tiers.map((t) => t.descriptor).join(' ')].join(' ').toLowerCase();
    return text.includes(query);
  });
  const list = $('list');
  list.innerHTML = '';
  for (const model of state.filtered) {
    const item = document.createElement('div');
    item.className = 'item' + (state.current === model ? ' sel' : '');
    const clips = newClips(model);
    item.innerHTML = `<div class="name">${model.label}</div>
      <div class="meta">${model.worlds.join('+').toUpperCase()} · ${model.id} · ${model.packages.join(', ')}</div>
      <div>${clips.length ? clips.map((c) => `<span class="badge">${c}</span>`).join('')
        : '<span class="badge b">binding only</span>'}</div>`;
    item.onclick = () => select(model);
    model.element = item;
    list.appendChild(item);
  }
  $('count').textContent = `${state.filtered.length} of ${state.models.length} models`;
}

// ---- tiles ------------------------------------------------------------------------------------------------------

function tilesFor(model, group) {
  const {old, new: now} = group;
  const tiles = [];
  const add = (role, clip, stride, status) => {
    if (!clip || !model.clips[clip]) return;
    const same = tiles.find((t) => t.clip === clip && Math.abs(t.stride - stride) < 1e-6);
    if (same) {
      if (!same.roles.includes(role)) same.roles.push(role);
      if (status === 'new') same.status = 'new';
      return;
    }
    tiles.push({clip, stride, roles: [role], status, duration: model.clips[clip].duration});
  };
  const runStride = (b) => b.run_stride_length ?? b.stride_length * 1.55;
  const statusOf = (clip, changed) => (model.clips[clip]?.new || changed ? 'new' : 'same');
  if (old.walk === now.walk) {
    add('walk', now.walk, now.stride_length, statusOf(now.walk, old.stride_length !== now.stride_length));
  } else {
    add('walk', now.walk, now.stride_length, statusOf(now.walk, true));
  }
  if (old.run === now.run) {
    add('run', now.run, runStride(now), statusOf(now.run, runStride(old) !== runStride(now)));
  } else {
    add('run', now.run, runStride(now), statusOf(now.run, true));
  }
  if (now.sprint) add('sprint', now.sprint, now.sprint_stride_length, statusOf(now.sprint, now.sprint !== old.sprint));
  if (old.walk !== now.walk) add('walk', old.walk, old.stride_length, 'old');
  if (old.run !== now.run) add('run', old.run, runStride(old), 'old');
  if (old.sprint && old.sprint !== now.sprint) add('sprint', old.sprint, old.sprint_stride_length, 'old');
  return tiles;
}

function disposeModel() {
  for (const tile of state.tiles) tile.scene = null;
  state.tiles = [];
  for (const gltf of [state.gltf, ...state.attachments]) {
    gltf?.scene.traverse((object) => {
      object.geometry?.dispose();
      for (const material of [].concat(object.material || [])) {
        for (const value of Object.values(material)) if (value?.isTexture) value.dispose();
        material.dispose();
      }
    });
  }
  state.gltf = null;
  state.attachments = [];
}

function makeScene(tile, gltf, attachments, model) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(tile.status === 'old' ? 0x2a2620 : tile.status === 'new' ? 0x1f2a24 : 0x22252a);
  scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x3a3328, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(3, 6, 4);
  scene.add(sun);
  const body = SkeletonUtils.clone(gltf.scene);
  body.traverse((object) => {
    if (object.isMesh && /LOD[1-9]|Shadow/i.test(object.name)) object.visible = false;
    if (object.isMesh) object.frustumCulled = false;
  });
  for (const [index, attachment] of attachments.entries()) {
    const bone = body.getObjectByName(model.attachments[index].node);
    if (bone) bone.add(attachment.scene.clone(true));
  }
  scene.add(body);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({color: 0x15171a, transparent: true, opacity: 0.55}));
  floor.rotation.x = -Math.PI / 2;
  floor.scale.setScalar(frame.height * 6);
  scene.add(floor);
  const cell = frame.height / 4;
  const grid = new THREE.GridHelper(cell * 24, 24, 0x5a6270, 0x3a4048);
  grid.position.y = 0.001;
  scene.add(grid);
  const mixer = new THREE.AnimationMixer(body);
  const clip = gltf.animations.find((a) => a.name === tile.clip);
  const action = mixer.clipAction(clip);
  action.play();
  Object.assign(tile, {scene, body, mixer, action, grid, cell, acc: 0});
}

function frameModel(gltf) {
  const probe = SkeletonUtils.clone(gltf.scene);
  probe.traverse((object) => { if (object.isMesh && /LOD[1-9]|Shadow/i.test(object.name)) object.visible = false; });
  const box = new THREE.Box3();
  probe.updateMatrixWorld(true);
  probe.traverse((object) => {
    if (!object.isMesh || !object.visible) return;
    // A skinned mesh's bounds in its rest pose (bind-pose geometry can be in another scale than the posed body).
    if (object.isSkinnedMesh) {
      object.skeleton.update();
      object.computeBoundingBox();
      box.union(object.boundingBox.clone().applyMatrix4(object.matrixWorld));
    } else {
      object.geometry.computeBoundingBox();
      box.union(object.geometry.boundingBox.clone().applyMatrix4(object.matrixWorld));
    }
  });
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  // Extent the camera has to fit: the height, or the body's length for long four-legged bodies.
  frame.height = Math.max(size.y, size.z * 0.85, size.x * 0.85, 0.2);
  frame.center.set(center.x, Math.max(size.y, 0.2) * 0.5, center.z);
  // Legs spread toward the camera (spiders) come nearer: keep half the body's depth out of the framing distance.
  frame.depth = Math.max(size.x, size.z) * 0.5;
}

function applyView() {
  const distance = frame.height * 2.3 + frame.depth;
  const directions = {side: [1, 0.12, 0], quarter: [0.75, 0.2, 0.65], front: [0, 0.12, 1], back: [0, 0.15, -1]};
  const [x, y, z] = directions[state.view];
  camera.position.set(x, y, z).normalize().multiplyScalar(distance).add(frame.center);
  controls.target.copy(frame.center);
  camera.near = frame.height / 100;
  camera.far = frame.height * 100;
  camera.updateProjectionMatrix();
  controls.update();
}

function layoutTiles() {
  const box = $('tiles');
  box.innerHTML = '';
  const visible = state.tiles.filter((tile) => state.showOld || tile.status !== 'old');
  const columns = visible.length <= 3 ? Math.max(visible.length, 1) : Math.ceil(visible.length / 2);
  box.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
  box.style.gridTemplateRows = `repeat(${Math.ceil(visible.length / columns) || 1}, 1fr)`;
  for (const tile of state.tiles) tile.element = null;
  for (const tile of visible) {
    const element = document.createElement('div');
    element.className = `tile ${tile.status}`;
    const speed = tile.stride / tile.duration;
    const tag = {new: 'new', old: 'replaced', same: 'unchanged'}[tile.status];
    element.innerHTML = `<div class="lab"><b>${tile.clip}</b><span class="tag ${tile.status}">${tag}</span><br>
      ${tile.roles.join(' + ')} · ${tile.duration.toFixed(2)} s · stride ${tile.stride.toFixed(3)}
      · ${speed.toFixed(2)} u/s</div>`;
    box.appendChild(element);
    tile.element = element;
  }
}

// ---- selection --------------------------------------------------------------------------------------------------

async function select(model, groupIndex = 0) {
  state.current = model;
  state.group = groupIndex;
  location.hash = model.id;
  for (const item of $('list').children) item.classList.remove('sel');
  model.element?.classList.add('sel');
  model.element?.scrollIntoView({block: 'nearest'});
  const group = model.groups[groupIndex];
  $('title').textContent = `${model.label} — ${model.id}`;
  $('sub').textContent = `${model.worlds.join(' + ').toUpperCase()} · ${model.packages.join(', ')} · ` +
    `${group.descriptors.join(', ')}` +
    (model.packages.some((p) => /^[hq]\d/.test(p)) ? ` · notes: gait_rollout_20261031/${model.packages
      .find((p) => /^[hq]\d/.test(p))}/README.md` : '');
  const groupSelect = $('group');
  groupSelect.innerHTML = model.groups.map((g, i) =>
    `<option value="${i}">${g.descriptors.map((d) => d.split(': ')[1]).join(', ')}</option>`).join('');
  groupSelect.value = String(groupIndex);
  $('groupBox').style.display = model.groups.length > 1 ? '' : 'none';
  renderRates(model);
  const token = ++state.loadToken;
  $('loading').textContent = 'Loading…';
  const loader = new GLTFLoader();
  try {
    const gltf = state.gltf?.userData.path === model.path ? state.gltf : await loader.loadAsync(ROOT + model.path);
    const attachments = state.gltf === gltf ? state.attachments
      : await Promise.all(model.attachments.map((a) => loader.loadAsync(ROOT + a.path)));
    if (token !== state.loadToken) return;
    if (state.gltf !== gltf) {
      disposeModel();
      gltf.userData.path = model.path;
      state.gltf = gltf;
      state.attachments = attachments;
      frameModel(gltf);
      applyView();
    }
    state.tiles = tilesFor(model, group);
    for (const tile of state.tiles) makeScene(tile, gltf, attachments, model);
    layoutTiles();
    $('loading').textContent = '';
    document.body.dataset.loaded = model.id;
  } catch (error) {
    $('loading').textContent = `Could not load ${model.path}: ${error}`;
  }
}

function rateCell(value, old) {
  if (!value) return '<span class="dim">—</span>';
  const [clip, rate, slide] = value;
  const wanted = rate * slide;
  const cls = old ? 'dim' : slide > 1.005 ? 'bad' : rate < 0.75 || rate > 1.5 ? 'warn' : 'ok';
  // Before the rollout there was no playback ceiling: the old clip played at the full rate.
  return `<span class="${cls}">${clip} ×${wanted.toFixed(2)}${!old && slide > 1.005 ? ' slides' : ''}</span>`;
}

function renderRates(model) {
  const states = [['standard_wander', 'Standard wander'], ['standard_chase', 'Standard chase'],
    ['maw_wander', 'MAW wander'], ['maw_chase', 'MAW chase']];
  let html = `<tr><th>Tier</th>${states.map(([, label]) => `<th>${label}: old → new</th>`).join('')}</tr>`;
  for (const tier of model.tiers) {
    html += `<tr class="${tier.group === state.group ? 'cur' : ''}"><td>${tier.world.toUpperCase()} ${tier.descriptor}</td>`;
    for (const [key] of states) {
      const [before, after] = tier[key];
      html += `<td>${rateCell(before, true)}<span class="arrow">→</span>${rateCell(after, false)}</td>`;
    }
    html += '</tr>';
  }
  $('rates').innerHTML = html;
}

// ---- loop -------------------------------------------------------------------------------------------------------

let last = performance.now();
function tick(now = performance.now()) {
  requestAnimationFrame(tick);
  const dt = Math.min((now - last) / 1000, 0.1) * (state.playing ? state.speed : 0);
  last = now;
  const canvas = renderer.domElement;
  const width = canvas.clientWidth, height = canvas.clientHeight;
  if (canvas.width !== Math.floor(width * renderer.getPixelRatio())
      || canvas.height !== Math.floor(height * renderer.getPixelRatio())) {
    renderer.setSize(width, height, false);
  }
  renderer.setScissor(0, 0, width, height);
  renderer.setClearColor(0x16181c);
  renderer.clear();
  controls.update();
  const reference = state.tiles.find((t) => t.roles.includes('walk'))?.duration || 1;
  const stage = canvas.getBoundingClientRect();
  for (const tile of state.tiles) {
    if (!tile.scene) continue;
    tile.acc += dt / (state.sync ? reference : tile.duration);
    tile.mixer.setTime((tile.acc % 1) * tile.duration);
    const travel = state.tread ? tile.acc * tile.stride : 0;
    tile.grid.position.z = -(travel % tile.cell);
    if (!tile.element) continue;
    const rect = tile.element.getBoundingClientRect();
    const left = rect.left - stage.left, bottom = stage.bottom - rect.bottom;
    camera.aspect = rect.width / rect.height;
    camera.updateProjectionMatrix();
    renderer.setViewport(left, bottom, rect.width, rect.height);
    renderer.setScissor(left, bottom, rect.width, rect.height);
    renderer.render(tile.scene, camera);
  }
}

// ---- controls ---------------------------------------------------------------------------------------------------

function toggle(id, key, onLabel, offLabel) {
  $(id).onclick = () => {
    state[key] = !state[key];
    $(id).classList.toggle('on', state[key]);
    if (onLabel) $(id).textContent = state[key] ? onLabel : offLabel;
    if (key === 'showOld') layoutTiles();
    if (key === 'sync') for (const tile of state.tiles) tile.acc = 0;
  };
}
toggle('play', 'playing', 'Pause', 'Play');
toggle('sync', 'sync');
toggle('tread', 'tread');
toggle('showOld', 'showOld');
$('speed').onchange = (e) => { state.speed = Number(e.target.value); };
$('view').onchange = (e) => { state.view = e.target.value; applyView(); };
$('group').onchange = (e) => select(state.current, Number(e.target.value));
$('search').oninput = filterList;
window.addEventListener('keydown', (event) => {
  if (event.target.tagName === 'INPUT') return;
  if (event.code === 'Space') { event.preventDefault(); $('play').click(); }
  if (event.code === 'ArrowDown' || event.code === 'ArrowUp') {
    event.preventDefault();
    const index = state.filtered.indexOf(state.current) + (event.code === 'ArrowDown' ? 1 : -1);
    const next = state.filtered[Math.max(0, Math.min(state.filtered.length - 1, index))];
    if (next && next !== state.current) select(next);
  }
});

const manifest = await (await fetch('manifest.json')).json();
state.models = manifest.models.map((model) => ({...model, kinds: kinds(model)}));
buildChips();
filterList();
const initial = state.models.find((m) => m.id === location.hash.slice(1)) || state.filtered[0];
if (initial) select(initial);
window.addEventListener('hashchange', () => {
  const model = state.models.find((m) => m.id === location.hash.slice(1));
  if (model && model !== state.current) select(model);
});
tick();
