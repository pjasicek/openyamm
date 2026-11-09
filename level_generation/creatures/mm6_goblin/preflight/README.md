# Goblin generation preflight — 2026-09-08

The driver requested live capability and permission checks before unattended execution of [the goal](../GOAL.md).
The initial checks below preceded generation. The goal is now active; see the latest recheck below and
[current progress](../PROGRESS.md). Capability tests are not evidence that the character is finished.

## Live recheck — 2026-09-08, 07:24 local time

The existing Blender 5.2.1 GUI responded to Python execution and viewport screenshot capture. An isolated test scene
successfully rendered a transparent PNG, exported GLB and saved a scene library checkpoint. A separate background
Blender process reopened the checkpoint and found the test scene and its three objects. The GUI returned to
`MM6 Goblin detail studio`; it was not restarted or disconnected. No additional permission prompt was needed.
Evidence: [structured results](permission_recheck_uvcltou1/result.json).

The add-on status/version helper reports `No module named 'blender_mcp.config'`. Actual MCP scene commands,
screenshot capture, rendering and export work, so this helper failure is not currently a production blocker.
The first test export scanned other scenes/actions because selection alone did not restrict scene scope.
Rerunning with `use_active_scene=True` and `export_animations=False` produced the intended one-mesh, one-scene
static test GLB in 0.011 seconds. Use an isolated export project and explicit animation selection for the real actor.
The checkpoint here is deliberately a scene library, not the final ordinary editable character file.

Rig/animation and built-in AI generation succeeded earlier in this session, as recorded below; this recheck did
not spend another image generation call. No unresolved approval is known for the tested workflow. Future service
outages, exhausted storage/quota or genuinely new privileged operations cannot be ruled out by a preflight.

## Verified in this session

| Capability | Result and evidence |
| --- | --- |
| Launch GUI Blender | PASS: Blender was closed; launched `blender` with the approved Blender command prefix |
| Automatic MCP startup | PASS: scene inspection succeeded after startup without a manual Connect click |
| Scene inspection and viewport screenshot | PASS: default scene with Cube, Camera and Light; screenshot visibly verified |
| Python scene/model/material edits | PASS: isolated `Goblin permission preflight` scene; original active scene restored |
| Rig, animation and corrective shapes | PASS: test armature, weighted mesh, keyframed bone and morph |
| Texture creation/packing | PASS: generated texture packed and exported |
| Cycles render and PNG writing | PASS: [128-pixel transparent test render](render.png) |
| GLB export | PASS: `rig_export.glb` parsed; skin, animation, morph targets and embedded image present |
| Save editable checkpoint | PASS: `checkpoint.blend` saved using `copy=True` |
| Background Blender/reopening | PASS: separate `blender -b` process reopened the checkpoint and found its rig |
| Long-job scheduling primitive | PASS: Blender timer executed and wrote `timer_check.txt` |
| Workspace and temporary writes | PASS: project and `/tmp` file creation/readback |
| Local processing dependencies | PASS: Pillow 10.4.0, NumPy 1.24.4, PyYAML 5.3.1 imported |
| Built-in AI image generation | PASS: actual reference-based generation completed; no CLI/API-key fallback used |
| Persist generated image | PASS: output copied from the tool's default directory into this project |

Blender version: **5.2.1 LTS**. Approximately **40 GiB** of free space was available at the beginning of the checks.
This is a point-in-time observation, not a storage reservation. Keep renders/checkpoints purposeful.

The GUI remains running and connected. The background reopen process exited normally; its message that MCP cannot
start in background mode is expected and does not disconnect the separate GUI server. Reuse the GUI instance.
The temporary preflight scene remains available for inspection; it is not the goblin authoring scene.

Host process inspection required the execution tool's normal escalation path because the sandbox process namespace
did not show host Blender processes. Host inspection and GUI/background Blender commands then succeeded. No permission
request or blocking dependency remained unresolved at the end of this preflight. The existing `blender` command prefix
covers the tested launch and background workflows; do not change approval settings or assume unrelated commands inherit it.
This does not guarantee future service availability, generation quota, disk capacity, crash recovery or approval of
new dependencies/actions beyond the tested scope. Follow the startup guide if the connection later drops.

## AI reference test

Input: `assets_dev/engine/sprites/gobsta0.bmp`, losslessly converted to [PNG](gobsta0_source.png).
Tool: built-in `image_gen`, using the imagegen skill. Exact prompt: [image_prompt.txt](image_prompt.txt).
Output: [restoration_front_test.png](restoration_front_test.png).

The result demonstrates working generation and project persistence. It retains the frontal green goblin, broad
armor arrangement and weapon side. It is **not yet an approved modeling reference**: compare proportions, face,
ear jewelry, equipment details and silhouette against the other native views before selecting or correcting it.
Do not treat the successful permission test as completion of the goal's reference audit or restoration stage.

Test implementation: [blender_check.py](blender_check.py). It expects no scene with its test name already present;
inspect existing test artifacts before rerunning. Structured results are in `blender_results.json`; the checkpoint,
GLB, render and small completion files provide the corresponding evidence.
