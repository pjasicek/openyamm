# MM6 Robot restoration

Validated, staged only. [Offline viewer](review.html), [visual review](review_notes.md), [validation](validation.json). 54 unique native images, three palettes, 2x matching base/mask pages with native animation and placement metadata.

Rebuild: `python3 level_generation/creatures/mm6_rob1/process.py`, then `python3 level_generation/creatures/mm6_rob1/package.py`, then `python3 level_generation/creatures/mm6_peasants/build_viewer.py rob1`. Re-review changes before accepting. Built-in imagegen exact prompts, raw sheets, rejected view revisions, provenance and deterministic settings preserved. No gameplay installation.
