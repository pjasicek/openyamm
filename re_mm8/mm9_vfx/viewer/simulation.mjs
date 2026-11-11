import {add, sub, mul, unit, cross, mix, clamp, identity, matrixMultiply, transform,
    quaternionMatrix, slerp, axisRotate, directionMatrix} from './math.mjs';

export function properties(key)
{
    const result = {Ck: [], Sk: [], Mk: []};
    for (const p of key.properties)
    {
        if (['Ck', 'Sk', 'Mk'].includes(p.name)) result[p.name].push(p.value);
        else result[p.name] = p.type === 3 ? p.numeric_selection : p.value;
    }
    for (const name of ['Sk', 'Mk']) result[name].sort((a, b) => a[0] - b[0]);
    result.Ck.sort((a, b) => a.time - b.time);
    return result;
}
export function assetName(value)
{
    if (!value || value.endsWith('|...')) return null;
    return value.split('|')[1].replaceAll('\\', '/').toLowerCase();
}
export function sampleTrack(keys, phase, fallback)
{
    if (!keys.length) return [...fallback];
    if (phase <= keys[0][0]) return keys[0].slice(1);
    for (let i = 1; i < keys.length; ++i)
        if (phase < keys[i][0])
            return mix(keys[i-1].slice(1), keys[i].slice(1),
                (phase - keys[i-1][0]) / (keys[i][0] - keys[i-1][0]));
    return keys.at(-1).slice(1);
}
export function sampleColor(keys, phase, lifespan = null)
{
    if (!keys.length) return [1, 1, 1, 1];
    // Native particle helper compares normalized age with lifespan (not one).
    const sample = lifespan !== null && phase >= lifespan ? keys.at(-1).rgb_transparency
        : sampleTrack(keys.map(k => [k.time, ...k.rgb_transparency]), phase, [255, 255, 255, 0]);
    return [...sample.slice(0, 3).map(v => clamp(v/255, 0, 1)), clamp(1-sample[3]/255, 0, 1)];
}
export class Random
{
    constructor(seed) { this.state = seed >>> 0; }
    next() { this.state = (Math.imul(this.state, 214013) + 2531011) >>> 0; return (this.state >>> 16) & 32767; }
    signed() { return (this.next() % 20000 - 10000) / 10000; }
}
export function emissionSample(p, scalar, vector)
{
    const normal = unit(p.PlaneDir ?? [0, 1, 0]);
    const u = unit(cross(normal, Math.abs(normal[1]) > .99 ? [1, 0, 0] : [0, 1, 0]));
    const v = cross(normal, u), radius = p.Radius ?? 0, speed = p.Velocity ?? 0;
    const plane = () => add(mul(u, scalar()*radius), mul(v, scalar()*radius));
    let offset = [0, 0, 0], velocity = [0, 0, 0];
    switch (p.EmissionType ?? 0)
    {
        case 0: velocity = [scalar()*speed, scalar()*speed, scalar()*speed]; break;
        case 1: case 6: offset = plane(); velocity = mul(normal, speed); break;
        case 2: offset = mul(vector(), radius); velocity = mul(unit(offset, [0, 0, 0]), speed); break;
        case 3: case 4:
            offset = mul(unit(plane(), [0, 0, 0]), radius);
            velocity = mul(unit(offset, [0, 0, 0]), p.EmissionType === 3 ? -speed : speed); break;
        case 5: velocity = mul(unit(add(plane(), mul(normal, 100))), speed); break;
        default: throw new Error(`Unknown emission opcode ${p.EmissionType}`);
    }
    return {offset, velocity};
}
export function modelPose(model, time)
{
    if (!model) return null;
    const animation = model.animation;
    let frame = 0, next = 0, blend = 0;
    if (animation?.times.length > 1)
    {
        const times = animation.times, end = times.at(-1);
        const ms = end > 0 ? (time*1000) % end : 0;
        while (frame+1 < times.length && times[frame+1] <= ms) ++frame;
        next = Math.min(frame+1, times.length-1);
        blend = next === frame ? 0 : (ms-times[frame])/(times[next]-times[frame]);
    }
    const world = [], skin = [];
    for (let i = 0; i < model.nodes.length; ++i)
    {
        const node = model.nodes[i];
        let global = node.bind;
        if (animation?.times.length)
        {
            const a = animation.tracks[i][frame], b = animation.tracks[i][next];
            const local = quaternionMatrix(slerp(a.slice(3), b.slice(3), blend), mix(a.slice(0, 3), b.slice(0, 3), blend));
            global = node.parent >= 0 ? matrixMultiply(world[node.parent], local) : local;
        }
        world.push(global);
        skin[node.index] = matrixMultiply(global, node.inverseBind);
    }
    return {world, skin};
}
const nodeNames = ['', '', 'LHand1', 'RHand1', 'LeftFoot', 'RightFoot', 'Head', 'Tail',
    'u1', 'u2', 'u3', 'u4', 'u5', 'u6', 'u7', 'u8', 'u9', 'u10'];

export class Simulation
{
    constructor(effect, models, options = {})
    {
        this.effect = effect;
        this.models = models;
        this.predictable = effect.compatibility_profile === "predictable";
        this.detail = this.predictable ? 1 : options.detail ?? 1;
        this.random = new Random(options.seed ?? 9);
        this.scalars = Array.from({length: this.predictable ? 0 : 8192}, () => this.random.signed());
        this.vectors = Array.from({length: this.predictable ? 0 : 8192}, () => unit([this.scalar(), this.scalar(), this.scalar()]));
        this.components = effect.keys.map(key => ({key, p: properties(key), type: key.component_ref.split(';')[0],
            active: false, started: false, particles: [], rotation: [0, 0, 0], last: -1e9}));
        this.time = 0;
        this.soundEvents = [];
        this.target = options.target ?? null;
        this.targetPose = modelPose(this.target, 0);
        this.targetMatrix = identity();
        if (this.predictable && this.target)
        {
            // Authored recipes use a foot-level origin; native MM9 groups keep their original anchor.
            let bottom = Infinity;
            for (const piece of this.target.pieces) for (const vertex of piece.vertices)
            {
                let position = vertex.position;
                if (vertex.weights.length)
                {
                    position = [0, 0, 0];
                    for (const [node, weight] of vertex.weights)
                        position = add(position, mul(transform(this.targetPose.skin[node], vertex.position), weight));
                }
                bottom = Math.min(bottom, position[1]);
            }
            if (Number.isFinite(bottom)) this.targetMatrix[13] = -bottom;
        }
        this.duration = Math.max(effect.phase_ms/1000,
            ...this.components.map(c => c.key.end + (c.p.SpriteLifespan ?? c.p.FadeTime ?? 0)));
        this.advance(0);
    }
    scalar() { return this.predictable ? this.random.signed() : this.scalars[this.random.next() & 8191]; }
    anchor(c)
    {
        const parent = c.key.linked ? this.components.find(p => p.key.id === c.key.linked_id) : null;
        const model = parent?.model ?? this.target;
        const pose = parent?.pose ?? this.targetPose;
        const origin = parent?.position ?? [0, 0, 0];
        const name = c.key.linked_node || nodeNames[c.p.UpdatePos ?? 0];
        if (name && model && pose)
        {
            const index = model.nodes.findIndex(n => n.name.toLowerCase() === name.toLowerCase());
            if (index >= 0)
            {
                const position = transform(pose.world[index], [0, 0, 0]);
                return parent ? transform(parent.matrix, position) : position;
            }
        }
        return origin;
    }
    phase(c)
    {
        const duration = (c.key.end-c.key.start) / Math.max(c.key.repeat, 1);
        return duration > 0 ? ((this.time-c.key.start) % duration) / duration : 0;
    }
    place(c)
    {
        const offset = c.p.Offset ?? [0, 0, 0];
        const motion = sampleTrack(c.p.Mk, this.phase(c), [0, 0, 0]);
        const anchor = c.p.UpdatePos === 0 ? c.initialAnchor : this.anchor(c);
        c.position = add(add(anchor, offset), motion);
        c.scale = sampleTrack(c.p.Sk, this.phase(c), [1])[0];
        c.color = sampleColor(c.p.Ck, this.phase(c));
        c.matrix = directionMatrix(Array.isArray(c.p.Facing) ? c.p.Facing : [0, 0, 1], c.position, c.scale);
        if (c.model) c.pose = modelPose(c.model, this.time-c.born);
    }
    start(c)
    {
        c.started = c.active = true;
        c.born = this.time;
        c.initialAnchor = this.anchor(c);
        c.model = this.models.get(assetName(c.p.Model));
        this.place(c);
        c.previous = [...c.position];
        c.interval = (c.p.EmissionInterval ?? 0) / this.detail / this.detail;
        if (c.type === 'SpriteSystem' && !this.predictable)
            c.samples = Array.from({length: 256}, () => emissionSample(c.p, () => this.scalar(),
                () => this.vectors[this.random.next() & 8191]));
        if (c.type === 'PlaySound') this.soundEvents.push({kind: 'start', c});
        if (!this.predictable) this.update(c, 0);
    }
    updatePredictable(c, dt)
    {
        const running = this.time < c.key.end;
        if (running) this.place(c);
        if (c.type !== 'SpriteSystem') { c.active = running; return; }
        const lifespan = c.p.SpriteLifespan;
        // The engine advances existing particles before emitting this tick's batch.
        c.particles = c.particles.filter(p => this.time-p.born+1e-6 < lifespan);
        for (const p of c.particles)
        {
            p.position = add(p.position, mul(add(p.velocity, mul(c.p.WindDir, c.p.WindAmount)), dt));
            p.animationMs += dt*1000;
            const phase = (this.time-p.born)/lifespan;
            p.color = sampleColor(c.p.Ck, phase);
            p.scale = sampleTrack(c.p.Sk, phase % 1, [.2])[0];
        }
        if (running && this.time-c.last > c.interval)
        {
            const count = c.p.SpritesPerEmission;
            for (let i = 0; i < count; ++i)
            {
                const sample = emissionSample(c.p, () => this.scalar(),
                    () => unit([this.scalar(), this.scalar(), this.scalar()]));
                const center = mix(c.position, c.previous, i/count);
                c.particles.push({born: this.time, position: add(center, sample.offset), velocity: sample.velocity,
                    animationMs: 0, color: sampleColor(c.p.Ck, 0), scale: sampleTrack(c.p.Sk, 0, [.2])[0]});
            }
            c.previous = [...c.position]; c.last = this.time;
        }
        if (!running && !c.particles.length) c.active = false;
    }
    update(c, dt)
    {
        if (this.predictable) { this.updatePredictable(c, dt); return; }
        const running = this.time < c.key.end;
        if (running) this.place(c);
        if (c.type === 'SpriteSystem')
        {
            const lifespan = c.p.SpriteLifespan ?? 1;
            if (running && this.time-c.last > c.interval)
            {
                const configured = c.p.SpritesPerEmission ?? 1;
                const count = configured ? Math.max(1, Math.trunc(configured*this.detail)) : 0;
                for (let i = 0; i < count; ++i)
                {
                    const sample = c.samples[this.random.next() & 255];
                    // Native batch starts at current center and steps back toward previous center.
                    const center = mix(c.position, c.previous, configured ? i/configured : 0);
                    c.particles.push({born: this.time, position: add(center, sample.offset),
                        velocity: axisRotate(sample.velocity, c.rotation), animationMs: 0});
                }
                c.previous = [...c.position];
                c.last = this.time;
            }
            c.rotation = add(c.rotation, c.p.RotateAdd ?? [0, 0, 0]);
            c.particles = c.particles.filter(p => this.time-p.born < lifespan-.1);
            for (const p of c.particles)
            {
                const wind = mul(c.p.WindDir ?? [0, 0, 0], c.p.WindAmount ?? 0);
                p.position = add(p.position, mul(add(p.velocity, wind), dt));
                p.animationMs += Math.trunc(dt*1000);
                const phase = (this.time-p.born)/(lifespan || .01);
                p.color = sampleColor(c.p.Ck, phase, lifespan);
                p.scale = sampleTrack(c.p.Sk, phase % 1, [.2])[0];
            }
            if (!running && !c.particles.length) c.active = false;
        }
        else if (!running)
        {
            if (c.type === 'Model' && c.p.SmoothFade)
            {
                c.fadeStart ??= this.time;
                c.color[3] = clamp(1-(this.time-c.fadeStart)/(c.p.FadeTime || .5), 0, 1);
                if (c.color[3] === 0) c.active = false;
            }
            else c.active = false;
            if (c.type === 'PlaySound') this.soundEvents.push({kind: 'stop', c});
        }
    }
    advance(dt)
    {
        this.time += dt;
        for (const c of this.components) if (c.active) this.update(c, dt);
        for (const c of this.components) if (!c.started && c.key.start <= this.time)
        {
            this.start(c);
            if (this.predictable && dt > 0) this.update(c, 0);
        }
    }
    get particleCount() { return this.components.reduce((n, c) => n+c.particles.length, 0); }
    get finished() { return this.time >= this.duration && !this.components.some(c => c.active); }
}
