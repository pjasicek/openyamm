#!/usr/bin/env bash
cd /home/pjasicek/github/OpenYAMM
L=level_generation/creatures; A=$L/mm9_honkmale_claude; B=$L/mm9_honkfemale_claude
TM=c6c00f4787b34fc38bc957f6bab50261; TF=0eaf705da79e4c22a53a2708a0af6570
RU=$(python3 -c "print(72/2048)")
DM=$(python3 -c "print(0.5396+110/2048)"),0.3521
DF=$(python3 -c "print(0.4077+110/2048)"),0.0762
b() { tools/run_creature_blender.sh --token "$@" 2>&1 | tail -1 | cut -c1-70; }
b $TM $A/v2/scripts/hand_fix.py $PWD/$A/v2/work/fix_v1.blend $PWD/$A/v2/work/hands_v3.blend $PWD/$A/v2/work/hands_v3.json scale=1.14
b $TM $A/v2/scripts/sleeve_lining.py $PWD/$A/v2/work/hands_v3.blend $PWD/$A/v2/work/sleeves_v3.blend $PWD/$A/v2/work/sleeve_lining_v3.json Bip01 $PWD/$A/v2/textures/honkm_head_basecolor.png body_png=$PWD/$A/textures/honkm_basecolor_v7.png orm_png=$PWD/$A/textures/honkm_metal_rough_1k_v7.png lining=1 near=0.22 end=0.15 radius_end=0.036 cap=0 dark_pct=10
b $TM $A/v2/scripts/robe_lining.py $PWD/$A/v2/work/sleeves_v3.blend $PWD/$A/v2/work/robe_v3.blend $PWD/$A/v2/work/robe_v3.json body_png=$PWD/$A/textures/honkm_basecolor_v7.png orm_png=$PWD/$A/textures/honkm_metal_rough_1k_v7.png boot_cut=0.28 dark_pct=30 drop_forearm_parts=1 wall_top=0.60 offset=0.012 dark_uv=$DM
b $TM $A/v2/scripts/medallion.py $PWD/$A/v2/work/robe_v3.blend $PWD/$A/v2/work/medal_v3.blend $PWD/$A/v2/work/medal_v3.json centre=-0.0065,-0.122,0.50 radius=0.042 atlas=0.5396,0.3521,$RU buckle=-0.011,-0.145,0.136
b $TF $B/v2/scripts/hand_fix.py $PWD/$B/v2/work/fix_v1.blend $PWD/$B/v2/work/hands_v3.blend $PWD/$B/v2/work/hands_v3.json scale=1.30
b $TF $B/v2/scripts/sleeve_lining.py $PWD/$B/v2/work/hands_v3.blend $PWD/$B/v2/work/sleeves_v3.blend $PWD/$B/v2/work/sleeve_lining_v3.json Bip01 $PWD/$B/v2/textures/honkf_head_basecolor.png body_png=$PWD/$B/textures/honkf_basecolor_v7.png orm_png=$PWD/$B/textures/honkf_metal_rough_1k_v7.png lining=1 near=0.14 end=0.14 radius_end=0.027 cap=0 dark_pct=10
b $TF $B/v2/scripts/robe_lining.py $PWD/$B/v2/work/sleeves_v3.blend $PWD/$B/v2/work/robe_v3.blend $PWD/$B/v2/work/robe_v3.json body_png=$PWD/$B/textures/honkf_basecolor_v7.png orm_png=$PWD/$B/textures/honkf_metal_rough_1k_v7.png dark_lo=1.03 dark_hi=1.18 boot_cut=0.28 hem=0.04 dark_pct=30 boot_weights=height wall_top=0.60 offset=0.012 dark_uv=$DF seal=0 drop_forearm_parts=1
b $TF $B/v2/scripts/medallion.py $PWD/$B/v2/work/robe_v3.blend $PWD/$B/v2/work/medal_v3.blend $PWD/$B/v2/work/medal_v3.json centre=-0.009,-0.140,0.386 radius=0.05 atlas=0.4077,0.0762,$RU
b $TF $B/v2/scripts/braid_fix.py $PWD/$B/v2/work/medal_v3.blend $PWD/$B/v2/work/braid_v3.blend $PWD/$B/v2/work/braid_v3.json
