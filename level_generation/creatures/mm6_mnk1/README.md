# MM6 Monk restoration

Accepted staged package: [offline viewer](review.html), [manifest](manifest.json), [validation](validation.json), [review notes](review_notes.md).

57 unique native images, all native actions/views/mirrors, three palettes. One 2× RGBA8 base with matching R8 robe masks. Decoded base plus mask pages including padding: 32,943,335 bytes (31.42 MiB). Shipping manifest and atlas PNGs: 7,159,036 bytes. Preview variants are excluded from runtime memory.

```sh
python3 level_generation/creatures/mm6_mnk1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py mnk1
python3 level_generation/creatures/mm6_peasants/build_viewer.py mnk1
```

Use the family processing script: it protects neutral hands and fits cloth variants from native pixel usage. Prompts, both identity drafts, accepted raw action sheets, source hashes and processing settings are retained. Repackaging resets visual acceptance; inspect any changed output before reaccepting. Original assets and gameplay are unchanged.
