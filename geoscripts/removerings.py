import sys, os
# sys.path.append(r'C:\OSGeo4W\apps\Python39\Lib\site-packages') # Set this if needed
from osgeo import osr, ogr

inshape = r'D:\gis\input.shp'
outshape = r'D:\gis\output.shp'

ogr.UseExceptions()
osr.UseExceptions()

def main():
    removeRings(inshape, outshape)

def removeRings(inshapefile, outshapefile):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(inshapefile, 0)
    inlayer = dataSource.GetLayer()
    projection = inlayer.GetSpatialRef()
    schema = inlayer.schema
    poltotal = []
    for feature in inlayer:
        geom = feature.GetGeometryRef()
        if geom:
            geomwkt = geomToWKT(geom)
            FID = feature.GetFID()
            poltotal.append([geomwkt,FID])
    poltotal = removeRingsProc(poltotal)
    saveShape(poltotal, outshapefile, projection, schema, inlayer)

def removeRingsProc(polcollection):
    hasrings = True
    while hasrings:
        hasrings = False
        polcollection = multiToPol(polcollection)
        geotemp = []
        for pol in range(0,len(polcollection)):
            rpol = polcollection[pol][0]
            splitpol = splitRing(rpol)
            if splitpol != []:
                hasrings = True
                geotemp.append([splitpol[0],polcollection[pol][1]])
                geotemp.append([splitpol[1],polcollection[pol][1]])
            else:
                geotemp.append([rpol,polcollection[pol][1]])
        polcollection = geotemp

    return polcollection

def splitRing(pol):
    geom = WKTtoGeom(pol)
    output = []
    hasring = geom.GetGeometryCount()
    if hasring > 1:
        outer = geom.GetGeometryRef(0)
        inner = geom.GetGeometryRef(1)
        outerextent = outer.GetEnvelope()
        innerextent = inner.GetEnvelope()
        Xhalf = innerextent[0] + (innerextent[1] - innerextent[0]) / 2
        Xstart = outerextent[0]
        Xend = outerextent[1]
        Ystart = outerextent[2]
        Yend = outerextent[3]
        leftcutcoords = [(Xstart, Ystart), (Xhalf, Ystart), (Xhalf, Yend), (Xstart, Yend), (Xstart, Ystart)]
        rightcutcoords = [(Xhalf, Ystart), (Xend, Ystart), (Xend, Yend), (Xhalf, Yend), (Xhalf, Ystart)]
        leftcut = ogr.Geometry(ogr.wkbLinearRing)
        for c in leftcutcoords:
            coord = [c[0], c[1]]
            leftcut.AddPoint_2D(*coord)
        leftcutpol = ogr.Geometry(ogr.wkbPolygon)
        leftcutpol.AddGeometry(leftcut)
        rightcut = ogr.Geometry(ogr.wkbLinearRing)
        for c in rightcutcoords:
            coord = [c[0], c[1]]
            rightcut.AddPoint_2D(*coord)
        rightcutpol = ogr.Geometry(ogr.wkbPolygon)
        rightcutpol.AddGeometry(rightcut)
        leftresult = leftcutpol.Intersection(geom)
        rightresult = rightcutpol.Intersection(geom)
        output = [geomToWKT(leftresult), geomToWKT(rightresult)]
    return output

def multiToPol(polcoll):
    geomcoll = []
    for each in polcoll:
        geom = WKTtoGeom(each[0])
        gtype = geom.GetGeometryType()
        if gtype == 6:
            for reg in geom:
                pol = geomToWKT(reg)
                geomcoll.append([pol,each[1]])
        elif gtype == 3:
            pol = geomToWKT(geom)
            geomcoll.append([pol,each[1]])
    return geomcoll

def geomToWKT(geom):
    if geom:
        coords = geom.ExportToWkt()
        return coords
    else:
        return None

def WKTtoGeom(wkt):
    poly = ogr.CreateGeometryFromWkt(wkt)
    return poly

def saveShape(geomcollin, outShapefile, projection, schema, inlayer):
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    outDataSource = outDriver.CreateDataSource(outShapefile)
    outLayer = outDataSource.CreateLayer('', projection, geom_type=ogr.wkbPolygon)

    for reg in schema:
        fieldName = reg.GetName()
        fieldType = reg.GetType()
        crField = ogr.FieldDefn(fieldName, fieldType)
        outLayer.CreateField(crField)

    for each in geomcollin:
        featureDefn = outLayer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        poly = ogr.CreateGeometryFromWkt(each[0])
        feature.SetGeometry(poly)

        sourceFID = each[1]
        for reg in schema:
            infeature = inlayer.GetFeature(sourceFID)
            fvalue = infeature.GetField(reg.GetName())
            feature.SetField(reg.GetName(), fvalue)

        outLayer.CreateFeature(feature)
        feature = None
    inDataSource = None
    outDataSource = None

if __name__ == "__main__":
        main()