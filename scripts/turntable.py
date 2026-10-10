"""Blender: .glb -> clay turntable renders (N views around the product), used as geometry/angle reference.

  blender -b -P scripts/turntable.py -- output/3d/sofa_00001_.glb renders/turntable 8
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

glb, out_dir, n = sys.argv[sys.argv.index("--") + 1:][:3]
n = int(n)
out = Path(out_dir).resolve()   # Blender reads relative render paths from the .blend location, not the cwd
out.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]

# normalise: centre on the floor, longest side = 2 m
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
s = 2.0 / max(hi - lo)
root = bpy.data.objects.new("root", None)
bpy.context.scene.collection.objects.link(root)
for o in objs:
    o.parent = root
root.scale = (s, s, s)
root.location = -Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s
bpy.context.view_layer.update()
height = (hi.z - lo.z) * s

clay = bpy.data.materials.new("clay")
clay.use_nodes = True
bsdf = clay.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.72, 0.72, 0.70, 1)
bsdf.inputs["Roughness"].default_value = 0.85
for o in objs:
    o.data.materials.clear()
    o.data.materials.append(clay)
    for p in o.data.polygons:
        p.use_smooth = True

bpy.ops.mesh.primitive_plane_add(size=30)
floor = bpy.context.object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
floor.data.materials.append(fm)

world = bpy.data.worlds.new("w")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
bpy.ops.object.light_add(type="AREA", location=(2.5, -3.0, 4.0))
key = bpy.context.object
key.data.energy = 900
key.data.size = 4
key.rotation_euler = (math.radians(40), 0, math.radians(40))

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
target = bpy.data.objects.new("target", None)
bpy.context.scene.collection.objects.link(target)
target.location = (0, 0, height * 0.45)
track = cam.constraints.new("TRACK_TO")
track.target = target

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 64
sc.cycles.device = "GPU"
sc.render.resolution_x, sc.render.resolution_y = 1344, 1024
dist, elev = 5.2, 1.3
for i in range(n):
    a = math.radians(-35 + i * 360 / n)   # view 0 = front three-quarter, like a catalogue photo
    cam.location = (dist * math.sin(a), -dist * math.cos(a), elev)
    sc.render.filepath = str(out / f"view_{i:02d}.png")
    bpy.ops.render.render(write_still=True)
print("rendered", n)
