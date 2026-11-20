#!/usr/bin/env python3
"""Record desktop CPU call stacks, gated by the game's loaded-map state."""

import argparse
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def validate_target(pid):
    process = Path(f"/proc/{pid}")
    if process.stat().st_uid != os.getuid() or (process / "exe").resolve().name != "openyamm":
        raise ValueError("--pid must identify an OpenYAMM process owned by the current user")


def main():
    repo = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=repo / "build-prof/game/openyamm")
    parser.add_argument("--output", type=Path, default=repo / "build-prof/perf-gameplay.data")
    parser.add_argument("--warmup", type=float, default=3.0,
                        help="seconds of loaded gameplay before enabling collection (default: 3)")
    parser.add_argument("--include-loading", action="store_true",
                        help="record the entire process, including loading and shutdown")
    parser.add_argument("--pid", type=int, help="attach to an already warmed-up OpenYAMM process owned by this user")
    parser.add_argument("--seconds", type=float, default=20.0, help="sampling duration when attaching (default: 20)")
    parser.add_argument("game_args", nargs=argparse.REMAINDER, help="game arguments after --")
    args = parser.parse_args()
    if not math.isfinite(args.warmup) or not 0 <= args.warmup <= 3600:
        parser.error("--warmup must be between 0 and 3600 seconds")
    if args.pid is not None:
        if args.pid <= 0 or not math.isfinite(args.seconds) or not 0 < args.seconds <= 3600:
            parser.error("--pid must be positive and --seconds must be between 0 and 3600")
        if args.game_args or args.include_loading:
            parser.error("--pid does not accept game arguments or --include-loading")
        try:
            validate_target(args.pid)
        except (OSError, ValueError) as error:
            parser.error(str(error))
    binary = args.binary.resolve()
    if args.pid is None and (binary.name != "openyamm" or not binary.is_file() or not os.access(binary, os.X_OK)):
        parser.error(f"executable not found: {binary}; build the openyamm target in build-prof first")
    perf = shutil.which("perf")
    if perf is None:
        parser.error("perf is not installed")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    game_args = args.game_args
    if game_args[:1] == ["--"]:
        game_args = game_args[1:]
    environment = os.environ.copy()
    # Profiles need a visible window: a minimized one is throttled differently.
    for key in ("OPENYAMM_PERF_CONTROL_FIFO", "OPENYAMM_PERF_ACK_FIFO", "OPENYAMM_PERF_WARMUP_MS",
                "OPENYAMM_START_MINIMIZED"):
        environment.pop(key, None)

    with tempfile.TemporaryDirectory(prefix="openyamm-perf-") as directory:
        command = [perf, "record", "-e", "cycles:u", "-F", "199", "--call-graph", "dwarf,16384",
                   "-o", str(output)]
        if args.pid is not None:
            if args.warmup > 0:
                command += [f"--delay={max(1, round(args.warmup * 1000))}"]
            command += ["-p", str(args.pid), "--", "sleep", str(args.warmup + args.seconds)]
        elif not args.include_loading:
            control = Path(directory) / "control"
            acknowledgement = Path(directory) / "ack"
            os.mkfifo(control, 0o600)
            os.mkfifo(acknowledgement, 0o600)
            command += ["--delay=-1", f"--control=fifo:{control},{acknowledgement}"]
            environment.update(OPENYAMM_PERF_CONTROL_FIFO=str(control),
                               OPENYAMM_PERF_ACK_FIFO=str(acknowledgement),
                               OPENYAMM_PERF_WARMUP_MS=str(round(args.warmup * 1000)))
        if args.pid is None:
            command += ["--", str(binary), *game_args]

        mode = f"OpenYAMM PID {args.pid}" if args.pid is not None else (
            "entire process, including loading" if args.include_loading else "loaded gameplay only")
        print(f"Recording {mode} to {output}", flush=True)
        if args.pid is None and not args.include_loading:
            print("Wait for '[Perf] collection enabled', then play. Close the game normally to finish.", flush=True)
        process = subprocess.Popen(command, cwd=repo, env=environment)
        try:
            return_code = process.wait()
        except KeyboardInterrupt:
            # The terminal delivers SIGINT to perf and its workload too. Let perf finish writing its data.
            return_code = process.wait()

    print(f"Profile: {output}", flush=True)
    return return_code if return_code >= 0 else 128 - return_code


if __name__ == "__main__":
    raise SystemExit(main())
