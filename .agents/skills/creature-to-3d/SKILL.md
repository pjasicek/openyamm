---
name: creature-to-3d
description: Create, inspect, audit or resume rigged MM6–MM8 creatures using the shared Claude playbooks. Complete production covers HD references, Meshy, fitted rigs, animations, textures and verified game integration. Use for CREATURE_TO_3D requests and creature-model WIPs. Honor narrower scope; pure 2D restoration uses creature-restore, and audit/planning do not start generation.
---

# Creature to 3D

One resumable workflow with three production stages and a read-only audit mode. Accept a creature name,
native source pattern or existing project/model path plus natural-language scope:

```text
$creature-to-3d FULL - MM6 GOBLIN
$creature-to-3d FULL - MM7 vampire - budget 150 credits
$creature-to-3d demon — prepare references and motion study
CREATURE_TO_3D gob*.bmp — plan only
$creature-to-3d demon — inspect this Meshy model
$creature-to-3d demon — inspect the returned rig
$creature-to-3d demon — continue animation production
$creature-to-3d demon — apply the returned textures
$creature-to-3d demon — audit current work
$creature-to-3d demon — resume
```

These are agent requests, not shell commands. Honor explicit scope and previous authorization. Skill creation,
discussion, audit, status and plan-only requests do not authorize image generation or asset changes. Inspection
alone is read-only; an instruction to correct or ingest a supplied asset authorizes the relevant local work.
On resume, continue the previously authorized production work; a prior audit-only request does not authorize repairs.

## Default production workflow (Codex and Claude)

Read the applicable playbook fully before production; use its existing scripts and review tools after inspecting
their inputs and side effects. Keep the procedure in these shared documents instead of maintaining a Codex copy:

| Work | Authoritative procedure |
| --- | --- |
| Every creature's references | [HD masters](../../../level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md): five generated views from original native sprites, gated before Meshy; never upload native or enlarged/restored frames |
| Humanoid body and motion | [Humanoid playbook](../../../level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md): current source-frame rig, local clip selection before modelling, G1–G7 and arm/hand checks on every clip; `mm6_bar1_claude/` and `mm6_gob2_claude/` are the current script references |
| Other anatomy | [Non-humanoid playbook](../../../level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md): local rigs, procedural motion and the applicable flyer, segmented, serpentine, effect-bodied (elementals: no Meshy) or other anatomy section |
| Materials and tiers | [Creature textures](../../../level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md): shared textures, padded region masks, palette ramps and head detail; [native shading transfer](../../../level_generation/creatures/NATIVE_SHADING_TRANSFER.md) only when comparison justifies it |
| Export and game contract | [Model rendering](../../../engine/render/MODEL_RENDERING.md): LODs, attachments, merged head materials, impact timing, sockets and head look; current implementation wins over stale runtime notes |

The humanoid playbook's current default and later corrections supersede its older quick-start/template recipes:
world-rotation retargeting on fitted source frames, mesh-measured hands, connectivity-based finger weights,
reduction after weighting, and route-specific UV transfer. Do not copy old Mixamo/MPFB defaults or require a paid
retexture just because topology changed when verified UV carry-over works. Playbook numbers and creature-specific
repairs need adaptation to the selected mesh; historical placeholder faults are not automatic accepted deviations.
The texture guide's older AO-in-red/specular-off notes are superseded where the current runtime uses that channel
as `openyamm_specular_mask`; follow the selected material contract and current compose/export scripts.

Codex uses its built-in imagegen directly under the imagegen skill. The playbook's `codex exec` worker commands
describe Claude's image handoff, not a required nested Codex run. Reuse adequate selected HD masters on resume.

## Complete production / FULL

A request to create a complete creature uses this workflow end to end by default. `FULL` is an explicit,
case-insensitive spelling of the same scope, including `CREATURE_TO_3D FULL <creature>`. It covers native studies,
HD references, agent-operated Meshy body/props, fitted rigs, all required actions, textures, editable/portable
exports, runtime LODs and bindings, regression and indoor/outdoor visual comparison with the native sprites.
An explicit asset-only, reference-only, handoff or other narrower request stops at that boundary. A bare resume
retains its existing scope; a new complete-production request can expand it. A quoted invocation in discussion
or skill maintenance does not start production.

Read [complete production and ownership](references/full-production.md) before complete production. Resolve the
selected project/branch and its state first; FULL supersedes an older preparation-only scope or user-operated
handoff, while preserving selected art and explicit design decisions. Reuse adequate work and repair confirmed
missing prerequisites, including weapons/equipment omitted from a deliberately unarmed body reference.
Continue through preparation and agent review gates instead of stopping for each Meshy return or routine repair.
Technical completion and user artistic acceptance remain separate; FULL does not require acceptance at every gate.

The existing project Meshy spending limit applies; a new complete project defaults to **100 credits**, including props.
An explicit `budget N credits` changes that limit. A limit is a spending boundary, not evidence of quality or
permission to declare unfinished work complete. Preserve state and report actual external blockers.
Complete production includes installation through the existing model runtime. Renderer/engine feature development,
directional sprite export and commits remain separate scope; preserve the original sprite assets.
Use `tools/run_creature_meshy.sh` for Meshy network operations and `tools/run_creature_blender.sh` for Blender.
Reuse their saved command-prefix approvals as described in the FULL reference; do not request a new approval
for each Python script, job name or polling interval.

## Start and route

Resolve the native family and existing project under `level_generation/creatures/`; reuse its selected artifacts,
manifests and recorded user decisions. Read [audit and progress](references/audit-and-progress.md) to establish
the current state. For audit/status requests, follow its read-only procedure and report; do not enter production.
For production, establish only the evidence needed to resume the requested operation, rather than conducting
a complete audit on every invocation. The stage references below supplement the selected playbook for scoped
handoffs, detailed anatomy checks and native reconstruction; they do not replace its default production route:

| Stage | Operations | Procedure |
| --- | --- | --- |
| 1. References and motion study | Native inventory, HD masters, source clip selection/ROM | [Stage 1](references/01-references-and-motion.md) |
| 2. Model and rig | Meshy geometry, likeness, fitted rig and deformation gates | [Stage 2](references/02-model-and-rig.md) |
| 3. Animation and finish | All clips, textures, LODs, exports and scoped game integration | [Stage 3](references/03-animation-and-finish.md) |

Report both the furthest produced artifact and the earliest unresolved prerequisite. A textured file can still
need anatomy correction. Missing evidence means unverified, not defective or complete. Keep technical checks,
agent visual review and user artistic acceptance separate, bound to the selected revision.

## Shared working rules

- Native sprites/descriptors establish identity, motion observations, timing and view reuse. Reviewed AI images
  clarify detail; they do not recover hidden original geometry. Label observations, inferences and user choices.
- Aim for convincing likeness and motion. Do not advance past a confirmed relevant defect to finish more clips;
  repair its cause and revisit affected evidence. No fixed revision count or time limit establishes quality.
  Honor explicitly accepted deviations and scope limits; report unresolved differences plainly.
- Use the [existing sprite-to-3D workflow](../../../level_generation/creatures/SPRITE_TO_3D_WORKFLOW.md) for
  applicable modeling, coordinate-space, Blender/export and optional directional-render details. Read only the
  sections relevant to the current operation; procedural ghost/goblin choices are examples, not defaults.
- Before image generation, read the available imagegen skill and inspect the supplied images. Use built-in
  imagegen for authorized reference generation. Save actual returns, prompts, input hashes and selected versions.
- Complete production uses agent-operated Meshy through the job helper and project budget. A requested
  user-operated handoff supplies concrete files/settings and the exact return needed. Check current official
  documentation for route-specific options and prices before submitting. Diagnose failures and reconcile uncertain
  submissions before further paid requests; never silently regenerate a recorded job.
- Check the [local animation library](../../../anim_library/README.md) before obtaining clips. Choose and preview
  humanoid source motions before modelling; use `meshy_anim_library.py check` before any paid library action and
  ingest each paid result. Preserve source rates and record adapted clips under runtime role names.
- Before interactive Blender authoring, follow
  [Blender MCP startup](../../../level_generation/BLENDER_MCP_STARTUP.md). Preserve unrelated scenes and selected
  checkpoints. FULL uses isolated background Blender, not the shared GUI/MCP scene. Audit in an isolated/background
  copy so loading a WIP cannot replace someone's live project.
- Reuse existing preparation, render and verification tools after inspecting their inputs and side effects.
  Asset-specific repair scripts and vertex masks belong to their recorded revision. Add a shared helper only
  for an operation existing tools cannot perform; do not create a custom viewer or report suite per creature.
- Texture for sharpness from the start: UVs from `level_generation/creatures/claude_shared/uv_atlas.py` (defaults since
  2026-11-12: PartUV charts, seam pass, sparrow packing; needs `partuv_venv` and `sparrow_venv`, falls back to xatlas
  by itself), Meshy paint at 4K downsampled once, gentle grading, `gutter_fill.py` last on every map, and
  `texture_quality.py` targets met before install, per the
  [texture quality pass](../../../level_generation/creatures/claude_shared/TEXTURE_QUALITY_PASS.md).
- Stage assets in the creature project before installation. Complete production includes the playbook's runtime
  binding and visual checks; scoped art/handoff work needs no engine build. Keep renderer changes and directional
  sprite export separate, and do not commit unless requested.

After production work, update one canonical progress record and give the selected paths, current stage/substep,
remaining findings and the next action with its owner. If awaiting a Meshy model, rig, texture return or a requested
artistic decision, hand off a concrete reviewable package; continue independent authorized work where useful.
