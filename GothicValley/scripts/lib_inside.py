import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); OUT = a[1]
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 1200, 700
wo = bpy.data.worlds.new("w"); wo.use_nodes = True; wo.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6; sc.world = wo
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = 1.5
for (x, y, z) in ((0, -6, 8), (0, 6, 8), (-18, 0, 8), (-4, -12, 8)):
    l = bpy.data.lights.new("l", "POINT"); l.energy = 4000; l.shadow_soft_size = 1.0
    lo = bpy.data.objects.new("l", l); lo.location = (x, y, z); sc.collection.objects.link(lo)
cam_d = bpy.data.cameras.new("eye"); cam_d.lens = 18; cam_d.clip_start = 0.05
cam = bpy.data.objects.new("eye", cam_d); sc.collection.objects.link(cam); sc.camera = cam
for k, (loc, tgt) in enumerate((((0, -11, 4.4), (0, 10, 6)), ((-1, 9, 4.2), (-16, 0, 5)), ((-20, -3, 4.3), (-4, 3, 5)), ((-6, -12, 12), (2, 8, 4)))):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"inside_{k}.png"); bpy.ops.render.render(write_still=True)
