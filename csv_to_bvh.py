"""
csv_to_bvh.py  —  Blender BVH export script
Adapted from Dene33/hmr for use with hmr2.0 output.

Changes vs original:
  - directory now points to hmr/output/csv_joined  (unchanged path, same pipeline)
  - target_file now uses os.path.join for cross-platform safety
  - bpy.data.objects select API updated for Blender 2.80+ (obj.select_set(True))
  - Added graceful error if csv_joined.csv is missing

Run with:
    blender --background hmr/csv_to_bvh.blend -noaudio -P hmr2.0/csv_to_bvh.py
"""

import csv
import os
import bpy

# ── gather empties from the .blend rig ────────────────────────────────────────
objects = bpy.context.scene.objects

empties = [obj for obj in objects if obj.type == 'EMPTY']
print(f"Found {len(empties)} empties: {[e.name for e in empties]}")

# ── paths — only this section changes from the original ───────────────────────
# The csv_joined step is unchanged, so the output path is the same.
filename  = 'csv_joined.csv'
directory = 'hmr/output/csv_joined'          # same as original
fullpath  = os.path.join(directory, filename)

if not os.path.exists(fullpath):
    raise FileNotFoundError(
        f"Cannot find {fullpath}\n"
        "Make sure the csv_join step ran successfully before this script."
    )

# ── animate empties from CSV ───────────────────────────────────────────────────
with open(fullpath, 'r', newline='') as csvfile:
    ofile = csv.reader(csvfile, delimiter=',')
    next(ofile)  # skip header row (frame, j0x, j0y, j0z, ...)

    for line in ofile:
        f, *pts = line

        frame_num = int(f)
        fpts      = [float(p) for p in pts]

        # 20 joints × 3 coords = 60 values
        coordinates = [fpts[i*3 : i*3+3] for i in range(20)]

        bpy.context.scene.frame_set(frame_num)
        bpy.data.scenes['Scene'].frame_end = frame_num + 1

        for ob, position in zip(empties, coordinates):
            ob.location = position
            ob.keyframe_insert(data_path="location", index=-1)

# ── select rig and export BVH ─────────────────────────────────────────────────
rig = bpy.data.objects.get('rig')
if rig is None:
    raise RuntimeError("No object named 'rig' found in the .blend file.")

# Blender 2.80+ uses select_set(); older versions used .select = True
try:
    rig.select_set(True)
except AttributeError:
    rig.select = True   # Blender < 2.80 fallback

target_file = os.path.join('hmr', 'output', 'bvh_animation', 'estimated_animation.bvh')
os.makedirs(os.path.dirname(target_file), exist_ok=True)

bpy.ops.export_anim.bvh(filepath=target_file)
print(f"BVH exported to {target_file}")
