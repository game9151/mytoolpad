# Builds the engine bay and fuel tank scenes, renders them and exports hotspot outlines.
# Run:  /Applications/Blender.app/Contents/MacOS/Blender -b -P build_bay.py -- <out_dir> [percent] [samples]
import bpy, bmesh, math, json, sys, os
from mathutils import Vector, Euler
from mathutils.geometry import convex_hull_2d
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = argv[0] if argv else os.path.normpath(HERE + "/../../../assets/car-sim")
PCT = int(argv[1]) if len(argv) > 1 else 100
SAMPLES = int(argv[2]) if len(argv) > 2 else 96
DEVICE = argv[3] if len(argv) > 3 else "GPU"

for s in list(bpy.data.scenes):
    if s.name not in ("Scene",):
        bpy.data.scenes.remove(s)

M = {}
def mat(name, col, metal=0.0, rough=0.5, coat=0.0, bump=0.0, scale=60.0):
    if name in M: return M[name]
    m = bpy.data.materials.new("bay_"+name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.05
    nt.links.new(b.outputs[0], out.inputs[0])
    if bump:
        tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = scale
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(tex.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    M[name] = m; return m

paint   = mat("paint", (0.015,0.04,0.11), 0.7, 0.3, coat=1.0)
bay     = mat("baymetal", (0.012,0.025,0.06), 0.6, 0.45, coat=0.5)
underbay= mat("underbay", (0.03,0.03,0.032), 0.2, 0.7)
blackp  = mat("blackplastic", (0.03,0.03,0.032), 0, 0.5, bump=0.15, scale=400)
rubber  = mat("rubber", (0.014,0.014,0.014), 0, 0.8, bump=0.1, scale=300)
alu     = mat("alu", (0.62,0.62,0.64), 1, 0.42, bump=0.25, scale=180)
alushiny= mat("heatshield", (0.8,0.8,0.82), 1, 0.22, bump=0.4, scale=40)
steel   = mat("steel", (0.5,0.5,0.52), 1, 0.3)
darkalu = mat("darkalu", (0.16,0.16,0.18), 0.8, 0.5, bump=0.3, scale=250)
grey    = mat("conngrey", (0.42,0.43,0.45), 0, 0.45)
green   = mat("conngreen", (0.05,0.35,0.12), 0, 0.4)
brown   = mat("connbrown", (0.28,0.15,0.07), 0, 0.45)
red     = mat("red", (0.6,0.03,0.02), 0, 0.4)
yellow  = mat("yellow", (0.8,0.55,0.03), 0, 0.4)
blue    = mat("bluecap", (0.03,0.15,0.5), 0, 0.4)
white   = mat("whiteplastic", (0.75,0.72,0.62), 0, 0.5)
fluid   = mat("coolant", (0.85,0.4,0.6), 0, 0.3)
floor   = mat("floor", (0.035,0.035,0.037), 0, 0.8, bump=0.3, scale=20)
copper  = mat("brass", (0.8,0.55,0.25), 1, 0.3)

class B:
    col = None
def finish(o, m, comp=None, bevel=0.0, smooth=False):
    B.col.objects.link(o); o.data.materials.append(m)
    if bevel:
        bm = o.modifiers.new("bev", "BEVEL"); bm.width = bevel; bm.segments = 3; bm.harden_normals = True; smooth = True
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    if comp: o["comp"] = comp
    return o
def box(name, loc, size, m, comp=None, bevel=0.006, rot=(0,0,0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.rotation_euler = Euler(rot)
    return finish(o, m, comp, bevel)
def cyl(name, loc, r, depth, m, comp=None, axis='Z', segs=32, r2=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=(r if r2 is None else r2), depth=depth)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc
    if axis == 'X': o.rotation_euler = Euler((0, math.pi/2, 0))
    elif axis == 'Y': o.rotation_euler = Euler((math.pi/2, 0, 0))
    return finish(o, m, comp, bevel, smooth=True)
def tube(name, pts, r, m, comp=None, res=4):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = r; cu.bevel_resolution = res; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = Vector(p); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu); B.col.objects.link(o); cu.materials.append(m)
    if comp: o["comp"] = comp
    return o
def pin(name, loc):
    e = bpy.data.objects.new("pp:"+name, None); e.location = loc; B.col.objects.link(e); return e
def light(name, kind, loc, energy, size, target=(0,0,0.2), color=(1,1,1)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    o = bpy.data.objects.new(name, ld); B.col.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z','Y').to_euler(); return o
def camera(sc, loc, target, lens):
    cd = bpy.data.cameras.new(sc.name+"Cam"); cd.lens = lens
    cam = bpy.data.objects.new(sc.name+"Cam", cd); B.col.objects.link(cam); cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z','Y').to_euler(); sc.camera = cam; return cam
def setup_render(sc, w, h):
    r = sc.render; r.engine = 'CYCLES'; r.resolution_x = w; r.resolution_y = h; r.resolution_percentage = PCT
    sc.cycles.device = DEVICE; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    r.image_settings.file_format = 'WEBP'; r.image_settings.quality = 84
    wd = bpy.data.worlds.new(sc.name+"World"); wd.use_nodes = True
    bg = wd.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.05,0.055,0.06,1); bg.inputs[1].default_value = 0.35
    sc.world = wd

ENGINE_PREFIX = ("altfin_","altpul_","block","oil_pan","head","valve_cover","vc_rib_","oil_cap","dipstick","timing_cover","crank_pulley","alt_pulley","alternator","belt",
  "heat_shield","hs_rib_","downpipe","coil","plenum","runner_","throttle_body","tps_","map_","fuel_rail","inj","tstat_housing","ect_","ckp_",
  "harness_inj","harness_coils","harness_map","harness_tps","harness_ect","harness_ckp","lead_")
def is_engine(o): return o.type in ('MESH','CURVE') and o.name.startswith(ENGINE_PREFIX)
def wm(o):
    m = o.matrix_basis.copy()
    return wm(o.parent) @ o.matrix_parent_inverse @ m if o.parent else m
def fix_matrices(sc):
    for o in sc.objects: o.matrix_world = wm(o)
def export(sc, cam, path, LW=None, LH=None):
    fix_matrices(sc)
    dg = sc.view_layers[0].depsgraph; dg.update()
    W = LW or sc.render.resolution_x; H = LH or sc.render.resolution_y
    pts = {}
    for o in sc.objects:
        c = o.get("comp")
        if not c: continue
        ev = o.evaluated_get(dg)
        try: me = ev.to_mesh()
        except Exception: continue
        if me is None: continue
        mw = ev.matrix_world
        for v in me.vertices:
            p = world_to_camera_view(sc, cam, mw @ v.co)
            pts.setdefault(c, []).append((p.x*W, (1-p.y)*H))
        ev.to_mesh_clear()
    comps = {}
    for c, P in pts.items():
        hull = convex_hull_2d(P)
        poly = [[round(P[i][0]), round(P[i][1])] for i in hull]
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        comps[c] = {"poly": poly, "cx": round(sum(xs)/len(xs)), "cy": round(sum(ys)/len(ys)), "box": [min(xs),min(ys),max(xs),max(ys)]}
    eng = []
    for o in sc.objects:
        if not is_engine(o): continue
        ev = o.evaluated_get(dg)
        try: me = ev.to_mesh()
        except Exception: continue
        if me is None: continue
        for v in me.vertices:
            p = world_to_camera_view(sc, cam, ev.matrix_world @ v.co); eng.append((p.x*W, (1-p.y)*H))
        ev.to_mesh_clear()
    pins = {}
    for o in sc.objects:
        if o.name.startswith("pp:"):
            p = world_to_camera_view(sc, cam, o.matrix_world.translation)
            pins[o.name[3:]] = [round(p.x*W), round((1-p.y)*H)]
    with open(path, "w") as f: json.dump({"w": W, "h": H, "comps": comps, "pins": pins, "engine": ([round(min(e[0] for e in eng)), round(min(e[1] for e in eng)), round(max(e[0] for e in eng)), round(max(e[1] for e in eng))] if eng else None)}, f)

# ======================= ENGINE BAY =======================
sc = bpy.data.scenes.new("EngineBay"); B.col = sc.collection
if bpy.context.window: bpy.context.window.scene = sc

box("floor", (0,0,-0.35), (4,4,0.02), floor, bevel=0)
box("bay_floor", (0,0.02,-0.05), (1.6,1.36,0.02), underbay, bevel=0)
box("subframe", (0,-0.1,0.0), (1.3,0.12,0.08), underbay, bevel=0.01)
for s in (-1,1):
    box("inner_fender_%d"%s, (s*0.80,0,0.2), (0.05,1.4,0.55), bay, bevel=0.01)
    box("fender_%d"%s, (s*0.93,-0.02,0.47), (0.22,1.55,0.06), paint, bevel=0.025)
    box("fender_side_%d"%s, (s*1.03,-0.02,0.2), (0.03,1.55,0.5), paint, bevel=0.01)
    cyl("strut_%d"%s, (s*0.71,0.36,0.40), 0.085, 0.12, bay)
    cyl("strut_top_%d"%s, (s*0.71,0.36,0.47), 0.05, 0.02, rubber)
    for i in range(3):
        a = i*2*math.pi/3
        cyl("strut_nut_%d_%d"%(s,i), (s*0.71+0.065*math.cos(a),0.36+0.065*math.sin(a),0.472), 0.011, 0.018, steel, segs=6)
box("firewall", (0,0.70,0.25), (1.62,0.04,0.65), bay, bevel=0.01)
box("firewall_pad", (0,0.675,0.22), (1.3,0.01,0.45), rubber, bevel=0.003)
box("cowl", (0,0.78,0.53), (1.65,0.18,0.03), blackp, bevel=0.01)
for i in range(18):
    box("cowl_slot_%d"%i, (-0.68+i*0.08,0.78,0.546), (0.05,0.12,0.004), rubber, bevel=0)
# ---- car body behind the bay: raised bonnet, windscreen, wipers, body sides ----
glass  = mat("glass", (0.02,0.03,0.035), 0.0, 0.03)
felt   = mat("hoodpad", (0.035,0.035,0.038), 0, 0.95, bump=0.5, scale=120)
dash_m = mat("dashboard", (0.025,0.025,0.028), 0, 0.7)
for s_ in (-1,1):
    box("body_rear_%d"%s_, (s_*0.93,1.25,0.47), (0.22,1.0,0.06), paint, bevel=0.025)
    box("body_side_rear_%d"%s_, (s_*1.03,1.25,0.2), (0.03,1.0,0.5), paint, bevel=0.01)
    tube("a_pillar_%d"%s_, [(s_*0.86,0.92,0.56),(s_*0.80,1.30,0.95),(s_*0.74,1.62,1.22)], 0.04, paint)
box("windscreen", (0,1.27,0.89), (1.62,0.95,0.008), glass, bevel=0, rot=(math.radians(-41),0,0))
box("dash_top", (0,1.35,0.72), (1.5,0.5,0.06), dash_m, bevel=0.03)
box("cowl_panel", (0,0.90,0.56), (1.75,0.16,0.03), blackp, bevel=0.012, rot=(math.radians(-12),0,0))
for s_,x0 in ((-1,-0.45),(1,0.25)):
    tube("wiper_arm_%d"%s_, [(x0,0.88,0.585),(x0+0.18,0.96,0.64),(x0+0.42,1.02,0.69)], 0.008, blackp)
    cyl("wiper_pivot_%d"%s_, (x0,0.88,0.585), 0.018, 0.02, blackp)
th = math.radians(78); hinge = Vector((0,0.86,0.58)); d = Vector((0,-math.cos(th),math.sin(th)))
inner = Vector((0,-math.sin(th),-math.cos(th)))  # underside normal, faces the camera
c = hinge + d*0.66
box("bonnet", tuple(c), (1.82,1.32,0.025), paint, bevel=0.012, rot=(-th,0,0))
box("bonnet_pad", tuple(c + inner*0.016 + d*0.02), (1.5,1.0,0.012), felt, bevel=0.01, rot=(-th,0,0))
for i in range(3):
    box("bonnet_brace_%d"%i, tuple(hinge + d*(0.25+i*0.4) + inner*0.03), (1.6,0.05,0.03), paint, bevel=0.008, rot=(-th,0,0))
box("bonnet_latch", tuple(hinge + d*1.27 + inner*0.03), (0.1,0.04,0.04), steel, bevel=0.005, rot=(-th,0,0))
for s_ in (-1,1):
    top = hinge + d*0.5; top.x = s_*0.84
    tube("bonnet_strut_%d"%s_, [(s_*0.84,0.70,0.50), tuple((Vector((s_*0.84,0.70,0.50))+top)/2), tuple(top)], 0.012, steel)
box("rad_support", (0,-0.70,0.45), (1.62,0.08,0.05), bay, bevel=0.01)
box("front_bumper_top", (0,-0.83,0.40), (1.95,0.14,0.08), paint, bevel=0.03)
box("radiator", (0,-0.64,0.22), (1.15,0.04,0.38), darkalu, bevel=0.004, comp="fan")
box("rad_tank_l", (-0.6,-0.64,0.22), (0.06,0.06,0.4), blackp, bevel=0.01)
box("rad_tank_r", (0.6,-0.64,0.22), (0.06,0.06,0.4), blackp, bevel=0.01)
cyl("rad_cap", (0.6,-0.64,0.44), 0.025, 0.03, steel, comp="fan")
cyl("fan_shroud", (0.12,-0.585,0.22), 0.17, 0.04, blackp, axis='Y', comp="fan")
box("hood_latch", (0,-0.67,0.49), (0.12,0.05,0.03), steel, bevel=0.005)

box("block", (0,0.02,0.20), (0.58,0.30,0.34), darkalu, bevel=0.012)
box("oil_pan", (0,0.02,0.0), (0.56,0.28,0.08), darkalu, bevel=0.01)
box("head", (0,0.02,0.40), (0.60,0.28,0.08), alu, bevel=0.01)
box("valve_cover", (0,0.03,0.47), (0.58,0.23,0.07), blackp, bevel=0.03)
for i in range(3):
    box("vc_rib_%d"%i, (-0.14+i*0.14,0.03,0.508), (0.01,0.2,0.008), blackp, bevel=0.003)
cyl("oil_cap", (-0.27,0.10,0.515), 0.03, 0.025, yellow)
tube("dipstick", [(-0.25,-0.13,0.15),(-0.26,-0.2,0.4),(-0.25,-0.22,0.52)], 0.006, steel)
cyl("dipstick_handle", (-0.25,-0.22,0.53), 0.014, 0.012, yellow)
box("timing_cover", (-0.31,0.02,0.27), (0.05,0.28,0.38), blackp, bevel=0.02)
cyl("crank_pulley", (-0.35,-0.06,0.12), 0.075, 0.03, steel, axis='X')
cyl("alt_pulley", (-0.35,-0.04,0.36), 0.035, 0.03, steel, axis='X', comp="alt")
cyl("alternator", (-0.40,-0.04,0.36), 0.075, 0.12, alu, axis='X', comp="alt")
box("belt", (-0.36,-0.05,0.24), (0.025,0.015,0.24), rubber, bevel=0.004, rot=(0.1,0,0))
# spinning alternator: slots and a fan ring parented to a rotating empty
ALT_ROT = bpy.data.objects.new("alt_rot", None); B.col.objects.link(ALT_ROT); ALT_ROT.location = (-0.40,-0.04,0.36)
for i in range(10):
    a = i*2*math.pi/10
    f = box("altfin_%d"%i, (0, 0.077*math.cos(a), 0.077*math.sin(a)), (0.10,0.012,0.006), darkalu, bevel=0.001, rot=(a,0,0))
    f.parent = ALT_ROT
    f["comp"] = "alt"
for i in range(6):
    a = i*2*math.pi/6
    h = box("altpul_%d"%i, (0.05, 0.026*math.cos(a), 0.026*math.sin(a)), (0.034,0.008,0.008), steel, bevel=0.001)
    h.parent = ALT_ROT
box("heat_shield", (0,0.19,0.30), (0.52,0.06,0.2), alushiny, bevel=0.01)
for i in range(6):
    box("hs_rib_%d"%i, (-0.22+i*0.088,0.222,0.30), (0.012,0.006,0.18), alushiny, bevel=0.002)
tube("downpipe", [(0.2,0.22,0.2),(0.28,0.35,0.05),(0.3,0.5,-0.05)], 0.04, alushiny)

for n in range(1,5):
    x = -0.21 + (n-1)*0.14; c = "coil%d" % n
    cyl(c+"_body", (x,0.02,0.52), 0.024, 0.09, blackp, comp=c)
    box(c+"_head", (x,0.0,0.565), (0.07,0.075,0.03), blackp, comp=c, bevel=0.008)
    box(c+"_conn", (x,-0.045,0.565), (0.035,0.025,0.025), grey, comp=c, bevel=0.004)
    box(c+"_tab", (x,-0.06,0.575), (0.016,0.008,0.012), green, comp=c, bevel=0.002)
    cyl(c+"_bolt", (x+0.028,0.045,0.583), 0.007, 0.006, steel, segs=6, comp=c)

cyl("plenum", (0.0,-0.31,0.45), 0.075, 0.56, blackp, axis='X')
cyl("plenum_cap_l", (-0.28,-0.31,0.45), 0.077, 0.02, blackp, axis='X')
for n in range(1,5):
    x = -0.21 + (n-1)*0.14
    tube("runner_%d"%n, [(x,-0.30,0.47),(x,-0.24,0.53),(x,-0.17,0.47),(x,-0.14,0.40)], 0.033, blackp)
cyl("throttle_body", (0.32,-0.31,0.45), 0.05, 0.08, alu, axis='X')
box("tps_body", (0.33,-0.37,0.45), (0.05,0.02,0.06), blackp, comp="tps", bevel=0.006)
box("tps_conn", (0.33,-0.385,0.47), (0.03,0.02,0.022), grey, comp="tps", bevel=0.003)
box("tps_tab", (0.33,-0.395,0.478), (0.012,0.006,0.008), green, comp="tps", bevel=0.002)
tube("intake_duct", [(0.36,-0.31,0.45),(0.44,-0.31,0.47),(0.50,-0.36,0.44)], 0.055, rubber, comp="hose")
for i in range(5):
    cyl("duct_rib_%d"%i, (0.39+i*0.02,-0.31,0.455), 0.058, 0.006, rubber, axis='X', comp="hose")
box("airbox", (0.57,-0.40,0.36), (0.25,0.30,0.18), blackp, bevel=0.025)
box("airbox_lid", (0.57,-0.40,0.46), (0.26,0.31,0.03), blackp, bevel=0.012)
for i in range(4):
    cyl("airbox_clip_%d"%i, (0.45 if i<2 else 0.69,-0.5 if i%2 else -0.3,0.45), 0.008, 0.03, steel)
box("map_body", (-0.10,-0.31,0.535), (0.05,0.04,0.025), blackp, comp="map", bevel=0.006)
box("map_conn", (-0.10,-0.345,0.54), (0.03,0.025,0.022), grey, comp="map", bevel=0.003)
box("map_tab", (-0.10,-0.358,0.55), (0.012,0.006,0.008), green, comp="map", bevel=0.002)
cyl("fuel_rail", (0.0,-0.155,0.445), 0.012, 0.50, steel, axis='X')
tube("fuel_line", [(0.25,-0.155,0.445),(0.32,-0.16,0.44),(0.36,-0.05,0.30),(0.4,0.2,0.1)], 0.006, steel)
for n in range(1,5):
    x = -0.21 + (n-1)*0.14 + 0.06; c = "inj%d" % n
    cyl(c+"_body", (x,-0.155,0.415), 0.012, 0.06, blackp, comp=c)
    box(c+"_conn", (x,-0.18,0.43), (0.026,0.03,0.022), brown, comp=c, bevel=0.004)
    box(c+"_tab", (x,-0.197,0.437), (0.012,0.006,0.008), grey, comp=c, bevel=0.002)

cyl("tstat_housing", (0.34,0.04,0.42), 0.035, 0.07, alu, axis='X', comp="tstat")
tube("upper_hose", [(0.37,0.04,0.42),(0.50,-0.05,0.44),(0.56,-0.45,0.42),(0.58,-0.62,0.40)], 0.022, rubber)
cyl("ect_body", (0.34,0.04,0.47), 0.011, 0.04, copper, comp="ect")
box("ect_conn", (0.34,0.04,0.50), (0.028,0.024,0.022), grey, comp="ect", bevel=0.004)
box("ect_tab", (0.34,0.022,0.507), (0.01,0.006,0.008), green, comp="ect", bevel=0.002)
tube("lower_hose", [(0.28,-0.1,0.10),(0.45,-0.5,0.08),(0.55,-0.62,0.06)], 0.022, rubber)
tube("heater_hose1", [(0.33,0.10,0.40),(0.40,0.45,0.42),(0.30,0.66,0.35)], 0.012, rubber)
tube("heater_hose2", [(0.30,0.12,0.30),(0.36,0.45,0.34),(0.24,0.66,0.32)], 0.012, rubber)

cyl("ckp_body", (-0.345,-0.15,0.17), 0.014, 0.05, blackp, comp="ckp", axis='X')
box("ckp_flange", (-0.335,-0.15,0.17), (0.012,0.045,0.03), blackp, comp="ckp", bevel=0.003)
box("ckp_conn", (-0.38,-0.15,0.17), (0.03,0.028,0.024), grey, comp="ckp", bevel=0.003)

box("battery", (-0.56,-0.40,0.26), (0.18,0.27,0.22), blackp, comp="bat", bevel=0.01)
box("battery_top", (-0.56,-0.40,0.375), (0.175,0.265,0.02), blackp, comp="bat", bevel=0.005)
box("battery_sticker", (-0.53,-0.40,0.386), (0.08,0.14,0.002), yellow, comp="bat", bevel=0)
cyl("bat_pos_post", (-0.60,-0.48,0.395), 0.011, 0.025, copper, comp="bat")
cyl("bat_pos_cover", (-0.60,-0.48,0.405), 0.026, 0.03, red, comp="bat", r2=0.018)
cyl("bat_neg_post", (-0.60,-0.32,0.395), 0.011, 0.025, copper, comp="bat")
box("bat_neg_clamp", (-0.60,-0.32,0.40), (0.04,0.03,0.015), steel, comp="bat", bevel=0.003)
box("battery_tray", (-0.56,-0.40,0.14), (0.22,0.31,0.02), blackp, bevel=0.004)
box("battery_bracket", (-0.56,-0.40,0.39), (0.03,0.29,0.006), steel, bevel=0.002)
pin("bat.pos", (-0.60,-0.48,0.415)); pin("alt.out", (-0.40,-0.11,0.40)); pin("bat.neg", (-0.60,-0.32,0.41))
tube("bat_neg_cable", [(-0.60,-0.32,0.40),(-0.66,-0.25,0.38),(-0.72,-0.1,0.3)], 0.008, rubber)
tube("bat_pos_cable", [(-0.60,-0.48,0.41),(-0.62,-0.58,0.36),(-0.45,-0.55,0.25),(-0.36,-0.2,0.12)], 0.009, red)

box("fuse_box", (-0.60,0.06,0.37), (0.18,0.24,0.11), blackp, comp="fuse", bevel=0.012)
box("fuse_lid", (-0.60,0.06,0.43), (0.185,0.245,0.02), blackp, comp="fuse", bevel=0.008)
box("fuse_label", (-0.60,0.06,0.441), (0.10,0.12,0.002), white, comp="fuse", bevel=0)
box("fuse_latch", (-0.60,-0.065,0.42), (0.04,0.01,0.03), blackp, comp="fuse", bevel=0.003)
tube("fuse_feed", [(-0.60,-0.48,0.41),(-0.66,-0.2,0.42),(-0.64,-0.06,0.42)], 0.007, red)

box("ecm_bracket", (0.58,0.46,0.33), (0.24,0.18,0.01), steel, bevel=0.002)
box("ecm", (0.58,0.46,0.37), (0.22,0.16,0.06), alu, comp="ecu", bevel=0.006)
for i in range(7):
    box("ecm_fin_%d"%i, (0.49+i*0.03,0.46,0.405), (0.008,0.15,0.012), alu, comp="ecu", bevel=0.001)
box("ecm_conn", (0.58,0.365,0.37), (0.17,0.035,0.05), blackp, comp="ecu", bevel=0.006)
box("ecm_conn_lever", (0.58,0.35,0.39), (0.18,0.006,0.012), grey, comp="ecu", bevel=0.002)

box("coolant_res", (0.62,0.08,0.34), (0.12,0.18,0.14), white, bevel=0.03)
box("coolant_level", (0.62,0.08,0.31), (0.121,0.181,0.08), fluid, bevel=0.03)
cyl("coolant_cap", (0.62,0.05,0.42), 0.03, 0.025, blue)
cyl("brake_booster", (-0.36,0.60,0.30), 0.14, 0.12, darkalu, axis='Y')
cyl("master_cyl", (-0.36,0.50,0.30), 0.03, 0.12, alu, axis='Y')
box("brake_res", (-0.36,0.48,0.36), (0.09,0.06,0.06), white, bevel=0.015)
cyl("brake_cap", (-0.36,0.48,0.40), 0.022, 0.02, yellow)
box("washer_bottle", (0.66,-0.15,0.30), (0.10,0.12,0.16), white, bevel=0.03)
cyl("washer_cap", (0.66,-0.15,0.39), 0.018, 0.02, blue)

H = rubber
tube("harness_main", [(0.58,0.34,0.37),(0.45,0.25,0.46),(0.20,0.15,0.53),(-0.10,0.14,0.54),(-0.36,0.14,0.50),(-0.52,0.10,0.45)], 0.014, H)
tube("harness_inj", [(0.30,0.05,0.52),(0.30,-0.08,0.51),(0.18,-0.12,0.48),(-0.20,-0.12,0.48),(-0.30,-0.12,0.45)], 0.011, H)
tube("harness_ckp", [(-0.30,-0.12,0.45),(-0.38,-0.14,0.30),(-0.38,-0.15,0.19)], 0.007, H)
tube("harness_coils", [(-0.30,-0.07,0.58),(0.25,-0.07,0.585)], 0.009, H)
tube("harness_map", [(-0.05,-0.12,0.48),(-0.08,-0.30,0.56),(-0.10,-0.36,0.54)], 0.006, H)
tube("harness_tps", [(0.25,-0.12,0.48),(0.30,-0.30,0.52),(0.33,-0.40,0.47)], 0.006, H)
tube("harness_ect", [(0.34,0.10,0.53),(0.34,0.05,0.515)], 0.006, H)
for n in range(1,5):
    x = -0.21 + (n-1)*0.14
    tube("lead_coil%d"%n, [(x,-0.07,0.585),(x,-0.065,0.575),(x,-0.058,0.567)], 0.005, H)
    xi = x+0.06
    tube("lead_inj%d"%n, [(xi,-0.12,0.48),(xi,-0.17,0.46),(xi,-0.19,0.435)], 0.005, H)

light("KeyPanel", 'AREA', (0.2,-0.4,2.4), 260, 2.2)
light("Fill", 'AREA', (-1.6,-1.2,1.4), 60, 1.5, color=(0.85,0.9,1))
light("Rim", 'AREA', (1.2,1.6,1.6), 90, 1.2, color=(1,0.92,0.8))
PAINT_MATS = {"bay_paint", "bay_baymetal"}
def is_paint(o): return o.type in ('MESH','CURVE') and any(m and m.name in PAINT_MATS for m in o.data.materials)
# camera views: name, file suffix, camera position, target, lens
VIEWS = [("front", "", (0,-1.55,1.70), (0,0.10,0.42), 33),
         ("top", "-top", (0,-0.12,2.75), (0,0.02,0.20), 31),
         ("side", "-side", (-1.45,-1.25,1.55), (-0.04,0.05,0.34), 30)]
ONLY = os.environ.get("VIEWS")
PASSES = set((os.environ.get("PASSES") or "main,engine,paint,alt").split(","))
cams = {}
for vname, suf, loc, tgt, lens in VIEWS:
    cams[vname] = camera(sc, loc, tgt, lens)
setup_render(sc, 3000, 2001)
sc.render.image_settings.quality = 88

# ======================= FUEL TANK ACCESS =======================
st = bpy.data.scenes.new("TankAccess"); B.col = st.collection
tankm = mat("tank", (0.035,0.035,0.035), 0, 0.6, bump=0.2, scale=30)
carpet = mat("carpet", (0.06,0.06,0.065), 0, 0.95, bump=0.6, scale=900)
box("carpet", (0,0,-0.02), (1.2,0.9,0.02), carpet, bevel=0)
box("access_hole", (0,0,-0.005), (0.5,0.4,0.01), underbay, bevel=0.02)
box("tank_top", (0,0,-0.03), (0.48,0.38,0.02), tankm, bevel=0.01)
cyl("pump_ring", (0,0,0.0), 0.12, 0.02, steel, segs=48)
for i in range(8):
    a = i*math.pi/4
    cyl("ring_bolt_%d"%i, (0.105*math.cos(a),0.105*math.sin(a),0.014), 0.008, 0.01, steel, segs=6)
cyl("pump_flange", (0,0,0.015), 0.095, 0.02, white, segs=48, comp="pump")
cyl("pump_outlet", (0.045,0.03,0.04), 0.012, 0.05, white, comp="pump")
box("pump_conn", (-0.04,-0.03,0.04), (0.045,0.03,0.03), grey, comp="pump", bevel=0.004)
box("pump_tab", (-0.04,-0.05,0.05), (0.016,0.008,0.01), green, comp="pump", bevel=0.002)
tube("pump_feed", [(0.045,0.03,0.065),(0.08,0.06,0.07),(0.25,0.12,0.03)], 0.007, rubber)
tube("pump_loom", [(-0.04,-0.01,0.05),(-0.12,0.06,0.06),(-0.3,0.15,0.03)], 0.008, rubber)
light("TKey", 'AREA', (0.2,-0.3,1.2), 70, 1.2)
light("TFill", 'AREA', (-0.8,0.4,0.9), 18, 1.0)
cam2 = camera(st, (0,-0.38,0.62), (0,0,0.0), 40)
setup_render(st, 900, 640)
st.render.filepath = OUT + "/tank.webp"

# ======================= RADIATOR AND COOLING FAN (seen from the engine side) =======================
sr = bpy.data.scenes.new("RadiatorFan"); B.col = sr.collection
fins = mat("radfins", (0.12,0.12,0.13), 0.9, 0.55, bump=0.8, scale=900)
box("r_floor", (0,0,-0.5), (3,3,0.02), floor, bevel=0)
box("r_core", (0,0.03,0), (1.0,0.03,0.42), fins, bevel=0.004)
for s_ in (-1,1):
    box("r_tank_%d"%s_, (s_*0.53,0.03,0), (0.07,0.07,0.46), blackp, bevel=0.012)
cyl("r_cap", (0.53,0.03,0.25), 0.03, 0.035, steel)
tube("r_upper_hose", [(0.53,-0.02,0.15),(0.45,-0.25,0.2),(0.35,-0.45,0.25)], 0.025, rubber)
tube("r_lower_hose", [(-0.53,-0.02,-0.15),(-0.45,-0.25,-0.2),(-0.35,-0.45,-0.25)], 0.025, rubber)
box("r_shroud", (0.0,-0.005,0.0), (0.82,0.03,0.40), blackp, bevel=0.02)
cyl("r_ring", (0.0,-0.03,0.0), 0.185, 0.03, rubber, axis='Y', segs=64)
cyl("r_ring_in", (0.0,-0.032,0.0), 0.172, 0.034, floor, axis='Y', segs=64)
for i in range(4):
    a = i*math.pi/2+math.pi/4
    box("r_strut_%d"%i, (0.10*math.cos(a),-0.06,0.10*math.sin(a)), (0.2,0.012,0.014), blackp, bevel=0.003, rot=(0,-a,0))
cyl("r_motor", (0,-0.08,0), 0.05, 0.07, darkalu, axis='Y', comp="fan")
box("r_conn", (0.0,-0.125,0.065), (0.05,0.03,0.03), grey, comp="fan", bevel=0.004)
box("r_tab", (0.0,-0.125,0.085), (0.018,0.01,0.008), green, comp="fan", bevel=0.002)
tube("r_loom", [(0.0,-0.14,0.065),(0.12,-0.2,0.18),(0.3,-0.3,0.3)], 0.008, rubber)
FAN_ROT = bpy.data.objects.new("fan_rot", None); B.col.objects.link(FAN_ROT); FAN_ROT.location = (0,-0.05,0)
FAN_ROT.rotation_mode = 'XYZ'
hub = cyl("r_hub", (0,0,0), 0.04, 0.03, blackp, axis='Y'); hub.parent = FAN_ROT; hub.location = (0,0,0)
for i in range(7):
    a = i*2*math.pi/7
    bl = box("r_blade_%d"%i, (0.1*math.cos(a), 0, 0.1*math.sin(a)), (0.13,0.006,0.055), blackp, bevel=0.004, rot=(0.0,-a,0.0))
    bl.rotation_mode = 'YXZ'; bl.rotation_euler = (0.45,-a,0.0)
    bl.parent = FAN_ROT
light("RKey", 'AREA', (0.3,-1.2,0.9), 45, 1.6, target=(0,0,0))
light("RFill", 'AREA', (-0.9,-0.7,0.4), 10, 1.0, target=(0,0,0))
cam3 = camera(sr, (0.0,-1.05,0.38), (0,0,0.0), 40)
setup_render(sr, 900, 640)
sr.render.filepath = OUT + "/radiator.webp"

def holdout_all(scene, keep):
    for o in scene.objects:
        if o.type in ('MESH','CURVE'): o.is_holdout = not keep(o)
def crop_box(scene, cam, objs, LW, LH):
    fix_matrices(scene)
    xs=[];ys=[]
    for o in objs:
        for v in o.data.vertices:
            q = world_to_camera_view(scene, cam, o.matrix_world @ v.co); xs.append(q.x); ys.append(q.y)
    m=0.01; x0,x1,y0,y1 = max(0,min(xs)-m),min(1,max(xs)+m),max(0,min(ys)-m),min(1,max(ys)+m)
    r = scene.render; r.use_border = True; r.use_crop_to_border = True
    r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = x0,x1,y0,y1
    return [round(x0*LW),round((1-y1)*LH),round(x1*LW),round((1-y0)*LH)]
def reset(scene):
    for o in scene.objects:
        if o.type in ('MESH','CURVE'): o.is_holdout = False
    scene.render.film_transparent = False; scene.render.image_settings.color_mode = 'RGB'; scene.render.use_border = False

for vname, suf, loc, tgt, lens in VIEWS:
    if ONLY and vname not in ONLY.split(","): continue
    cam = cams[vname]; sc.camera = cam
    jpath = OUT + "/bay%s.json" % suf
    export(sc, cam, jpath, 2000, 1334)
    if SAMPLES <= 0: continue
    reset(sc); sc.render.filepath = OUT + "/bay%s.webp" % suf
    if "main" in PASSES: bpy.ops.render.render(write_still=True, scene=sc.name)
    # engine-only layer
    holdout_all(sc, is_engine); sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = OUT + "/bay-engine%s.webp" % suf
    if "engine" in PASSES: bpy.ops.render.render(write_still=True, scene=sc.name)
    # paint mask (alpha = painted body panels), so each car can be a different colour
    holdout_all(sc, is_paint); sc.render.filepath = OUT + "/paint%s.webp" % suf
    if "paint" in PASSES:
        smp = sc.cycles.samples; sc.cycles.samples = 8
        bpy.ops.render.render(write_still=True, scene=sc.name); sc.cycles.samples = smp
    # spinning alternator sprite
    ACC = ("alternator","alt_pulley","altfin_","altpul_")
    holdout_all(sc, lambda o: o.name.startswith(ACC))
    box_ = crop_box(sc, cam, [o for o in sc.objects if o.type=='MESH' and o.name.startswith(ACC)], 2000, 1334)
    with open(jpath) as f: J=json.load(f)
    J["acc"]={"box":box_,"frames":6}
    with open(jpath,"w") as f: json.dump(J,f)
    for i in range(6 if "alt" in PASSES else 0):
        ALT_ROT.rotation_euler = (i*(2*math.pi/10)/6,0,0)
        sc.render.filepath = OUT + "/alt%s_%d.webp" % (suf, i)
        bpy.ops.render.render(write_still=True, scene=sc.name)
    ALT_ROT.rotation_euler = (0,0,0); reset(sc)

if not ONLY or "tank" in ONLY.split(","):
    export(st, cam2, OUT + "/tank.json")
    if SAMPLES > 0: bpy.ops.render.render(write_still=True, scene=st.name)
if not ONLY or "radiator" in ONLY.split(","):
    export(sr, cam3, OUT + "/radiator.json")
    if SAMPLES > 0:
        reset(sr); bpy.ops.render.render(write_still=True, scene=sr.name)
        blades = [o for o in sr.objects if o.name.startswith(("r_blade_","r_hub"))]
        holdout_all(sr, lambda o: o.name.startswith(("r_blade_","r_hub")))
        sr.render.film_transparent = True; sr.render.image_settings.color_mode = 'RGBA'
        fb = crop_box(sr, cam3, blades, 900, 640)
        with open(OUT + "/radiator.json") as f: J=json.load(f)
        J["fan"]={"box":fb,"frames":6}
        with open(OUT + "/radiator.json","w") as f: json.dump(J,f)
        for i in range(6):
            FAN_ROT.rotation_euler = (0, i*(2*math.pi/7)/6, 0)
            sr.render.filepath = OUT + "/fan_%d.webp" % i
            bpy.ops.render.render(write_still=True, scene=sr.name)
        FAN_ROT.rotation_euler = (0,0,0); reset(sr)

bpy.ops.wm.save_as_mainfile(filepath=HERE + "/engine-bay.blend")
print("DONE")
