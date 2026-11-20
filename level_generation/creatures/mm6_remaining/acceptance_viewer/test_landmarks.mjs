import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const context = vm.createContext({document: {addEventListener() {}},
  state: {manifest: {pixels_per_logical_pixel: 2, logical_pivot: [100.5, 210.25],
    frames: {pose: {crop_origin_px: [20, 60]}}}, layout: {originX: 51.5, originY: 42.25}},
  $: id => id === 'zoom' ? {value: '2.5'} : {value: 'eye1'},
  tier: () => 2, frameScale: () => 1.35,
  restoredGeometry: () => ({x: 31.25, y: 69.75, scale: 1.12}),
});
vm.runInContext(fs.readFileSync(new URL('./landmarks.js', import.meta.url), 'utf8'), context);
const evaluate = code => JSON.parse(JSON.stringify(vm.runInContext(code, context)));
for (const mirrored of [false, true]) {
  for (const side of ['original', 'restored']) {
    const screen = evaluate(`landmarkScreenPoint({frame:'pose',mirrored:${mirrored}},'${side}',[43.25,83.5])`);
    // CSS scales the canvas by 0.8. Pointer coordinates must undo both CSS and actor transforms.
    const point = evaluate(`landmarkFromPointer({clientX:${12 + screen[0] * .8},clientY:${24 + screen[1] * .8}},
      {width:1000,height:800,getBoundingClientRect:()=>({left:12,top:24,width:800,height:640})},
      {frame:'pose',mirrored:${mirrored}},'${side}')`);
    assert.deepEqual(point, [43.25, 83.5], `${side} mirrored=${mirrored}`);
  }
}
const fit = evaluate(`fitLandmarkPairs([
  {original:[10,10],restored:[16,14]}, {original:[30,80],restored:[56,154]},
  {original:[20,null],restored:[36,null]}])`);
assert.equal(fit.scale, .5);
assert.deepEqual(fit.translation, [2, 3]);
assert.equal(fit.residual, 0);
assert.throws(() => vm.runInContext('fitLandmarkPairs([{original:[10,10],restored:[20,20]}])', context),
  /two separated/);
const headFit = evaluate('headTopBottomFit(40,340,100,340)');
assert.equal(headFit.scale, 1.25);
assert.equal(headFit.offsetY, 0);
assert.equal(340 + headFit.scale * (100 - 340) + headFit.offsetY, 40);
const shiftedFeet = evaluate('headTopBottomFit(40,340,55,355)');
assert.equal(shiftedFeet.scale, 1);
assert.equal(shiftedFeet.offsetY, -15);
assert.throws(() => vm.runInContext('headTopBottomFit(40,340,330,340)', context), /allowed size range/);
assert.throws(() => vm.runInContext('headTopBottomFit(40,340,350,340)', context), /head top above/);
console.log('PASS: fractional/mirrored coordinate mapping, X-only fit, head-top scale and independent feet alignment');
