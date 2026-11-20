# Icon workspace and redeployment

The restoration workspace is retained under `level_generation/ui/`. Runtime files in `assets_dev/` are deployed
copies. Changes should originate in the restoration workspace, be reviewed and recorded, then be deployed.

The [MM7/MM8 minimap revision](../../minimaps/esrgan_study_20260928/README.md) uses the user-selected
**anime-video v3 direct 2×** treatment for all 27 native minimaps. Sources, neural masters and accepted exports
are retained there. The 15 MM6 minimaps retain their approved Blender light-noise treatment.

The [transparent PC portrait revision](pc_transparent_acceptance_20260927/README.md) is accepted and installed:
all **4,032 portraits across 72 active families** now use the reviewed 118×158 RGBA exports in the shared
engine `icons_x2` root. The port 9100 preview shows the accepted set with selection rings, center guides and offsets.
The [HUD facemask removal](hud_facemask_removal_20260927/README.md) removes the obsolete green overlay from
the shared HUD and preview while preserving portrait dimensions, click areas and selection-ring placement.

The [MM7 Town Portal revision](town_portal_mm7_acceptance_20260927/README.md) is accepted and installed:
the regenerated `antagrich.png` map and six matching destination highlights. All seven installed files exactly
match the accepted browser artwork. Native canvases and placement are preserved.

The [MM6 Town Portal revision](town_portal_acceptance_20260927/README.md) is accepted and installed:
one map with repaired gargoyle terrain and six registered destination highlights. All seven runtime files
match the reviewed browser artwork. Native positions and canvas sizes are unchanged.

The [spellbook reconstruction](spellbook_fixup_review/README.md), on port 8900, is now
[accepted and installed](spellbook_acceptance_20260927/README.md): 12 shared-background pages, 111 stable spell
pairs, 12 school bookmark pairs, and the restored strength of nine Air pairs. The acceptance publishes 258 files
and changes 156 runtime images. All controls retain their YAML positions; five default-state export widths adopt
their paired highlighted canvases under explicit migration receipts.

## Current ownership

Paths below are relative to the repository root.

| Purpose | Location |
| --- | --- |
| Main workspace and live acceptance ledger | `level_generation/ui/hud_inventory/`; `checkpoint/state.json` |
| Frozen original dimensions, logical canvases and destinations | `level_generation/ui/hud_inventory/expected_targets.json`; current spell export overrides are recorded in `spellbook_acceptance_20260927/canvas_migrations.json` |
| Current accepted x2 index, hashes and destinations | `level_generation/ui/hud_inventory/accepted_icons.json` |
| Latest accepted revision and exports | Follow `accepted_icons.json` → `latest_revision`; each revision retains `accepted/` and `receipts/` |
| Earlier accepted exports, retained for unchanged targets and history | `hud_inventory/town_portal_mm7_acceptance_20260927/accepted/`, `hud_inventory/town_portal_acceptance_20260927/accepted/`, `level_generation/minimaps/accepted/`, `hud_inventory/spellbook_acceptance_20260927/accepted/`, `hud_inventory/spill_acceptance_20260927/accepted/` and `hud_inventory/runtime_install_20260926/stage/` |
| Original review notes, offsets and fitting records | `level_generation/ui/hud_inventory/finalization_20260926/` |
| Raw attempts, generated sheets, masters and repair work | `hud_inventory/checkpoint/attempts/`, `hud_inventory/chat_returns/`, `hud_inventory/review/`, `hud_inventory/paperdoll_review/`, plus the sibling `level_generation/ui/remaining_art_review/` and `mm8_art_review/` workspaces |
| Archived originals | `assets_legacy/icons_20260926/`; mapped by `runtime_install_20260926/source_archive.json` |
| Runtime copies | `assets_dev/engine/icons_x2/` and `assets_dev/worlds/mm6`, `mm7`, `mm8` `/icons_x2/` |

There are 9,920 accepted exports: 7,995 engine, 846 MM6, 517 MM7, and 562 MM8. World NPC namespaces stay separate.
The current `accepted_icons.json` points to the accepted version of every export, including unchanged exports
from earlier revisions. All these files are inside `level_generation/`. Per-revision receipts and run manifests
trace their preparation; the index hash is bound to the canonical ledger.

The ledger records the [current input reconciliation](../../minimaps/esrgan_study_20260928/input_reconciliation/receipt.json),
which preserves independently updated menu layouts and faithful fonts. It retains the earlier
[HUD facemask removal](hud_facemask_removal_20260927/input_reconciliation.json) and
[inventory-grid offset reconciliation](input_reconciliation_20260927/README.md).
Exact current hashes and original snapshots are checked without modifying frozen artwork contracts.

Masters are not consolidated into one uniform directory per icon. Many are multi-image generation sheets with
recorded crops. Some accepted sprites are direct Real-ESRGAN outputs or deterministic derivatives, so not every
x2 image has a separate larger master to downscale. All final accepted x2 files are indexed together, with
immutable artwork retained in their respective revision directories.

## Redeploy the current accepted workspace

From the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
```

This checks the current index, accepted artwork and canonical ledger, then copies changed images into their
recorded engine/world destinations. It does not regenerate images or accept modified files. Old dated installers
must not replay historical snapshots over newer approvals; the original consolidation installer now refuses
to overwrite the new spill revision.

The installer copies image exports only. The installed `engine/icon_packages.txt` content policy and
`engine/data_tables/item_visuals.txt` are also needed. The latter's source placement and fitting proposals are
preserved in `finalization_20260926/`; the artwork installer does not regenerate or install those tables.
Release ZIP packaging is a separate step.

## Revise an asset

1. Find the target in the live ledger and `accepted_icons.json`; follow its reviewed-artwork
   path and prior receipts to the source master or prepared sprite.
2. Create a new version under `level_generation/`. Preserve the original master, accepted x2 export and old receipt.
3. Produce a candidate on the current accepted export canvas, normally the exact native canvas at x2. Honor any
   explicit accepted canvas migration rather than silently restoring historical state-size differences. Update
   only the intended inventory/equipment variants and any deliberate shared-image aliases.
4. Review it in context, including transparency, equipment overlap, body/pose variants and saved offsets.
5. Record the new approved hash and provenance in a new receipt/transaction, update the live ledger and publish
   the new `accepted_icons.json` with its hash bound to the ledger.
6. Deploy the newly accepted export and any approved data changes, then validate the resulting installation.

Editing an accepted file in place invalidates its recorded hash. Editing a raw/master file alone does not rebuild
or deploy its descendants. New revisions currently require the relevant preparation and acceptance steps;
there is no universal command that performs the entire edit → regenerate → approve → publish cycle.

The current browser remains on port 8899. [Open paperdoll review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html).
See [the latest revision](pc_transparent_acceptance_20260927/README.md) for deployment and validation, and
[the original installation handoff](runtime_install_20260926/README.md) for runtime ownership and placement history.

## Check for color spill

For a future scan, explicitly use the current index and a new output directory to preserve the reviewed audit:

```sh
python3 -B level_generation/ui/hud_inventory/scan_spill.py \
  --manifest level_generation/ui/hud_inventory/accepted_icons.json \
  --output level_generation/ui/hud_inventory/spill_audit_next
```

The scan reads accepted x2 files, linked masters and other retained named masters. It checks magenta, green and
cyan/teal against native rendering
profiles and separates likely spill from intentional-material uncertainty. It does not alter artwork or acceptance.
See [the audit instructions](spill_audit_20260926/README.md) and
[the browser report](http://127.0.0.1:8899/level_generation/ui/hud_inventory/spill_audit_20260926/index.html).

## Accepted spill repairs (2026-09-27)

[Spill acceptance](spill_acceptance_20260927/README.md) publishes all 1,722 reviewed entries, with 1,531 changed
runtime images, including 768 inventory/equipment images. Only the 12 recently commented targets received
additional repairs. Original palette keys and actual linked master backgrounds are recorded separately.
Existing alpha, canvas sizes and placement tables are unchanged. Retained colored materials and spell effects
are accepted under the user's blanket approval, without additional artwork changes.

Use `spill_acceptance_20260927/accepted.json` for this revision and its neighboring `validation.json` for checks.
The review displays the installed accepted versions, retains old flags and notes, and has a **Resolved recent
comments** filter. Raw masters and old accepted files remain provenance. Deploy from `accepted_icons.json` through
`deploy_icons.py`; superseded pilots and the old dated snapshot are historical evidence.
