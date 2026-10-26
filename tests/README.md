# Test content requirements

The unit tests use the MM6–MM8 content in `assets_dev`. Imported MM9 content is an optional, untracked package.
Tests that need its files use `requiresMm9Assets()` and are reported as skipped when `assets_dev/worlds/mm9`
is absent. MM9 parser and gameplay tests with synthetic inputs still run. A present but incomplete MM9 directory
is tested normally and must fail if required files are missing or invalid.

Use doctest's `--no-skip` option on a content-complete CI host to require every asset integration test.

The built-in headless regression runner also reports missing optional MM9 content and the optional MM8 actor-model
manifest as explicit `[SKIP]` entries, with a skipped count in its summary. Base MM6–MM8 gameplay coverage still runs.
