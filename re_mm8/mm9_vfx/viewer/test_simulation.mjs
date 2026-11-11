import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Simulation, properties, sampleColor, emissionSample, assetName, modelPose} from './simulation.mjs';
import {dot, length} from './math.mjs';

const retained = JSON.parse(readFileSync(new URL('../column_of_fire.json', import.meta.url)));
const fire = retained.effect;
const p = properties(fire.keys[0]);
assert.equal(p.EmissionType, 3, 'Use the numeric opcode despite the saved PlaneOut label');
assert.equal(p.Radius, 10);
assert.ok(Math.abs(sampleColor(p.Ck, 0)[3]-155/255) < 1e-12);
const inward = emissionSample(p, () => .5, () => [0, 1, 0]);
assert.ok(Math.abs(length(inward.offset)-10) < 1e-6);
assert.ok(dot(inward.offset, inward.velocity) < 0, 'Native opcode3 must move inward');
const cone = emissionSample({...p, EmissionType: 5}, () => .5, () => [0, 1, 0]);
assert.deepEqual(cone.offset, [0, 0, 0], 'Cone particles start at the center');
const endpoints = [{time: 0, rgb_transparency: [255, 0, 0, 0]},
    {time: 1, rgb_transparency: [0, 0, 255, 255]}];
assert.deepEqual(sampleColor(endpoints, .81, .8), [0, 0, 1, 0], 'Short lifespan terminal-color quirk');

const simpleKey = structuredClone(fire.keys[0]);
simpleKey.end = 1;
simpleKey.properties = simpleKey.properties.filter(p => !['Mk', 'Offset', 'EmissionType', 'Velocity'].includes(p.name));
simpleKey.properties.push({name: 'EmissionType', type: 3, value: '0,Point', numeric_selection: 0},
    {name: 'Velocity', type: 2, value: 0});
const single = {...fire, keys: [simpleKey]};
const coarse = new Simulation(single, new Map());
coarse.advance(.5);
assert.equal(coarse.particleCount, 2, 'One update emits one batch, with no catch-up burst');
assert.equal(coarse.components[0].particles[0].position[1], -50, 'Wind magnitude is retained');
coarse.advance(.41);
assert.equal(coarse.components[0].particles.some(p => p.born === 0), false, 'Expiry at lifespan minus .1');
const low = new Simulation(single, new Map(), {detail: .5});
assert.ok(Math.abs(low.components[0].interval-.04) < 1e-7, 'Initial and current detail division');

for (const fps of [30, 60, 120])
{
    const simulation = new Simulation(fire, new Map());
    let maximum = 0;
    for (let step = 0; step < fps*5; ++step)
    {
        simulation.advance(1/fps);
        maximum = Math.max(maximum, simulation.particleCount);
        for (const c of simulation.components)
            for (const p of c.particles)
                assert.ok([...p.position, ...p.color, p.scale].every(Number.isFinite));
    }
    assert.ok(simulation.finished);
    console.log(`Column of Fire: ${fps} Hz, peak ${maximum} particles, drains completely`);
}
if (process.argv[2])
{
    const data = JSON.parse(readFileSync(process.argv[2]));
    const models = new Map(Object.entries(data.models));
    for (const model of models.values())
    {
        const pose = modelPose(model, .37);
        assert.ok(pose.world.flat().every(Number.isFinite));
    }
    for (const effect of data.catalog.effects)
    {
        const simulation = new Simulation(effect, models, {target: models.get('models/monk.abc')});
        for (let i = 0; i < Math.ceil((simulation.duration+1)*60); ++i)
        {
            simulation.advance(1/60);
            for (const c of simulation.components)
                if (c.active)
                {
                    assert.ok(c.position.every(Number.isFinite), effect.name);
                    for (const p of c.particles)
                        assert.ok([...p.position, ...p.color, p.scale].every(Number.isFinite), effect.name);
                }
        }
        assert.ok(simulation.finished, `${effect.name} did not finish`);
    }
    console.log(`All ${data.catalog.effects.length} effects simulate and finish with finite transforms.`);
}
console.log('Recovered-rule regression checks passed.');
