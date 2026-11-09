# Visual review — pfem

Reviewed native five-view/three-palette references, all ten generated raw sheets, registered action comparisons,
all 59 enhanced frames, all 59 mask overlays, three standing palette sets, and worst-edge patches on light/dark.
The standing, walk, attack, hit, fidget and falling silhouettes remain recognizable against the native poses.
Clothing construction, headband, short tied hair and two hem stripes remain coherent across views.

The first color fit included unchanged greenish cloth shades and made palette 787 too olive. Restricting the fit
to changed native indices restored the brown appearance. A softer chroma coverage threshold covers the dark bodice
without tinting off-white fabric. A narrow fringe inherits coverage from nearby interior material to avoid noisy
color selection caused by matte unmixing.

The browser attack mask view revealed greenish blade pixels entering the cloth mask. Six reviewed local blade
polygons in `config.json` neutralize blade RGB at preserved luma/alpha and force zero recolor coverage. This is a
local deterministic repair, not a new generation or whole-character desaturation.

Browser captures exercise a mirrored blue walking pose, the brown attack with mask overlay, and a prone green pose
against a light background. Native/enhanced pivot placement, crop offsets and displayed sequence entries agree.
The offline viewer provides native timed playback, explicit stepping, all eight view aliases and palette switching.
Captures are reproducible with `tools/capture_local_html.py`; no engine scenarios or builds were used.

Remaining approximations: restored cloth shadows are softer and warmer than the original's near-black shading;
small facial and fold details vary between separately generated poses. The native fidget is extremely subtle and
the enhanced fidget retains that restrained motion. AI detail and inferred matte alpha are reconstructions, not
recovered original geometry or ground-truth transparency. Thin blade silhouettes remain intentionally small.
