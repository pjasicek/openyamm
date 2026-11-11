import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {Simulation, sampleColor} from './simulation.mjs';

const effects = JSON.parse(execFileSync('python3', ['-B', '-c',
    'from authored import load_authored; import json; print(json.dumps(load_authored()[0]))'],
    {cwd: fileURLToPath(new URL('.', import.meta.url)), encoding: 'utf8'}));
assert.equal(effects.length, 3);
for (const effect of effects)
{
    for (const fps of [30, 60, 120])
    {
        const sim = new Simulation(effect, new Map());
        let peak = 0;
        for (let i = 0; i < fps*5; ++i)
        {
            sim.advance(1/fps);
            peak = Math.max(peak, sim.particleCount);
            for (const c of sim.components) for (const p of c.particles)
            {
                assert.ok(p.scale >= 0 && Number.isFinite(p.scale));
                assert.ok(p.color.every(Number.isFinite));
                const phase = (sim.time-p.born)/c.p.SpriteLifespan;
                assert.deepEqual(p.color, sampleColor(c.p.Ck, phase));
                assert.ok(Math.abs(p.animationMs-(sim.time-p.born)*1000) < 1e-6);
            }
        }
        assert.ok(peak > 0 && peak < 100, `${effect.name}: bounded, nonempty emission`);
        assert.equal(sim.particleCount, 0);
        assert.ok(sim.finished);
    }
    const high = new Simulation(effect, new Map(), {detail: 1});
    const low = new Simulation(effect, new Map(), {detail: .15});
    for (let i = 0; i < 40; ++i) { high.advance(1/60); low.advance(1/60); }
    assert.deepEqual(high.components, low.components, 'Native detail control must not change authored recipes');
    console.log(`${effect.display_name}: 30/60/120 Hz playback, fades, animation clock and complete drain passed`);
}
