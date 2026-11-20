import assert from 'node:assert/strict';
import {chamber, sandState, measurePile, pileVolumes, totalVolume} from './sand-volume.mjs';

// Re-measure the displayed pile and clipped upper reservoir, rather than asserting
// that two requested percentages add up. Include both unequal glass orientations.
const phases = [...new Set([0, 1e-10, 1e-7, 1-1e-7, 1-1e-10, 1,
  ...Array.from({length: 1001}, (_, i) => i/1000)])].sort((a, b) => a-b);
let maxTotalError = 0, maxTransferError = 0;

for (const turns of [0, 1]) {
  const oppositeFull = sandState(1-turns, 1);
  const upperSlices = pileVolumes(1-turns, oppositeFull.fillHeight).reverse();
  const step = 1536/upperSlices.length;
  let previousLower = -1, previousUpper = Infinity;
  for (const p of phases) {
    const state = sandState(turns, p);
    const lower = measurePile(turns, state.fillHeight);
    const upper = upperSlices.reduce((sum, volume, row) =>
      sum + volume*Math.max(0, Math.min(1, (row+1)-state.upperCut/step)), 0);
    assert(Number.isFinite(lower) && Number.isFinite(upper) && Number.isFinite(state.upperCut));
    assert(lower >= previousLower-1e-6, `Lower pile shrinks: orientation ${turns}, progress ${p}`);
    assert(upper <= previousUpper+1e-6, `Upper reservoir grows: orientation ${turns}, progress ${p}`);
    const totalError = Math.abs((lower+upper)/totalVolume-1);
    const transferError = Math.abs(lower/totalVolume-p);
    assert(totalError < .00005, `Conservation error: orientation ${turns}, progress ${p}: ${totalError}`);
    assert(transferError < .00005, `Transfer error: orientation ${turns}, progress ${p}: ${transferError}`);
    maxTotalError = Math.max(maxTotalError, totalError);
    maxTransferError = Math.max(maxTransferError, transferError);
    previousLower = lower;
    previousUpper = upper;
  }
  // The same shape and material turn into the next cycle's upper sand, without a reset.
  assert.equal(sandState(turns, 1).lower.d, sandState(1-turns, 0).upper.d);
  assert.equal(sandState(turns, 1).lower.crest, sandState(1-turns, 0).upper.crest);
  assert.equal(sandState(turns, 0).lower.d, '');
  assert.equal(sandState(turns, 1).upperCut, 1536);
  assert.equal(sandState(turns, 1).lower.top, chamber(turns).neck);
}
console.log(JSON.stringify({samples: phases.length*2, maxTotalError, maxTransferError,
  endpoints: 'Both half-turns preserve the exact sand path and crest'}, null, 2));
