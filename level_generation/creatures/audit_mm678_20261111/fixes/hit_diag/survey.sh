#!/usr/bin/env bash
# survey.sh <stem> <factor> [joints]: Hit with the upper-body rotations scaled toward Standing frame 0, region shares
# (writes the scaled copy to work.glb, overwritten each run)
s=$1; f=$2; J=${3:-'B_Spine*,B_Neck,B_Head,B_*_Clavicle'}
w=${s%%_*}; G=../../../../../assets_source/worlds/$w/models/$s.glb
python3 ../anim_tools/scale_keys.py $G work.glb --clip Hit --joints "$J" --factor $f >/dev/null
echo "$s x$f $(python3 ../anim_tools/clip_audit.py work.glb Standing Hit | tr '\n' ' ' | sed 's/hot {[^}]*}//g; s/pop [^ ]* inside [^ ]*//g' | cut -c1-230)"
