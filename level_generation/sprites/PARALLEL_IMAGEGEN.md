# Scheduling multiple built-in image requests

Use this for authorized creature, decoration, item, projectile and effect restoration, alongside the installed
imagegen skill. Discussion and planning alone do not start generation. Concurrent submission is not a separately
billed API/CLI workflow and does not authorize switching models/accounts or bypassing limits.

## Measured behavior

The [2026-09-09 ten-request trial](concurrency_trial_10/README.md) submitted ten independent calls within 5 ms.
All ten succeeded in **272.238 seconds**, returning roughly one image every 24–32 seconds. A matching standalone
control took **31.054 seconds**. Extrapolating that single control to ten images gives 310.54 seconds, an estimated
1.14x throughput ratio, **not a measured ten-versus-ten speedup**. The result is consistent with effective queuing
somewhere in the tool/service path; client observations cannot locate the serialization boundary.

Concurrent submission works in this session, but it did not demonstrate a substantial generation speedup. Do not
promise 10x faster work, infer extra service capacity from ten pending promises, or sum queue-inclusive request
latencies as a supposed sequential baseline. Preparation/review/export time is separate from generation latency.

## Agent procedure

1. Inventory, deduplicate and prepare prompts/references ahead of generation. Inspect local references first.
   Use explicit reference paths for every request where supported; avoid relative “last image” references when
   completion order can differ. Assign a stable job ID and private output paths to each asset/sheet.
2. Establish and visually review a shared enhanced identity reference before dependent action/view sheets.
   Then independent sheets/assets can be submitted together. Keep corrections, masks and final packing dependent
   on accepted inputs. Short related animations and interactive state pairs should stay coherent within sheets.
3. Prefer small ready batches of **2–4 requests** for short feedback and manageable review. A requested ten-job
   batch is supported by this trial, but adds queue latency without proven extra capacity. Do not queue hundreds.
   This batch size is a local workflow choice, not an official service concurrency limit.
4. In `functions.exec`, start each async built-in call before awaiting the batch with `Promise.allSettled`.
   Use the current tool name/schema. Await every promise before the cell exits; fire-and-forget work is discarded.
   Follow the tool's yield/wait instructions and resume existing cells rather than starting duplicate requests.
5. Record submission and result-return times per job. Tag results with the submitted job ID, never arrival order.
   Keep successful outputs when another fails. Copy selected files from their actual returned paths into the
   workspace, preserve exact prompts/provenance and use one owner for the aggregate manifest. Do not log base64.
6. Keep a bounded review backlog. Clean and visually review the completed batch before accepting it or packing
   final assets. Preserve alpha/spill, anchors, native timing, state/view consistency, material masks and FX blending.
   Overlap independent preparation/cleanup when tool orchestration allows it; never accept unseen results for speed.
7. On a concurrency/rate-limit rejection, preserve successes, honor the retry delay and reduce to serial calls.
   Retry only failed jobs after checking output/status. A timeout or yielded cell is not proof that generation failed.
   Do not automatically switch to paid API/CLI fallback or repeat a benchmark for every family.

No subagents are needed for multiple tool promises. If delegation is separately authorized, use a shared queue cap
and one generation owner; workers can prepare/review independent assets without racing on the same manifests.

The larger reliable savings are deduplication, reuse of accepted identity/palette references, compact useful sheets,
deterministic cleanup, and targeted repairs. The trial produced ten drafts, but some retained pixel steps or invented
details: a successful image response is not a production-quality acceptance check.
