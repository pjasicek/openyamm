"""Choose continuous elbow planes and palm rotations for a two-handed boulder grip."""
import math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
import armik


def fit(rig, records, hand, apply):
    phis = np.arange(-180, 180, 5)
    psis = np.array([0])
    result = {}
    for side, sign in [('L', 1), ('R', -1)]:
        tables = []
        geometry = []
        rotations = []
        ub, fb, hb = [f'B_{side}_{n}' for n in ['UpperArm', 'Forearm', 'Hand']]
        axis_h=(rig.data.bones[hb].matrix_local.to_3x3().inverted() @ (sum((rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(5)),Vector())/5-rig.data.bones[hb].head_local)).normalized()
        rest = (rig.data.bones[fb].matrix_local.to_3x3().inverted()
                @ rig.data.bones[hb].matrix_local.to_3x3()).inverted()
        for record in records:
            apply(record['pose'])
            Mu, Mf, Mh = [armik.W(rig, n) for n in [ub, fb, hb]]
            S, E0, W0 = [m.translation.copy() for m in [Mu, Mf, Mh]]
            a0 = (E0-S).normalized()
            bone=rig.data.bones[ub];parent=bone.parent
            upper_ref=(armik.W(rig,parent.name).to_3x3().normalized() @ parent.matrix_local.to_3x3().inverted() @ bone.matrix_local.to_3x3()).inverted()
            upper_axis=(bone.matrix_local.to_3x3().inverted() @ (rig.data.bones[fb].head_local-bone.head_local)).normalized()
            L1, L2 = (E0-S).length, (W0-E0).length
            contact = record['centre'] + Vector((sign*.30, 0, -.11))
            grip = record['grip'];pole_grip=record.get('pole_grip',grip)
            costs = np.zeros((len(phis), len(psis)))
            states = []
            frame_rotations = []
            for j, psi in enumerate(psis):
                H0=record['carry'][side]['rotation']
                T=W0.lerp(record['carry'][side]['target'],grip)+Vector((sign*.18,-.12,0))*math.sin(math.pi*grip)+Vector((sign*.04,-.04,0))*record.get('approach',0)
                Hbase = Mh.to_quaternion().slerp(H0.to_quaternion(), grip).to_matrix()
                d = T-S
                reach = d.length/(L1+L2)
                T = S+d.normalized()*min(d.length, (L1+L2)*.999)
                d = T-S
                dist, u = d.length, d.normalized()
                base = Vector((sign,0,0))
                base = (base-u*base.dot(u)).normalized()
                ref = E0-S;ref = (ref-u*ref.dot(u)).normalized()
                base = ref.slerp(base,pole_grip)
                column = []
                column_rotations = []
                for i, phi in enumerate(phis):
                    v = Quaternion(u, math.radians(float(phi)))@base
                    ca = max(-1, min(1, (L1*L1+dist*dist-L2*L2)/(2*L1*dist)))
                    E = S+L1*(u*ca+v*math.sqrt(1-ca*ca))
                    a1 = (E-S).normalized()
                    q = a0.rotation_difference(a1)
                    n0, n1 = (E0-S).cross(W0-E0), (E-S).cross(T-E)
                    if n0.length > 1e-6 and n1.length > 1e-6:
                        n0 = q@n0
                        n0 = (n0-a1*n0.dot(a1)).normalized()
                        n1 = (n1-a1*n1.dot(a1)).normalized()
                        q = Quaternion(a1, math.atan2(a1.dot(n0.cross(n1)), n0.dot(n1)))@q
                    qf = (q@(W0-E0)).rotation_difference(T-E)
                    forearm = qf.to_matrix()@q.to_matrix()@Mf.to_3x3().normalized()
                    H=Hbase
                    if 'relax_hand' in record:
                        neutral=forearm@rest.inverted()@record['pose'][hb][0].to_matrix()
                        H=Hbase.to_quaternion().slerp(neutral.to_quaternion(),record['relax_hand']).to_matrix()
                    rel = (rest@(forearm.inverted()@H)).to_quaternion()
                    sw, tw = armik.split_swing_twist(rel, axis_h)
                    swing = math.degrees(min(sw.angle, 2*math.pi-sw.angle))
                    twist = abs(math.degrees(tw))
                    column_rotations.append([list((q.to_matrix()@Mu.to_3x3().normalized()).to_quaternion()),list(forearm.to_quaternion())])
                    upper_q=(upper_ref @ q.to_matrix() @ Mu.to_3x3().normalized()).to_quaternion()
                    _,upper_tw=armik.split_swing_twist(upper_q,upper_axis)
                    upper_roll=abs(math.degrees(upper_tw))
                    deviation = 0
                    costs[i, j] = (swing+.03*swing*swing+.25*twist+.07*abs(phi)*grip
                                   +.10*deviation*grip+max(0, reach-.999)*500
                                   +max(0, swing-60)**2+max(0, twist-75)**2
                                   +.3*upper_roll+100*max(0,upper_roll-55)**2
                                   +200000*max(0,.40-sign*E.x)**2*pole_grip)
                    if record.get('endpoint') and phi!=0:costs[i,j]=np.inf
                    column.append((T, H, S+v, reach, {'reach':reach,'swing':swing,'twist':twist,'upper_roll':upper_roll,'phi':float(phi),'psi':float(psi)}))
                states.append(column)
                frame_rotations.append(column_rotations)
            tables.append(costs)
            geometry.append(states)
            rotations.append(np.array(frame_rotations)[0])
        delta_phi=(np.subtract.outer(phis,phis)+180)%360-180
        dphi=np.square(delta_phi)*.15

        dpsi = np.square((np.subtract.outer(psis, psis)+180)%360-180)*.20
        acc = tables[0].copy()
        back = []
        for frame_index,cost in enumerate(tables[1:],1):
            # Elbow coordinates change with the shoulder; continuity belongs to actual joint rotations.
            dots=np.abs(np.einsum('ikq,jkq->ijk',rotations[frame_index],rotations[frame_index-1]))
            steps=2*np.degrees(np.arccos(np.clip(dots,0,1)))
            transition=(.10*steps**2+20*np.maximum(steps-12,0)**2).sum(axis=2)
            stage = acc[None, :, :]+transition[:, :, None]
            ap = np.argmin(stage, axis=1)
            stage = np.min(stage, axis=1)[:, None, :]+dpsi[None, :, :]
            bp = np.argmin(stage, axis=2)
            acc = np.min(stage, axis=2)+cost
            back.append((ap, bp))
        i, j = np.unravel_index(int(np.argmin(acc)), acc.shape)
        path = [(i, j)]
        for ap, bp in reversed(back):
            oldj = bp[i, j]
            i, j = ap[i, oldj], oldj
            path.append((i, j))
        path.reverse()
        result[side] = [geometry[f][j][i] for f, (i, j) in enumerate(path)]
        for _ in range(4):
            old=result[side];smoothed=[old[0]]
            for f in range(1,len(old)-1):
                T,H,pole,reach,metrics=old[f]
                q=H.to_quaternion().slerp(old[f-1][1].to_quaternion().slerp(old[f+1][1].to_quaternion(),.5),.5)
                R=H;target=T
                newpole=pole.lerp(old[f-1][2].lerp(old[f+1][2],.5),.5)
                smoothed.append((target,R,newpole,reach,metrics))
            result[side]=smoothed+[old[-1]]
    return result
