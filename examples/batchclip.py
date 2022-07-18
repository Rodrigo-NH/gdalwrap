from os import walk
import os
from gdalwrap import *

# os.environ['SHAPE_ENCODING'] = "cp1252" # I need this often

def main():
    '''Batch clip. Will clip and transform (reproject) output shapefiles
    automatically using the clipping shapefile SRS'''

    # Folders where to scan for input shapefiles
    folders = [
        r'D:\shapes\temp',
        r'D:\shapes\temp2',
    ]

    # Output folder where to store resulting shapefiles
    outputfolder = r'D:\shapes\out'

    # Shapefile used as clip mask
    clipshape = r'D:\shapes\quadrante.shp'

    shapefiles = []
    outshapes = []
    for folder in folders:
        files = []
        for (dirpath, dirnames, filenames) in walk(folder):
            files.extend(filenames)
            break
        for each in files:
            sp = each.split('.')
            if sp[1].upper() == 'SHP' and len(sp) == 2:
                shapepath = folder + '\\' + sp[0] + '.' + sp[1]
                shapeout = outputfolder + '\\' + sp[0] + '.' + sp[1]
                outshapes.append(shapeout)
                shapefiles.append(shapepath)

    clipshape = Setsource(clipshape, Action='open r')
    clipshape.getlayer(0)
    clipshape.getfeature(0)
    clipgeom = clipshape.geom
    for si in range (0, len(shapefiles)):
        print("Clip: " + shapefiles[si])
        inshp = Setsource(shapefiles[si], Action='open r')
        outshape = Setsource(shapefiles[si], Action='memory')
        inshp.getlayer(0)
        s1 = clipshape.srs
        s2 = inshp.srs
        outshape.createlayer('nlayer', s1, Type=inshp.layertypestr)
        sourcetrans = Transformation(s1, s2)
        outrans = Transformation(s2, s1)
        clipgeomt = sourcetrans.transform(clipgeom)
        clipfeatures = layerclip(inshp.layer, clipgeomt)
        fields = inshp.getattrtable()
        outshape.setattrtable(fields)
        if len(clipfeatures) > 0:
            for feature in clipfeatures:
                geom = feature.geometry()
                geomt = outrans.transform(geom)
                feature.SetGeometry(geomt)
                outshape.createfeature(feature)
            outshape.savefile(outshapes[si])


if __name__ == "__main__":
    main()