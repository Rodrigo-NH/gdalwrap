import sys, os
from osgeo import osr, ogr

inshapefile = r'D:\srtm\invent\work3\temp5\ring\OUTPUT10.shp'
outshapefile = r'D:\srtm\invent\work3\temp5\ring\OUTPUT10_.shp'

ogr.UseExceptions()
osr.UseExceptions()

def main():
	poltotal = []
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(inshapefile, 0)
	inlayer = dataSource.GetLayer()
	projection = inlayer.GetSpatialRef()
	schema = inlayer.schema
	for feature in inlayer:
		geom = feature.GetGeometryRef()
		linering = geom.GetGeometryRef(0)
		pc = linering.GetPointCount()
		if pc > 254:
			env = geom.GetEnvelope()

			Yhalf = env[2] + (env[3] - env[2])/2


			upcutcoords = [(env[0], env[3]),(env[1],env[3]),(env[1],Yhalf),(env[0],Yhalf),(env[0], env[3])]
			downcutcoords = [(env[0],Yhalf),(env[1],Yhalf),(env[1],env[2]),(env[0],env[2]),(env[0],Yhalf)]
			upcut = ogr.Geometry(ogr.wkbLinearRing)
			for c in upcutcoords:
				coord = [c[0], c[1]]
				upcut.AddPoint_2D(*coord)
			upcutpol = ogr.Geometry(ogr.wkbPolygon)
			upcutpol.AddGeometry(upcut)

			downcut = ogr.Geometry(ogr.wkbLinearRing)
			for c in downcutcoords:
				coord = [c[0], c[1]]
				downcut.AddPoint_2D(*coord)
			downcutpol = ogr.Geometry(ogr.wkbPolygon)
			downcutpol.AddGeometry(downcut)

			upresult = upcutpol.Intersection(geom)
			downresult = downcutpol.Intersection(geom)


			poltotal.append(geomToWKT(upresult))

			poltotal.append(geomToWKT(downresult))
			# print(upresult)

	saveShape(poltotal, outshapefile, projection, schema, inlayer)


def geomToWKT(geom):
    if geom:
        coords = geom.ExportToWkt()
        return coords
    else:
        return None

def saveShape(geomcollin, outShapefile, projection, schema, inlayer):
    outDriver = ogr.GetDriverByName("ESRI Shapefile")
    outDataSource = outDriver.CreateDataSource(outShapefile)
    outLayer = outDataSource.CreateLayer('', projection, geom_type=ogr.wkbPolygon)

    # for reg in schema:
    #     fieldName = reg.GetName()
    #     fieldType = reg.GetType()
    #     crField = ogr.FieldDefn(fieldName, fieldType)
    #     outLayer.CreateField(crField)

    for each in geomcollin:
        featureDefn = outLayer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        poly = ogr.CreateGeometryFromWkt(each)
        feature.SetGeometry(poly)

        # sourceFID = each[1]
        # for reg in schema:
        #     infeature = inlayer.GetFeature(sourceFID)
        #     fvalue = infeature.GetField(reg.GetName())
        #     if reg.GetName() == "AREA":
        #         feature.SetField(reg.GetName(), 0)
        #     else:
        #         feature.SetField(reg.GetName(), fvalue)

        outLayer.CreateFeature(feature)
        feature = None
    inDataSource = None
    outDataSource = None

if __name__ == "__main__":
        main()