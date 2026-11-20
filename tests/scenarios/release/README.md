# Release check scenarios

The release workflow (`.github/workflows/packages.yml`) plays every scenario listed in `scenarios.txt` with the
Linux and Windows builds and the desktop content packs, and the publish job plays the first one in a fresh
installation of the small Linux package (`packaging/publish_release.py check`). Paths are relative to
`tests/scenarios/`. Keep the set small and fast; it guards packaging, content mounting and save/load, not gameplay.
