# Plate Knight review and reproduction

Accepted all 59 native unique images and original action/variant contracts. Five stored views,
mirrors, timing, logical size/anchor, native frame scale, shared actions and collapse pieces preserved.
Reviewed native references and every generated batch, all-base/all-mask ordered contacts,
three standing palettes, enlarged light/dark edges and offline viewer samples:
mirrored walk view 6 / palette 762 / frame 3; death palette 761 / frame 3.
Sequence and paused-viewer review does not establish real-GPU performance.

Rejected first standing sheet (red instead of blue-violet) and first front-walk/attack/hit sheets
(rear mane incorrectly drawn over face/chest). Corrected images were generated using native poses;
attack and hit use accepted front walk as the enhanced identity reference. Exact submitted prompts,
references and rejected drafts are retained in generation.json.

Native palette research shows accent changes AND blue shifts in dark neutral materials.
Enhanced RGBA8 mask R selects blue-violet accents, G neutral materials, preserving warm grip/fittings.
Usage-weighted native palette luminance LUTs reproduce red/brass accents and dark steel shifts;
base bypass is exact, variants preserve alpha and zero-mask pixels.
Generated warm steel was neutralized through G coverage with fixed overall gain 0.90.
Purple-safe extraction preserves violet material, with narrow warm-pink and green edge cleanup.
Native dark violet accents remain intentionally purple. Generic magenta-excess audit counts
7,748 cleaned / 8,803 exported / 8,803 atlas-extracted candidates; these are not a zero-spill claim.
The final inspected contacts show retained material color and acceptable contours, without the earlier
pink/green spike halo. Automated coverage, provenance, unclipped cells, exact crop/atlas reconstruction,
mask sums and per-palette native sequence checks all pass.

Fine skull fittings and helmet faceplate are more defined than native pixels; smooth metal shading
and hair strands are approximate. Some native hard blue shadow patches become softer in the LUT fit.
No originals were changed and no gameplay installation was performed.
Extraction comparisons precede the final grade; final packaged contacts and viewer captures include it.

Rebuild (repository root):
```
python3 level_generation/creatures/mm6_kni/process.py
python3 level_generation/creatures/mm6_kni/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py kni
```
Family wrapper declares the nonlinear LUT contract. Rebuild resets visual acceptance; review again.
