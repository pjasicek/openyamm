# MM6 Hydra restoration

Complete staged 2x package: 59 unique native images, descriptors 559-561, palettes 754-756. Five unused native standing images retained offline. Open [review.html](review.html); [manifest.json](manifest.json) defines matching atlas/mask placement, timelines, mirrors, scales and RGB LUT variants. [Review notes](review_notes.md) record actual checks and limitations.

Raw sheets, exact submitted prompts, source hashes, rejected additive-only palette comparison and deterministic processing settings are preserved. Reproduce with process.py, package.py, then ../mm6_peasants/build_viewer.py hyd; changes require affected review and a refreshed acceptance record. LUT variant rendering is implemented offline and declared for future runtime integration. No gameplay installation.
