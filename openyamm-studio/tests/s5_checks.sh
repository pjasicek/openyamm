#!/usr/bin/env bash
# The S5 browser editor's local checks (S5_BROWSER_EDITOR.md 4.13, S5a2 to S5a4): the request list's catalogue and its
# generated types, the RPC contract suite against the native and the WebAssembly core (with S5a4's recorded walks),
# the host's tests (the byte routes, the MCP tools, the live side: notices, the watcher, the relay, the inbox; walk
# mode's files and Play here; S5a5's jobs: the background checks, cancel by kill, the job route), and the web app's
# suite (the schema lint with its allow list, the RPC client and its notices, the plan's geometry, the pins, the
# controller's pin loop, Play here and jobs, walk mode's input and the camera against the game's, the flow graph,
# the scorecard and the compare's heat). S5c: the contract suite also drives the browser worker's build (the hosted
# page's core, oymap_worker.mjs beside oymap_rpc.js) under Node, and the web suite tests the hosted page's file system,
# the install's layout and pairing. S6: the lighting bake job's sidecar pages, pictures and refusals (lighting.test.mjs;
# LIGHTING_BAKE=<project> also bakes for real).
# Usage: tests/s5_checks.sh [--native <oymap>] [--wasm <oymap_rpc.js>]
#   defaults: build/oymap, build-wasm/oymap_rpc.js. Exit code 1 when any check fails.
set -uo pipefail
studio="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
native="$studio/build/oymap"
wasm="$studio/build-wasm/oymap_rpc.js"

while [ $# -gt 0 ]; do
    case "$1" in
        --native) native="$2"; shift 2 ;;
        --wasm) wasm="$2"; shift 2 ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
done

# The tests run in other folders: the cores by absolute paths.
native="$(realpath "$native")"
wasm="$(realpath "$wasm")"

failed=0
run() {
    echo "== $*"
    "$@" || { echo "FAILED: $*"; failed=1; return 1; }
}

run node "$studio/schema/rpc/gen.mjs" --check
worker="$(dirname "$wasm")/oymap_worker.mjs"
if [ -f "$worker" ]; then
    run node "$studio/schema/rpc/contract/run.mjs" --native "$native" --wasm "$wasm" --worker "$worker"
else
    echo "== the browser worker's build is missing ($worker): ./build.sh wasm"
    failed=1
    run node "$studio/schema/rpc/contract/run.mjs" --native "$native" --wasm "$wasm"
fi
(cd "$studio/host" && { run node test/host.test.mjs; run node test/mcp.test.mjs; OYMAP="$native" run node test/live.test.mjs;
    OYMAP="$native" run node test/play.test.mjs; OYMAP="$native" run node test/jobs.test.mjs; run node test/lighting.test.mjs; }
    exit "$failed") || failed=1

if [ -d "$studio/web/node_modules" ]; then
    (cd "$studio/web" && run npm test)
    [ $? -eq 0 ] || failed=1
else
    echo "== web: skipped (no web/node_modules: npm ci in web/ first)"
    failed=1
fi

exit "$failed"
