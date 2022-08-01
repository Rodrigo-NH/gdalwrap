from gdalwrap import *
from osgeo import ogr
import os

def main():
    '''Scan all files in directory (shp, gpkg), and output to KML file. Will search for 'Name' column to set output
    KML 'Name' attribute. For polygons classify by 'Name' and assign Style colors for each class.'''

    inputpathpath = r'D:\shapes\temp'
    infiles_shp = scanfiles(inputpathpath, 'shp')
    infiles_gpkg = scanfiles(inputpathpath, 'gpkg')
    infiles_shp = infiles_shp + infiles_gpkg

    outkml = os.path.join(inputpathpath, 'outest.kml')
    tempout = Setsource('tempsource', Action='memory')


    for file in infiles_shp:
        bn = os.path.basename(os.path.splitext(file)[0])
        inshape = Setsource(file, Action='open r')
        inshape.getlayer(0)
        classes = []
        uniquev = []
        it = inshape.iterfeatures(Action='reset')
        for feat in it:
            try:
                fatt = inshape.getfield('Name')
            except:
                fatt = ''
                pass
            classes.append(fatt)
        for val in classes:
            if val not in uniquev:
                uniquev.append(val)

        for t in range(0, len(uniquev)):
            if uniquev[t] == None:
                uniquev[t] = ''

        style_table = ogr.StyleTable()
        for si in range(0, len(uniquev)):
            stylestr = ['PolStyle' + str(si), 'PEN(c:#000000FF,w:1.0px);BRUSH(fc:' + getpalette(si) + 'C8)']
            style_table.AddStyle(stylestr[0], stylestr[1])
        style_table.AddStyle('PointStyle',
                             'SYMBOL(id:"http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",'
                             'c:#FFAA00FF,s:0.9);LABEL(c:#FFFF00FF,w:80.0)')
        tempout.datasource.SetStyleTable(style_table)
        tempout.createlayer(bn, inshape.srs, Type=inshape.layertypestr)
        tempout.getlayer(bn)
        atttrt = inshape.getattrtable()
        tempout.setattrtable(atttrt)

        suniquev = uniquev.copy()
        suniquev.sort()
        ct = 0
        for reg in suniquev:
            it2 = inshape.iterfeatures(Action='reset')
            for feat in it2:
                try:
                    fatt = inshape.getfield('Name')
                except:
                    fatt = ''
                    pass
                if fatt == None:
                    fatt = ''
                if fatt == reg:
                    fgeom = inshape.geom
                    nfeat = tempout.createfeatgeom(fgeom)
                    for f in range(0, inshape.feature.GetFieldCount()):
                        ft = inshape.feature.GetField(f)
                        nfeat.SetField(f, ft)
                    geomtype = inshape.geomtypestr.upper()
                    if 'POLYGON' in geomtype:
                        stylei = '@PolStyle' + str(uniquev.index(fatt))
                        nfeat.SetStyleString(stylei)
                    if 'POINT' in geomtype:
                        stylei = '@PointStyle'
                        nfeat.SetStyleString(stylei)
                    ct += 1
                    print("Processing feature: " + str(ct))
                    tempout.createfeature(nfeat)

    tempout.savefile(outkml, Transform='4326')


def getpalette(index):

    palette = [
        '#cea714',
        '#e4ff57',
        '#5c7026',
        '#d67b17',
        '#ab3cc6',
        '#323149',
        '#99a0c1',
        '#f999ac',
        '#fff699',
        '#efda07',
        '#f6927c',
        '#ff9e99',
        '#ffacba',
        '#ffbcdd',
        '#ffcff3'
    ]

    if index > 14:
        index = 0
    return palette[index]


if __name__ == "__main__":
    main()