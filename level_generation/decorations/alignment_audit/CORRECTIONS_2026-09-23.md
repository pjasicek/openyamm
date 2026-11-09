# Ground-contact correction — 2026-09-23

The [initial visual inspection](INSPECTION_2026-09-23.md) found 73 accepted grounded appearances with lower
visible and opaque edges 1.5–4 native pixels above their originals. The correction used existing accepted pixels;
there were no image-generation calls.

- Five clear static lifts were translated down 3–4 native pixels and reaccepted.
- Forty-six smaller static lifts were translated down 1.5–2.5 native pixels and reaccepted. Their job IDs and
  current output directories are recorded in [static_contact_revisions_2026-09-23.json](static_contact_revisions_2026-09-23.json).
- Five animation jobs (24 frames) received one shared vertical translation per job. The crystal sequence moved
  1 native pixel; the purple flame pedestal, both cooking-fire chunks and burning rock moved 1.5. Every frame in
  each chunk received the same shift, preserving the motion deltas. See
  [animation_contact_revisions_2026-09-23.json](animation_contact_revisions_2026-09-23.json).
- The sixth flagged animation job, `g17714_v0_s0` (`searkb01`–`searkb06`), was reaccepted unchanged with
  `anchor_kind: water`. Its frame-five lower-edge difference is moving foam around a fixed rock, not a floating
  ground support.

This changed **75 accepted PNGs in 56 explicit queue revisions**, covering all 72 true raised appearances and
three additional crystal frames that needed the sequence's shared correction. The 73rd initial flag was the
waterline exception. All previous raw masters, outputs and acceptance states remain archived in each new attempt.
New full-canvas light/dark proofs, checks and specific review notes accompany the accepted revisions.

Every corrected image is a pixel-exact integer translation of its previous accepted output. No alpha >=17 pixel
was discarded at the lower edge; resampling fringe with alpha at most 15/255 was trimmed where it occupied the
previous canvas's final rows. Native logical and 2x physical canvas sizes remain unchanged.

The refreshed audit reports **zero grounded vertical-contact flags**, **zero wrong dimensions** and **zero
accepted-hash mismatches**. Forty-two grounded rows remain on the shortlist for horizontal lowest-band shape
differences only; their visible lower edges stay within one native pixel of the originals. The strict readiness
ledger remains at 2,504 ready and 22 deferred source files; the export remains incomplete for those unrelated
refusals. `queue.py validate`, `readiness.py` and `queue.py export` passed after the changes.

An isolated `mm6/outa1.odm` desktop check compared native and corrected `6tree27` at the same pose. The
[side-by-side contact crop](runtime/outa1_6tree27_contact_comparison.png) shows the corrected trunk meeting the
same terrain contact without a visible gap or clipped base. Full [native](runtime/outa1_6tree27_native.png) and
[corrected](runtime/outa1_6tree27_corrected.png) captures and the [pose record](runtime/capture.json) are saved.
The corrected capture used a private temporary map override; no global assets or maps were modified. This is one
placement check, not proof of every map instance or every corrected decoration.
