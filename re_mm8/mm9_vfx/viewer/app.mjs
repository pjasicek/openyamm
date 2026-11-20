import {Simulation, properties, assetName} from './simulation.mjs';
import {Renderer} from './render.mjs';

const $ = id => document.getElementById(id);
const models = new Map(), audioBuffers = new Map(), activeSounds = new Map();
let catalog, renderer, sim, selected, playing = true, loading = false, revision = 0, accumulator = 0;
let audio = null, master = null, warnings = [], lastClock = performance.now(), endWait = 0;
const pretty = name => catalog?.effects.find(e => e.name === name)?.display_name ?? name.replace(/^fg spell-/, '').replace(/^spell-/, '').replace(/\b\w/g, c => c.toUpperCase());

function showWarning()
{
    $('warning').hidden = !warnings.length;
    $('warning').textContent = [...new Set(warnings)].join('\n');
}
function stopSounds()
{
    for (const source of activeSounds.values()) { try { source.stop(); } catch {} }
    activeSounds.clear();
}
async function enableSound()
{
    if (!audio)
    {
        audio = new AudioContext(); master = audio.createGain(); master.connect(audio.destination);
    }
    await audio.resume(); master.gain.value = Number($('volume').value);
}
async function preloadSound(name)
{
    if (audioBuffers.has(name)) return;
    const response = await fetch('/api/sound?name='+encodeURIComponent(name));
    if (!response.ok) throw new Error('Sound unavailable: '+name);
    audioBuffers.set(name, await response.arrayBuffer());
}
async function startSound(c)
{
    if (!$('sound').checked || !audio || audio.state !== 'running' || !playing) return;
    const token = revision, name = assetName(c.p.Sound), currentSim = sim;
    let data = audioBuffers.get(name);
    if (!data) return;
    if (data instanceof ArrayBuffer)
    {
        try { data = await audio.decodeAudioData(data.slice(0)); audioBuffers.set(name, data); }
        catch { warnings.push('This browser could not decode '+name); showWarning(); return; }
    }
    if (revision !== token || sim !== currentSim || !c.active || !playing || !$('sound').checked) return;
    const elapsed = Math.max(0, sim.time-c.born);
    if (!c.p.Loop && elapsed >= data.duration) return;
    const source = audio.createBufferSource(), gain = audio.createGain();
    source.buffer = data; source.loop = Boolean(c.p.Loop);
    source.playbackRate.value = (c.p.PitchShift ?? 1)*Number($('speed').value);
    gain.gain.value = (c.p.Volume ?? 100)/100;
    source.connect(gain); gain.connect(master);
    if (activeSounds.has(c.key.id)) { try { activeSounds.get(c.key.id).stop(); } catch {} }
    activeSounds.set(c.key.id, source);
    source.onended = () => { if (activeSounds.get(c.key.id) === source) activeSounds.delete(c.key.id); };
    source.start(0, elapsed % data.duration);
}
function audioEvents()
{
    for (const event of sim.soundEvents.splice(0))
    {
        if (event.kind === 'start') void startSound(event.c);
        else if (activeSounds.has(event.c.key.id))
        {
            try { activeSounds.get(event.c.key.id).stop(); } catch {}
            activeSounds.delete(event.c.key.id);
        }
    }
}
async function getModel(name)
{
    if (models.has(name)) return;
    const response = await fetch('/api/model?name='+encodeURIComponent(name));
    if (!response.ok) throw new Error('Model unavailable: '+name);
    models.set(name, await response.json());
}
function newSimulation()
{
    stopSounds(); accumulator = endWait = 0;
    sim = new Simulation(selected, models, {detail: Number($('detail').value), seed: 9,
        target: $('monk').checked ? models.get('models/monk.abc') : null});
    $('timeline').max = sim.duration;
    audioEvents();
}
function replay()
{
    if (!selected || loading) return;
    playing = true; $('pause').textContent = 'Pause'; newSimulation();
}
function togglePause()
{
    if (!sim || loading) return;
    playing = !playing; $('pause').textContent = playing ? 'Pause' : 'Play';
    accumulator = 0; stopSounds();
    if (playing) for (const c of sim.components) if (c.active && c.type === 'PlaySound') void startSound(c);
}
function drawList()
{
    const query = $('search').value.toLowerCase(), list = $('effects');
    list.replaceChildren();
    const matches = catalog.effects.filter(e => `${e.display_name ?? ''} ${e.name}`.toLowerCase().includes(query));
    $('count').textContent = `${matches.length} / ${catalog.effects.length}`;
    for (const effect of [...matches].sort((a, b) =>
        Number(b.source === 'authored') - Number(a.source === 'authored')
        || pretty(a.name).localeCompare(pretty(b.name))))
    {
        const button = document.createElement('button');
        button.textContent = pretty(effect.name);
        button.classList.toggle('active', selected?.name === effect.name);
        button.setAttribute('aria-pressed', String(selected?.name === effect.name));
        button.dataset.effect = effect.name;
        const small = document.createElement('small');
        small.textContent = `${effect.source === 'authored' ? 'OpenYAMM · ' : 'MM9 · '}`
            + `${effect.keys.length} layers · ${(effect.phase_ms/1000).toFixed(1)} s`;
        button.append(small);
        button.onclick = () => { void selectEffect(effect); };
        list.append(button);
    }
}
function details()
{
    $('summary').textContent = `${selected.keys.length} layers · ${selected.source === 'authored' ? 'OpenYAMM showcase' : 'MM9 source assets'}`;
    $('fidelity').textContent = selected.source === 'authored'
        ? 'Original effect recipes with CC0 artwork. Preview reads the same definitions and textures as the game. Lighting and particle placement may differ.'
        : 'Preview using recovered MM9 timing, emission and transparency rules. Original-game rendering parity is still being investigated.';
    const table = document.createElement('table');
    const row = document.createElement('tr');
    for (const text of ['Key', 'Component', 'Start', 'End', 'Asset'])
    {
        const th = document.createElement('th'); th.textContent = text; row.append(th);
    }
    table.append(row);
    for (const key of selected.keys)
    {
        const p = properties(key), tr = document.createElement('tr');
        for (const text of [key.id, key.component_ref, key.start.toFixed(3), key.end.toFixed(3),
            (assetName(p.Sprite ?? p.Model ?? p.Sound) ?? '—').split('/').at(-1)])
        {
            const td = document.createElement('td'); td.textContent = text; tr.append(td);
        }
        table.append(tr);
    }
    $('components').replaceChildren(table);
}
async function selectEffect(effect)
{
    const token = ++revision;
    const sourceChanged = selected?.source !== effect.source || !selected;
    selected = effect; loading = true; stopSounds();
    if (sourceChanged)
    {
        renderer.resetCamera();
        if (effect.source === 'authored') { renderer.distance = 180; renderer.target = [0, 30, 0]; renderer.pitch = .25; }
    }
    $('detail').disabled = effect.source === 'authored';
    $('loading').hidden = false; $('loading').textContent = 'Loading '+pretty(effect.name)+'…';
    $('title').textContent = pretty(effect.name);
    $('category').textContent = effect.source === 'authored' ? 'OPENYAMM SHOWCASE'
        : effect.name.includes('spell') || effect.name === 'elemental blast' ? 'SPELL EFFECT' : 'SPECIAL EFFECT';
    warnings = [...catalog.problems[effect.name]]; showWarning(); drawList(); details();
    const textures = new Set(), jobs = [];
    const missing = new Set(warnings.map(w => w.replace('Missing asset: ', '')));
    for (const key of effect.keys)
    {
        const p = properties(key), sprite = catalog.sprites[assetName(p.Sprite)];
        if (sprite) for (const frame of sprite.frames) textures.add(frame);
        const skin = assetName(p.Skin), model = assetName(p.Model), sound = assetName(p.Sound);
        if (skin && !missing.has(skin)) textures.add(skin);
        if (model && !missing.has(model)) jobs.push(() => getModel(model));
        if (sound) jobs.push(() => preloadSound(sound));
    }
    if ($('monk').checked)
    {
        jobs.push(() => getModel('models/monk.abc')); textures.add('skins/monk1.dtx');
    }
    for (const texture of textures) if (!renderer.textures.has(texture)) jobs.push(() => renderer.loadTexture(texture));
    let next = 0;
    await Promise.all(Array.from({length: Math.min(6, jobs.length)}, async () =>
    {
        while (next < jobs.length)
        {
            const job = jobs[next++];
            try { await job(); }
            catch (error) { if (token === revision) warnings.push(error.message); }
        }
    }));
    if (token !== revision) return;
    loading = false; playing = true;
    $('loading').hidden = true; $('pause').textContent = 'Pause'; showWarning();
    newSimulation();
    history.replaceState(null, '', '?effect='+encodeURIComponent(effect.name)+(!$('monk').checked ? '&target=off' : ''));
}
function seek(time)
{
    if (!sim || loading) return;
    newSimulation();
    const dt = 1/Number($('fps').value), steps = Math.floor(Math.min(time, sim.duration)/dt);
    for (let i = 0; i < steps; ++i) sim.advance(dt);
    sim.soundEvents.length = 0; stopSounds(); playing = false; $('pause').textContent = 'Play';
    render();
}
function render()
{
    renderer.render(sim, catalog.sprites, {grid: $('grid').checked, monk: $('monk').checked,
        helpers: $('helpers').checked, background: $('background').value});
    if (!sim) return;
    $('timeline').value = sim.time;
    $('time').textContent = `${Math.min(sim.time, sim.duration).toFixed(2)} / ${sim.duration.toFixed(2)} s`;
    $('stats').textContent = `${sim.particleCount} particles · ${sim.components.filter(c => c.active).length} layers`;
    $('status').textContent = loading ? 'Loading' : sim.finished ? 'Finished' : playing ? 'Playing' : 'Paused';
}
function frame(clock)
{
    const elapsed = Math.min((clock-lastClock)/1000, .25); lastClock = clock;
    if (sim && playing && !loading)
    {
        if (sim.finished)
        {
            endWait += elapsed;
            if ($('repeat').checked && endWait > .6) newSimulation();
        }
        else
        {
            const dt = 1/Number($('fps').value);
            accumulator += elapsed*Number($('speed').value);
            while (accumulator >= dt) { sim.advance(dt); accumulator -= dt; }
            audioEvents();
        }
    }
    render(); requestAnimationFrame(frame);
}
async function boot()
{
    renderer = new Renderer($('canvas'));
    const response = await fetch('/api/catalog');
    if (!response.ok) throw new Error('Could not read the effects catalog.');
    catalog = await response.json();
    $('search').oninput = drawList;
    $('replay').onclick = replay; $('pause').onclick = togglePause;
    $('resetCamera').onclick = () => {
        renderer.resetCamera();
        if (selected?.source === 'authored') { renderer.distance = 180; renderer.target = [0, 30, 0]; renderer.pitch = .25; }
    };
    $('timeline').oninput = () => seek(Number($('timeline').value));
    $('fps').onchange = replay; $('detail').onchange = replay;
    $('monk').onchange = () => { void selectEffect(selected); };
    $('sound').onchange = async () =>
    {
        if ($('sound').checked) { await enableSound(); replay(); } else stopSounds();
    };
    $('volume').oninput = () => { if (master) master.gain.value = Number($('volume').value); };
    $('speed').onchange = () =>
    {
        stopSounds();
        for (const c of sim.components) if (c.active && c.type === 'PlaySound') void startSound(c);
    };
    document.addEventListener('keydown', event =>
    {
        if (['INPUT', 'SELECT', 'BUTTON'].includes(event.target.tagName)) return;
        if (event.code === 'Space') { event.preventDefault(); togglePause(); }
        if (event.code === 'KeyR') replay();
    });
    document.addEventListener('visibilitychange', () =>
    {
        if (document.hidden && playing) togglePause();
    });
    const params = new URLSearchParams(location.search);
    if (params.get('target') === 'off') $('monk').checked = false;
    await selectEffect(catalog.effects.find(e => e.name === params.get('effect'))
        ?? catalog.effects.find(e => e.name === 'spell-column of fire'));
    if (params.has('time')) seek(Number(params.get('time')));
    // Small deterministic inspection surface used by browser smoke tests.
    window.fxViewer = {select: async name => selectEffect(catalog.effects.find(e => e.name === name)), seek,
        state: () => ({effect: selected.name, time: sim.time, particles: sim.particleCount, playing, loading,
            warnings, glError: renderer.gl.getError(), textures: renderer.textures.size}),
        catalog: () => catalog, activeSounds: () => activeSounds.size};
    lastClock = performance.now(); requestAnimationFrame(frame);
}
boot().catch(error => { $('loading').textContent = error.message; console.error(error); });
