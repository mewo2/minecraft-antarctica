from __future__ import division

import contextlib
import shutil
import os
import os.path

import numpy as np

from osgeo import gdal

from pymclevel import mclevel, nbt, box, level
from pymclevel.materials import alphaMaterials as mat

# Optionally set to your Minecraft save directory, e.g.
# savedir = "/Users/olearym/Library/Application Support/minecraft/saves/"
savedir = "./saves"

# Location of Bedmap2 data
bedmapdir = "./bedmap2_tiff"

mapname = "Antarctica"

vscale = 0.01    # Vertical scale factor
vshift = 80      # Vertical shift
step = 1         # Step size (use every "step"th pixel)
batch_size = 32  # Save changes every N rows - ideally a multiple of 16

# Material definitions
rock = mat.Stone
ice = mat[174]    # Packed ice is new in Minecraft 1.8, so it isn't named in
                  # pymclevel
water = mat.Water


@contextlib.contextmanager
def create_world(name):
    if not os.path.isdir(savedir):
        print "Creating directory", savedir
        os.makedirs(savedir)
    path = os.path.join(savedir, name)
    shutil.rmtree(path, ignore_errors=True)
    world = mclevel.MCInfdevOldLevel(path, create=True)
    tags = [nbt.TAG_Int(0, "MapFeatures"),
            nbt.TAG_String("flat", "generatorName"),
            nbt.TAG_String("0", "generatorOptions")]
    for tag in tags:
        world.root_tag["Data"].add(tag)
    world.GameType = 1 # Creative mode
    yield world
    world.saveInPlace()

def fill_box(world, material, x0, x1, y0, y1, z0, z1):
    tilebox = box.BoundingBox((x0,y0,z0), (x1-x0,y1-y0,z1-z0))
    world.createChunksInBox(tilebox)
    world.fillBlocks(tilebox, material)

def fill_column(world, x, z, *matheights):
    elev = 0
    for material, height in matheights:
        if height > 0:
            fill_box(world, material, x, x + 1, elev, elev + height, z, z + 1)
            elev += height

@contextlib.contextmanager
def batch_changes():
    chunkset = set()
    def deferred(chunk, needsLighting=True):
        chunkset.add(chunk)
    tmp, level.LightedChunk.chunkChanged = level.LightedChunk.chunkChanged, deferred
    yield
    level.LightedChunk.chunkChanged = tmp
    for chunk in chunkset:
        chunk.chunkChanged(True)

def load_tiff(filename, nanvalue=np.nan):
    filepath = os.path.join(bedmapdir, filename)
    dat = gdal.Open(filepath).ReadAsArray()
    dat = dat.astype(float)
    dat[dat == 32767] = nanvalue
    print "%s: min %.1f, max %.1f" % (filename, np.nanmin(dat), np.nanmax(dat))
    return dat

bed = load_tiff("bedmap2_bed.tif")
surf = load_tiff("bedmap2_surface.tif", 0)
thick = load_tiff("bedmap2_thickness.tif", 0)

tomc = lambda x: int(x * vscale + vshift)

assert tomc(np.nanmin(bed)) > 0, \
    "Bed goes below y=0 (decrease vscale or increase vshift)"
assert tomc(np.nanmax(surf)) < 255, \
    "Surface goes above y=255 (decrease vscale or decrease vshift)"

total = 0
with create_world(mapname) as world:
    for i_ in xrange(0,bed.shape[0],step*batch_size):
        with batch_changes():
            for i in xrange(i_, min(i_ + step * batch_size, bed.shape[0]), step):
                print "Processing row %d/%d" % (i//step+1, bed.shape[0]//step)
                for j in xrange(0,bed.shape[1],step):
                    try:
                        bedheight = tomc(bed[i, j])
                        baseheight = tomc(surf[i, j] - thick[i, j])
                        surfheight = tomc(surf[i, j])
                        if thick[i, j] > 0 and surfheight == baseheight:
                            baseheight -= 1
                        if baseheight < bedheight:
                            bedheight = baseheight
                    except ValueError:
                        continue
                    mats = [(rock, bedheight), (water, baseheight - bedheight),
                            (ice, surfheight - baseheight)]
                    total += surfheight
                    fill_column(world, j//step, i//step, *mats)
        world.saveInPlace() 
        world.setPlayerPosition((bed.shape[1]//(step*2), 250,
            bed.shape[0]//(step*2)))

print total, "blocks used"
