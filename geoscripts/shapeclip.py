import sys, random, os, pathlib
from subprocess import Popen, PIPE, STDOUT
sys.path.append(r'C:\OSGeo4W\apps\Python39\Lib\site-packages')
from osgeo import ogr, gdal, osr

shapefile = r'D:\MA\Trabalhos\BASE-SIG\Inventario-MG\Inventario_Florestal_MG_2009.shp'
tempfolder = r'D:\MA\Trabalhos\BASE-SIG\Inventario-MG\split'

Xclipammount = 1.8
Yclipammount = 1.8

def main():
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapefile, 1)
    layer = dataSource.GetLayer()
    extent = layer.GetExtent()

    totalX = abs(extent[0]-extent[1])
    totalY = abs(extent[2] - extent[3])

    divX = int(round(totalX / Xclipammount))
    divY = int(round(totalX / Yclipammount))

    Xstep = totalX / divX
    Ystep = totalY / divY
    Xpos = extent[0]
    Ypos = extent[3]
    gridcount = divX * divY

    index = 0
    indexo = []
    for Ytile in range(0,divY):
        for Xtile in range(0, divX):
            coords = [(Xpos, Ypos), (Xpos + Xstep, Ypos), (Xpos + Xstep, Ypos - Ystep), (Xpos, Ypos - Ystep),(Xpos, Ypos)]
            createGrid(coords, index)
            indexo.append(index)
            index += 1
            Xpos = Xpos + Xstep
        Xpos = extent[0]
        Ypos = Ypos - Ystep


    for reg in range(0,gridcount):
        print(reg)
        callstr = ['ogr2ogr',
                   '-clipsrc',
                   tempfolder + '\\grid' + str(reg) + '.shp',
                   tempfolder + '\\OUTPUT' + str(reg) + '.shp',
                   shapefile]
        proc = Popen(callstr, stdout = PIPE, stderr = STDOUT, shell = True)
        for line in proc.stdout:
            print(line.decode('ansi').strip('\n'))

        outputlayer = driver.Open(tempfolder + '\\OUTPUT' + str(reg) + '.shp', 1)
        layer = outputlayer.GetLayer()
        if len(layer) == 0:
            layer = None
            outputlayer = None
            os.remove(tempfolder + '\\OUTPUT' + str(reg) + '.shp')
        outputlayer = layer = None

def createGrid(coords, index):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in coords:
        ring.AddPoint(coord[0], coord[1])

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    polywkb = poly.ExportToWkt()

    dest_srs = osr.SpatialReference()
    dest_srs.ImportFromEPSG(4326)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.CreateDataSource(tempfolder + '\\grid' + str(index) + '.shp')
    layer = ds.CreateLayer('', dest_srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    defn = layer.GetLayerDefn()

    feat = ogr.Feature(defn)
    feat.SetField('id', 123)
    geom = ogr.CreateGeometryFromWkt(polywkb)
    feat.SetGeometry(geom)
    layer.CreateFeature(feat)
    feat = geom = None  # destroy these
    ds = layer = feat = geom = None

if __name__ == "__main__":
    main()