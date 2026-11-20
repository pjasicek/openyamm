# Complete production / FULL and workspace ownership

The agent owns source interpretation, likeness, corrections and actual visual/playback review. Helpers provide
ownership, uploads, receipts and integrity checks; they cannot certify art automatically. Read stage procedures
when their work becomes necessary. Complete-production requests use this procedure by default; `FULL` explicitly
requests the same end-to-end scope, including runtime installation and checks. Honor explicit asset-only or other
narrower boundaries. Follow the shared playbooks linked from the skill for the production method.

## Resolve and resume

Resolve world, native bitmap family, descriptors and palettes. Inspect the existing creature project, selected
branch, READMEs, progress and recorded user decisions. Prefer explicit selection/current-method evidence over
modification time, `final` filenames or high revisions. Explain a defensible inferred branch choice without
restarting good work. Reuse its canonical JSON progress record; use `creature_3d_progress.json` for a new project.
Record the current requested scope while retaining historical scope/receipts and explicit design decisions.
An old `next_action.owner = user` for a Meshy handoff does not block newly requested complete production; a bare
resume retains that handoff scope. Workflow maintenance and adopting a new default do not start a production run.

Verify selected files/hashes and inspect actual images/models before trusting historical completion. Use
`tools/run_creature_meshy.sh ... inspect` for list-based selected-artifact records; inspect other manifest formats
directly, without forced conversion. The helper checks presence/hash/roles, not visual correctness. Resume at the
earliest relevant unresolved criterion. Do not regenerate references, rerig good geometry or discard working clips
solely because the agent/workflow changed. Keep the canonical progress current at useful milestones.
An absent component inventory is unverified coverage, even when the missing-component list is empty.

Inventory required body structures and equipment from native sources even when the modeling reference is unarmed.
Inspect actual imported geometry, appearance, animation grip and final export for missing weapons, shields, straps,
digits and attachments. A valid body GLB alone is not complete creature coverage.

Example: MM6 goblin has several historical branches. `stage1_20261006/creature_3d_progress.json` records selected
unarmed body references and a native motion study, with a separate sword still required. If that is the selected
branch, verify those artifacts, resume body production and obtain/assemble the sword. Do not replay historical
procedural builds or treat an absent weapon in a neutral body reference as permission to omit it.

## Parallel ownership and Blender

Claim the **top-level creature project** under `level_generation/creatures/`, using the canonical native bitmap
family id, such as `mm6:gob`, not an alias or palette name. Branches/palettes share that family ownership. Identity
leases prevent two agents claiming different directories for the same family; different families work independently.
Choose a unique agent/session owner and retain the returned token across tool calls:

```sh
python3 tools/creature_workspace.py claim --project level_generation/creatures/mm6_goblin \
  --identity mm6:gob --owner <unique-agent-run-id> --state stage1_20261006/creature_3d_progress.json
```

The stored credit limit is reused; a new project defaults to 100 credits including props. Use `--budget N` for an
explicitly requested limit. Keep one canonical state; `--state` is relative to the creature root. Claim before
mutations/jobs. Protect non-Meshy writes, including state edits, with:

```sh
python3 tools/creature_workspace.py run --project <creature-root> --token <own-token> -- <command> <arguments>
```

Do not nest another guarded helper inside `run`: its project lock intentionally rejects nested writers. Delegate
same-creature work only with the parent's ownership and serialized writes; prefer different creatures for parallel
production. Never copy another agent's token to bypass ownership.

FULL uses separate background Blender processes and project-local scripts with explicit input/output paths.
Inspect reused scripts for shared `/tmp` paths, fixed render names or unrelated writes. Prefer
`tools/run_creature_blender.sh --token <own-token> <project-script.py>`: factory settings, embedded auto-execution
disabled, bounded CPU threads, Python failures propagated and a unique log per invocation. Scripts explicitly load
selected inputs and save new owned revisions. Do not also wrap the launcher in `run`. Inspect render/playback files
from isolated copies. Do not use or restart the shared Blender GUI/MCP scene, change its project or kill another
creature's process. Explicit interactive tasks outside FULL still follow the Blender startup/ownership procedure.

Release on completion or deliberate handoff using `creature_workspace.py release --project ... --token ...`.
Pending jobs survive in the state. After interruption, inspect the recorded owner and live agents/processes;
release an old lease only when its owner is confirmed inactive. Leases never expire merely because a long job
has not updated a timestamp. Do not steal a live project; continue independent work or report its ownership dependency.

## Agent-operated Meshy

Use `tools/run_creature_meshy.sh` for production submission, status and downloads. It invokes only the fixed
`creature_meshy.py` helper, preserving ownership, budget limits and durable receipts. Credentials come from `MESHY_API_KEY`
or the configured global `meshy` MCP environment. Never write them into prompts, request JSON, receipts or logs.
An optional backup account (`MESHY_API_KEY_BACKUP`, same places) takes a new job when the primary has fewer credits
than the job's estimate. Each receipt records its `account`, and status, downloads and follow-up jobs that reference
an earlier task (`rig_task_id`, `input_task_id`) stay on that task's account. `balance` lists every account.
If a follow-up is rejected because its account ran out, rebuild that step from the project file (for example rig
again from `@file:` instead of the old task id) under a new job name; it then goes to an account with credits.
The official MCP uses the primary key only, so it cannot inspect or reconcile backup-account tasks.

### Reusable execution approval

Before the first paid submission, verify authentication and network with `tools/run_creature_meshy.sh balance`.
When sandbox networking is restricted, request `sandbox_permissions: "require_escalated"` with
`prefix_rule: ["tools/run_creature_meshy.sh"]` on this read-only check. Explain that the client can save this
approval for subsequent budget-authorized Meshy operations. If the check fails because of sandbox DNS/network
restrictions, retry this same read-only command outside the sandbox before creating a paid submission intent.
Reuse the saved prefix for all submissions, polls, downloads and adoption operations, across creatures.
Approval persistence is controlled by the client; FULL authorization and skill instructions alone do not save it.

Invoke the wrapper directly from the repository root, with ordinary arguments and `--token`, so its approved
prefix matches. Do not invoke it through `bash`, `python3`, a heredoc, an environment assignment or another
guarded command. Use the existing `tools/run_creature_blender.sh` prefix for authoring/export/render scripts.
Keep ordinary project-file preparation and progress edits inside the filesystem sandbox. Do not seek broad
Python/shell approval for routine helpers. Reuse existing task ids after switching execution context; network
approval is not permission to resubmit an uncertain job. Required higher-priority host restrictions still apply.

Check current official [generation](https://docs.meshy.ai/en/api/image-to-3d),
[rigging](https://docs.meshy.ai/en/api/rigging), [texturing](https://docs.meshy.ai/en/api/retexture) and
[pricing](https://docs.meshy.ai/en/api/pricing) docs when selecting settings. Single-image SmartTopology uses
`meshy-t2`, up to 15,000 target faces; inspect actual output. Multi-image is a separate route. Preserve selected
settings instead of inheriting a wrapper's advice to regenerate a correct A-pose as T-pose. Provisional textures
for rigging are distinct from final UV/material production. Rigging needs a textured humanoid GLB facing glTF +Z;
it estimates joints automatically and exposes no manual landmark-coordinate inputs. Correct joints/weights and
extra structures locally. Unsupported anatomy needs a scoped local rig, not repeated failing humanoid jobs.

Use project-local API request JSON with `@file:` paths relative to the creature root. Files are encoded inside the
helper; receipts retain paths/hashes rather than binary data. For example:

```json
{"model_url": "@file:work/body_for_rig.glb", "height_meters": 1.0}
```

Use the creature's actual selected scale; 1.0 above is illustrative. Stage uploads inside its project. After
geometry corrections, upload the corrected GLB rather than chaining the unchanged original task id.

```sh
tools/run_creature_meshy.sh --project <creature-root> --state <canonical-state.json> --token <own-token> \
  submit --job body_rig_v1 --kind rigging --request requests/body_rig_v1.json --credits 5
tools/run_creature_meshy.sh --project <creature-root> --state <canonical-state.json> --token <own-token> \
  poll --job body_rig_v1 --wait-seconds 45
tools/run_creature_meshy.sh --project <creature-root> --state <canonical-state.json> --token <own-token> \
  download --job body_rig_v1
```

Estimate credits conservatively from current prices. Actual consumption and unresolved reservations count toward
the creature limit, including props. A terminal receipt with explicit consumption releases the unused reservation;
without that receipt retain the estimate and do not guess refunds. Identical named jobs reuse the task id without
a POST. Changed inputs require a named revision after diagnosis. A timed-out creation is `UNCERTAIN`, not failed:
inspect service receipts/tasks, then use `adopt --job ... --task-id ... --evidence ...` after matching the submission.
Do not bypass uncertainty with a new job name. Confirmed rejection/failure needs a diagnosed cause and corrected
submission, recorded in the correction ledger. A reached limit/external blocker leaves preserved checkpoints and
an honest incomplete status; no per-job approval is needed within the existing authorization.

Poll in bounded intervals, continue independent work and download originals/maps promptly because API assets have
limited retention. Downloads use `meshy/<unique-job-name>/` with hashes in canonical state. Never edit originals
in place. Refresh expired signed output URLs by polling the recorded task while retained. Reuse local originals
without regenerating; diagnose missing expired outputs instead of silently submitting another job.

## Equipment and separate props

Record `required_components` as a list in the canonical state, for example:

```json
[{"id": "body", "artifact_role": "body", "required": true},
 {"id": "scimitar", "artifact_role": "weapon", "required": true}]
```

Also record component source/design evidence, selected revision, assembly/attachment and review state. Retain the
original manifest's path convention (normally relative to the manifest); Meshy download paths are relative to the
creature root. Add selected-artifact roles when verified. Role/file presence does not prove final assembly.

Reuse adequate existing props. Generate missing complex props through Meshy image-to-3D or text-to-3D from isolated
item references; retexture an existing corrected prop when appropriate. Use separate names such as
`scimitar_geometry_v1` and `scimitar_texture_v1` with the shared creature budget/provenance. Model simple parts
locally when quicker and faithful; complicated weapons need not be built by hand. Check actual thickness,
silhouette, ornament, materials, hilt/hand scale, grip space and orientation against source views. Never send a rigid
weapon through humanoid rigging. Attach it locally with rigid weights or a supported node, then inspect blade
direction, hand contact, clearance and native visibility/drop behavior throughout motion. A separate prop remains
a delivery prerequisite until assembled and reviewed in the final animated/exported creature.

## Completion evidence

Apply the full stage 2/3 deformation and animation reviews: contacts, twist paths, digits, rigid tips, equipment,
cloth/armor and required effect/visibility tracks. Cover all required actions and applicable palettes. For game
models, keep selected clips at their intended speed and follow the humanoid playbook's "Clip timing": fit wind-up
near the native action, mark the blow/release, retain gameplay timing and keep Hit within its native duration.
Exact frame/hold reconstruction applies when explicitly requested, including native directional sprite exports.
Review actual normal/slow playback, close views and in-between poses from the delivered export. Fix confirmed
relevant faults before expanding clips or completing.
Service success and a revision/retry count never substitute for art review.

Check the consumer's current skin/influence/bone/material/texture/effect capabilities with existing engine/asset
tools. Missing components, unverified clips, unsupported required effects and export differences block production
completion. Exclude scene/template objects and widgets, verify units/axes/anchors, UV/tangent/material seams and
reimport the actual GLB in isolated Blender. Use the selected playbook's UV route: the current humanoid body
retexture uses Meshy's UVs (`enable_original_uv: false`) transferred back by verified face correspondence;
head-only and suitable locally unwrapped uploads retain their UVs. Transfer maps/UVs to the retained animated
master instead of replacing it with the static return.

Deliver the editable `.blend`, portable GLB, required textures, clip/component/effect and palette manifests as
applicable, selected hashes and concise reproduction/review instructions in the existing project. Reuse existing
evidence formats; no new viewer per creature. Track technical/agent visual completion separately from user artistic
acceptance. Report accepted deviations and actual consumer limitations. Technical completion can precede user
artistic acceptance; a confirmed unresolved required defect still prevents completion.

## Runtime delivery and review

For complete production, continue through the playbook's installation and checks. An explicit staged/asset-only
request ends with its verified exports instead. Use existing runtime support; missing engine features are a
separate task, not permission to rewrite the renderer or alter gameplay.

1. Follow [model build post-processes](../../../../engine/render/MODEL_RENDERING.md): export, prepare, colour/shadow
   LODs and the applicable shadow correction, region variants, rigid equipment split, then head-material merge.
   Validate the actual deliverables and reuse the existing review viewer; test every tier/clip with
   `claude_shared/check_viewer.mjs` before sharing its link.
2. Install every accepted GLB (body and attachments) with `tools/install_model.py <export.glb> --world <world>`: the
   source goes to `assets_source/worlds/<world>/models/`, the runtime copy to `assets_dev` (see AGENTS.md). Then
   update that world's `assets_dev/worlds/<world>/models/actors.yml`, preserving unrelated bindings and original
   sprites. Derive scale from the appropriate upright/flight pose and native frame scale;
   verify tier scaling, stride, clips, impact events, attachments, launch sockets and humanoid head look.
3. Add or update focused actor-binding regression coverage where the new family needs it. Build the ordinary
   `openyamm` target when required, then run the affected world's actor regression suite. Follow AGENTS.md for
   build and desktop-launch commands; a creature task does not authorize a Vulkan build.
4. Inspect real viewer playback and native game captures: all tiers, useful front/side/three-quarter views, face
   and both hands, gait, attacks/casts, hit, death/remains, contacts and materials. Compare model and sprite using
   the same camera indoors and outdoors at the playbook's test locations, or an appropriate habitat for water
   creatures. Keep spawn commands in one open console session as the newer humanoid playbook specifies.
5. Fix relevant faults and repeat affected checks. Record installed paths/hashes, checks actually performed,
   remaining findings and artistic acceptance separately. If the runtime environment is unavailable, preserve
   the staged output and report runtime review as incomplete rather than declaring delivery complete.

Do not commit unless requested. Do not start generation or installation while updating this workflow.
