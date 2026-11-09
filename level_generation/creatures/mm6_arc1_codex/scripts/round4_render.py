"""Final runtime textured sheets and native landmarks, using CPU Cycles on this host."""
import bpy,sys,runpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/round4_gates.py'),run_name='__main__')
code=(P/'scripts/round3_native_probe.py').read_text().replace("'round2'","'round3'").replace("'round3',P/'work","'round4',P/'work").replace("review/round3/baseline/work","review/round4/baseline/work").replace("label=='round3'","label=='round4'").replace("review/round3/native_pose.json","review/round4/native_pose.json")
exec(compile(code,str(P/'scripts/round3_native_probe.py'),'exec'),{'__file__':str(P/'scripts/round3_native_probe.py'),'__name__':'__main__'})
n=json.loads((P/'review/round4/native_pose.json').read_text());rig=bpy.data.objects['Rig']
axis=rig.pose.bones['Bow'].matrix.to_3x3().col[2].normalized()
n['round4']['bow_azimuth_deg']=math.degrees(math.atan2(axis.x,-axis.y));n['native']['bow_azimuth_deg']=0.
n['native']['front_tip_elevation_deg']=90-n['native']['bow_tilt_deg'];n['round4']['front_tip_elevation_deg']=-18.
pts=n['round4']['landmarks_m']
u=[b-a for a,b in zip(pts['B_L_UpperArm'],pts['B_L_Forearm'])];f=[b-a for a,b in zip(pts['B_L_Forearm'],pts['B_L_Hand'])]
n['round4']['upper_side_deg']=math.degrees(math.atan2(-u[1],-u[2]));n['round4']['forearm_side_deg']=math.degrees(math.atan2(-f[1],-f[2]))
n['round4']['elbow_bend_side_deg']=abs(n['round4']['forearm_side_deg']-n['round4']['upper_side_deg'])
left=rig.pose.bones['B_L_Hand'].head;right=rig.pose.bones['B_R_Hand'].head.copy();right.x=-right.x
n['round4']['mirrored_right_wrist_error_m']=(left-right).length
n['round4']['mirrored_right_wrist_front_error_m']=math.hypot(left.x-right.x,left.z-right.z)
n['round4']['wrist_forward_of_right_m']=right.y-left.y
n['decision']='R4 user-approved sketch supersedes the erroneous vertical carry of rounds 2–3. Match the accepted right arm in front projection, with the native slight forward elbow bend in side view; bow 72 degrees from vertical, along forward -Y, front tip lower, string underneath. Native hip estimates are uncertain by 6 pixels; native azimuth is inferred from the end-on front view, not an exact calibrated 3D measurement.'
(P/'review/round4/native_pose.json').write_text(json.dumps(n,indent=2))
import common
def cpu(scene,textured=False):
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
 scene.render.threads_mode='FIXED';scene.render.threads=4
 if scene.world is None:scene.world=bpy.data.worlds.new('ReviewWorld')
 scene.world.use_nodes=True
 bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.7,.7,.7,1);bg.inputs['Strength'].default_value=.8
 scene.view_settings.view_transform='Standard'
common.workbench_clay=cpu
code=(P/'scripts/render_final.py').read_text().replace('bpy.ops.import_scene.gltf','bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf')
exec(compile(code,str(P/'scripts/render_final.py'),'exec'),{'__file__':str(P/'scripts/render_final.py'),'__name__':'__main__'})
sc=bpy.context.scene;sc.render.film_transparent=True
common.render_views(str(P/'review/round4/standing_alpha'),.85,1.85,views=('front','left'),resolution=(680,1000))
sc.render.film_transparent=False
common.render_views(str(P/'review/round4/soles'),.12,.50,views=('front','left'),resolution=(800,600))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_authoring.blend'))
code=(P/'scripts/release_gate.py').read_text().replace('round3/contact_gates.json','round4/shared_final/gates.json').replace('review/release_gate.json','review/round4/release_gate.json')
exec(compile(code,str(P/'scripts/release_gate.py'),'exec'),{'__file__':str(P/'scripts/release_gate.py'),'__name__':'__main__'})
sys.argv=['glb_hand_closeups.py','--',str(P/'review/viewer/mm6_arc1_a.glb'),str(P/'review/hand'),'Standing:0','Attack:1.2','Cast:1.2','Death:0.7']
runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')

# Repeat the existing switch-size silhouette measurement with current actions and unchanged selected geometry.
import shutil
D=P/'review/round4/reduction';D.mkdir(exist_ok=True)
shutil.copy2(P/'review/round3/reduction/camera.json',D/'camera.json')
shutil.copy2(P/'work/round3/unreduced.blend',P/'work/round4/unreduced.blend')
sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(P/'work/round4/unreduced.blend')]
runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
code=(P/'scripts/round2_assembled_metrics.py').read_text().replace('review/round2/reduction','review/round4/reduction').replace("W/('unreduced.blend'if label=='high'else f'lod{level}.blend')","(P/'work/round4/unreduced.blend'if label=='high'else W/f'lod{level}.blend')")
exec(compile(code,str(P/'scripts/round2_assembled_metrics.py'),'exec'),{'__file__':str(P/'scripts/round2_assembled_metrics.py'),'__name__':'__main__'})
