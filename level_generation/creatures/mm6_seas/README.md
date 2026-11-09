# MM6 Sea Serpent restoration

Validated, staged only. Open [offline viewer](review.html); see [review notes](review_notes.md) and [validation](validation.json). All 59 unique sources, three native palettes, 2x base/mask atlas pages and placement/animation metadata are present.

Rebuild with `python3 level_generation/creatures/mm6_seas/process.py`, then `python3 level_generation/creatures/mm6_seas/package.py`, then `python3 level_generation/creatures/mm6_peasants/build_viewer.py seas`. Re-review before refreshing acceptance after changes. Built-in imagegen raw sheets, exact submitted prompts, generation hashes and processing settings are preserved locally. No gameplay installation.
