"""Staff carry for the right arm on the locomotion/idle clips: work/rig_v2.blend -> work/rig_v3.blend.
Per frame the staff is placed in the body's heading frame (from the clip's hips/upper legs): upright at the right
side, grip 1.15 m above the rest floor (native pmn2sta0, staff foot just above the ground) moving with the hips,
tilted forward per clip, swept with the left arm swing (the foot trails as the right leg steps forward) and its foot
leaned outward per frame just enough (smoothed) to keep the shaft 15 mm off the legs, pouches and skirt. The grip
position is the least-wrist-strain grid point whose idle shaft clears the body by 3 cm. The right arm is solved with
staff_rig.Side('Right'); legs, spine, head and left arm stay Meshy's. Per-frame numbers: work/carry_report.json."""
import bpy, sys, os, math, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
import staff_rig as sr

CLIPS = {'Idle_9': {'tilt': 4, 'sweep': 0.0}, 'Walking': {'tilt': 6, 'sweep': 0.35},
         'Spear_Walk': {'tilt': 6, 'sweep': 0.35}, 'Running': {'tilt': 18, 'sweep': 0.25}}
GRIP_Z, FOOT_CLEAR, MARGIN = 1.15, 0.012, 0.015
HIPS_REST_Z = (sr.AW @ sr.D('Hips').head_local).z
RIGHT = sr.Side('Right')


def staff_axis(F, R, tilt_deg, out):
    t = math.radians(tilt_deg)
    return (Vector((0, 0, 1)) * math.cos(t) + F * math.sin(t) - R * out).normalized()     # top in, foot out


def carry_target(tilt, out, lat, fwd):
    hips, F, R = sr.body_frame()
    a = staff_axis(F, R, tilt, out)
    G = Vector((hips.x, hips.y, 0)) + F * fwd + R * lat
    G.z = max(GRIP_Z + (hips.z - HIPS_REST_Z), FOOT_CLEAR + a.z * sr.GRIP_FROM_FOOT)
    pole = Vector((0, 0, -1)) * 0.6 - F * 0.6 + R * 0.4
    return G, a, pole


sr.set_action('Idle_9'); sr.scene.frame_set(0)
P0 = sr.body_points(); grid = []
for lat in (0.20, 0.24, 0.28, 0.32, 0.36, 0.40):
    for fwd in (0.08, 0.14, 0.20, 0.26, 0.32):
        G, a, pole = carry_target(CLIPS['Idle_9']['tilt'], 0.02, lat, fwd)
        r = RIGHT.solve(G, a, pole)
        clr = sr.shaft_clearance(P0, G, a)
        if clr >= 0.03:                                  # idle: shaft clear of pouch/skirt/legs with room for walking
            grid.append((r['cost'], lat, fwd, round(r['sw'], 1), round(r['tw'], 1), round(clr * 1000)))
grid.sort()
print('GRID best', grid[:3])
LAT, FWD = grid[0][1], grid[0][2]
sr.scene['pmn2_carry'] = json.dumps({'lat': LAT, 'fwd': FWD, 'grip_z': GRIP_Z})
report = {}
for name, cfg in CLIPS.items():
    act, (f0, f1) = sr.set_action(name)
    swing = []
    for f in range(f0, f1 + 1):
        sr.scene.frame_set(f); hips, F, R = sr.body_frame()
        v = (sr.AW @ sr.B('LeftForeArm').head) - (sr.AW @ sr.B('LeftArm').head)
        swing.append(math.degrees(math.atan2(v.dot(F), -v.z)))
    mean = sum(swing) / len(swing)
    sweeps = [max(-10, min(10, cfg['sweep'] * (x - mean))) for x in swing]
    need = []
    for i, f in enumerate(range(f0, f1 + 1)):
        sr.scene.frame_set(f); P = sr.body_points(); out = 0.02
        while out < 0.30:
            G, a, pole = carry_target(cfg['tilt'] + sweeps[i], out, LAT, FWD)
            if sr.shaft_clearance(P, G, a) >= MARGIN:
                break
            out += 0.01
        need.append(out)
    n = len(need)
    wide = [max(need[(i + k) % n] for k in range(-2, 3)) for i in range(n)]
    lean = [max(sum(wide[(i + k) % n] for k in range(-2, 3)) / 5, need[i]) for i in range(n)]
    phi = None; rows = []
    for i, f in enumerate(range(f0, f1 + 1)):
        sr.scene.frame_set(f)
        G, a, pole = carry_target(cfg['tilt'] + sweeps[i], lean[i], LAT, FWD)
        r = RIGHT.solve(G, a, pole, phi); phi = r['phi']
        RIGHT.apply(r, f)
        rows.append({'f': f, 'lean': round(lean[i], 2), 'wrist_swing': round(r['sw'], 1), 'wrist_twist': round(r['tw'], 1),
                     'reach_miss_mm': round(r['miss'] * 1000, 1), 'staff_foot_z': round((G - a * sr.GRIP_FROM_FOOT).z, 3)})
    report[name] = rows
    print('CARRY', name, 'wrist swing max %.1f twist max %.1f reach miss max %.1f mm staff foot z min %.3f' % (
        max(r['wrist_swing'] for r in rows), max(abs(r['wrist_twist']) for r in rows),
        max(r['reach_miss_mm'] for r in rows), min(r['staff_foot_z'] for r in rows)))
json.dump(report, open(os.path.join(common.WORK, 'carry_report.json'), 'w'), indent=0)
sr.set_action('Idle_9')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
