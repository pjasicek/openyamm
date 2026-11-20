Work in progress. Custom cyan extraction restores base and candle flames. Common registration (0.85,0,-5) corrects oversized raw. Lower raw row repeats stand at 617 rather than 627 pixels: crop origin shifted up 10 pixels for that row, retaining canvas size. No per-frame foreground fitting or support replacement. Native support colors vary across frames, so do not blindly copy first-frame support. Remaining: inspect corrected light/dark proofs, tone and native-timed motion; not accepted.

## Tone correction checkpoint
Existing extracted backups retained. Whole-object RGB gamma gave the base a purple cast; replaced with pooled spatial correction for main flame (native y 0:80), tiers/candles (80:210), and base (210:253), shared across all four frames and preserving alpha. Replay repair_extraction.py then restore_native_tone.py then queue.py check. Latest three-region outputs still require both-background and timed-motion inspection before acceptance. No new imagegen call.

## Final review
Common scale reduced to .83 (dx 0, dy -5); all four outside-canvas fractions now zero. Refreshed before_tone backups from this extraction, reapplied three-region pooled grade, and inspected every light/dark proof plus the four-frame 125 ms contact. Detailed placement warning disposition is in review.json. Base has 3–3.5 native pixels extra bottom margin; no per-frame fitting or support copying.
