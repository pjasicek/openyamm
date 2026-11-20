# MM7 water elemental — blocked identity correction

Prepared all 120 native frames and 18 compact generation batches, with original palettes 501/502/503 explicitly
resolved to their shared MM8 ACT files. Native palette comparison is review/native_palettes.png. The appearances
are blue-teal, green-teal and red-brown, with separately changing fins and pale belly shading.

One raw standing sheet covers five stored views. Its enhanced anatomy and detail are retained, but review found
that the top-middle tail fan incorrectly shows bright pink/cyan front colors instead of the native dark underside.
The plain scaled chest also needs the targeted detail cleanup described in prompts/submitted/standing_v2.txt.
This is a partial checkpoint, not validated final art. The remaining 17 action sheets have not been generated.

The exact correction was rejected twice by built-in imagegen, HTTP 400 output moderation category sexual:
c7ff452e-920f-470d-bc06-89cbe69ebf91 and 5dfefe41-a118-4744-8c72-3f4f62764019. This is a nonsexual restoration
of the native fantasy creature. Both request records are in generation.json; no rejected output was available.

Resume when the image-service rejection can be resolved: submit the preserved standing_v2.txt with native
references/standing.png as input 1 and raw/standing_v1.png as input 2. Inspect the dark underside fan and plain
chest scales before selecting v2 with ../mm7_m514/record_generation.py. Reuse that corrected identity across
the prepared 17 missing action batches. Retain every exact submitted prompt and versioned output.

The partial five-frame cleanup uses tone 0.80 and common per-batch scale calibration. After artwork completion,
author enhanced-pixel masks for the independently changing cool scales and fin regions, fit deterministic native
palette transforms with an exact base bypass, process/export all frames, build the offline viewer, review every
pose and variant plus light/dark edges, write artifact-hashed acceptance, then refresh inventory and MM7 ledger.
No final atlas or complete manifest is issued. Everything remains staged; native files and gameplay are untouched.
