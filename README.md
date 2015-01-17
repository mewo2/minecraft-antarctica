# Minecraft Antarctica generator script

This is the script that was used to generate [Minecraft
Antarctica](http://www.martinoleary.com/minecraft/). Feel free to use as a base
for your own creations. This is unsupported code - it worked for me when I
needed it to. The code is MIT licensed, details are in `LICENSE.md`.

## Libraries needed

The script uses a few external libraries. The Minecraft file format is handled
by `pymclevel`, which you'll have to install from Github.

 * [numpy](http://www.numpy.org) 
 * [osgeo](http://gdal.org/python/)
 * [pymclevel](https://github.com/jashley/pymclevel)

## Data needed

The underlying data is
[Bedmap2](http://www.antarctica.ac.uk//bas_research/our_research/az/bedmap2/).
You'll want the TIFF version, available
[here](https://secure.antarctica.ac.uk/data/bedmap2/bedmap2_tiff.zip).

