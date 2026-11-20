exec(open('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m416_claude/scripts/string_probe.py').read())
bpy.context.view_layer.update()
for n in ['B_R_Hand','Crossbow','StringL']:
 print(n,'BASIS',r.pose.bones[n].matrix_basis,'POSE',r.pose.bones[n].matrix,'REST',r.data.bones[n].matrix_local)
for n in ['CrossbowMesh','StringLMesh','StringRMesh']:
 o=bpy.data.objects[n];print(n,'OBJECT',o.matrix_world,'groups',[(g.name,g.index) for g in o.vertex_groups], 'mods',[(m.name,m.type) for m in o.modifiers]);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=o.data.vertices[0];bone=n.removesuffix('Mesh');print('EXPECTED',r.pose.bones[bone].matrix@r.data.bones[bone].matrix_local.inverted()@v.co,'ACTUAL',me.vertices[0].co);ev.to_mesh_clear()
