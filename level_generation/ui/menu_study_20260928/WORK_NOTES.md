# Menu study

The approved browser design, audit and provenance are in [README.md](README.md).

The user approved revision 03 on 28 September 2026 and requested staging. The
[integration bundle](runtime_stage/README.md) contains blank graphics, fonts, UI YAML drafts, frozen references
and runtime contracts. `stage_runtime.mjs` exports the approved CSS surfaces/geometry; `prepare_stage.py` assembles
the bundle; `validate_stage.py` checks it against the actual engine layout parser and writes the manifest/receipt.
Native integration remains separate work. Existing runtime assets/code and the Git index were not changed by staging.
