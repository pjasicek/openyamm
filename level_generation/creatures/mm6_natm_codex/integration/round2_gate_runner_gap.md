# Requested head/palm checks unsupported by the shared runner

Review round 2 requires head-facing yaw/pitch limits and a casting-palm target at release.
The current `claude_shared/gates/run_gates.py` does not implement either check, and its
configuration validator rejects unknown fields. Shared files are read-only under batch rule 3;
batch cost-control rule 6 explicitly prohibits a replacement per-creature gate implementation.

`shared_gate_request.json` records the requested intent for the orchestrator/tooling owner.
Those two checks must not be described as shared-runner PASS. The motion authoring receipt
records the construction's measured directions, and the final export removes constant
translation/scale animation channels from B_Neck and B_Head.

Neck edge stretch **can** use the existing implementation: `review/round2_neck.gates.json`
selects the neck skin as both arm edge regions. All original arm/hand/contact checks remain
in the main `gates.json` run. This reuses the unmodified shared evaluator; it adds no gate code.
The neck probe uses p99 <= 1.5 and maximum <= 2.0, on every clip and colour/shadow LOD.
