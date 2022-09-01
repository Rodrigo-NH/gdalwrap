from os import walk
import os
from gdalwrap import *

os.environ['SHAPE_ENCODING'] = "cp1252" # I need this often

def main():
    '''Batch clip. Will clip and transform (reproject) output shapefiles
    automatically using the clipping shapefile SRS'''

    # Folders where to scan for input shapefiles
    folders = [
        r'D:\gis\shapedir',
        r'D:\gis2\anothershapedir'
    ]

    # Output folder where to store resulting shapefiles
    outputfolder = r'D:\gisout\outputfolder'

    # Shapefile used as clip mask
    clipshape = r'D:\geo\project\clippingshape.shp'

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
                shapepath = os.path.join(folder, sp[0] + '.' + sp[1])
                shapeout = os.path.join(outputfolder, sp[0] + '.' + sp[1])
                outshapes.append(shapeout)
                shapefiles.append(shapepath)

    clipshape = Datasource(clipshape, Action='open r')
    ly = clipshape.getlayer(0)
    for si in range(0, len(shapefiles)):
        iterfeatures = ly.iterfeatures(Action='reset')
        outshape = Datasource(shapefiles[si], Action='memory')
        s1 = ly.layer.GetSpatialRef()
        inshp = Datasource(shapefiles[si], Action='open r')
        inly = inshp.getlayer(0)
        outshape.Newlayer('nlayer', s1, Type=inly.getgeomtypename())
        outly = outshape.getlayer('nlayer')
        print("Clip: " + shapefiles[si])
        for tf in iterfeatures:
            clipgeom = tf.getgeom().geom
            s2 = inly.layer.GetSpatialRef()
            sourcetrans = Transformation(s1, s2)
            outrans = Transformation(s2, s1)
            clipgeomt = sourcetrans.transform(clipgeom)
            clipfeatures = layerclip(inly.layer, clipgeomt)
            fields = inly.getattrtable()
            outly.setattrtable(fields)
            if len(clipfeatures) > 0:
                for feature in clipfeatures:
                    of = outly.Newfeature()
                    of.setfeature(feature)
                    ig = of.getgeom().geom
                    og = outrans.transform(ig)
                    of.setgeom(og)
                    of.insert()
        if outly.getfeaturecount() > 0:
            outshape.savefile(outshapes[si])


if __name__ == "__main__":
    main()