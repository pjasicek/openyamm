#!/usr/bin/env bash
# Head-set paint chain (project folder), both tiers: fix_neck_pm3.py (from the composed heads' _preneck backups: neck skin,
# collar wedges, bead line; r2: beard-to-neck gradient, smooth collar line) -> fringe_fix.py (skin texels on the hair shell's rim -> hair) -> hand_clean.py (one clean skin
# tone per tier on the hands) -> pad_head.py (gutters). Re-runnable: every run starts from the _preneck backups.
set -euo pipefail
V=../claude_shared/gltf_venv/bin/python
G=${G:-work/pm3_body_tex.glb}
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/fix_neck_pm3.py "$G" pm3_tp pm3b_tp 2>/dev/null | grep "FIXNECK pm"
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/fringe_fix.py pm3_tp 2>/dev/null | grep "FRINGE hair texels"
RIM_K=2.4 systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/fringe_fix.py pm3b_tp 2>/dev/null | grep "FRINGE hair texels"
# r2 (orchestrator review): tier A glared - eye opening x1.35 and brows 3 mm up in paint, upper-lid crease lightened
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/eye_open_pm3.py "$G" pm3_tp ${EYE_A:-1.15 0.0 0.3 0.0 0.002} 2>/dev/null | grep EYE_OPEN
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/face_fix_r3.py "$G" pm3_tp 2>/dev/null | grep FACEFIX
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/face_fix_r3.py "$G" pm3b_tp 2>/dev/null | grep FACEFIX
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/ear_skin_pm3.py "$G" pm3_tp pm3b_tp 2>/dev/null | grep EARSKIN
[[ -n "${R5:-}" ]] || systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/mouth_slot_paint.py "$G" pm3_tp pm3b_tp 2>/dev/null | grep MOUTHSLOT
HAND_REF=205,122,90 systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/hand_clean.py pm3_tp 2>/dev/null | grep HAND_CLEAN | cut -c1-60
HAND_REF=220,148,112 systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/hand_clean.py pm3b_tp 2>/dev/null | grep HAND_CLEAN | cut -c1-60
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$V" scripts/pad_head.py "$G" pm3_tp pm3b_tp 2>/dev/null | grep PAD_HEAD
