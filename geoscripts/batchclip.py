import sys, random, os, pathlib
from subprocess import Popen, PIPE, STDOUT

sys.path.append(r'C:\OSGeo4W\apps\Python39\Lib\site-packages')
from osgeo import ogr, gdal, osr
from os import walk

# clipshape, inputshape, outputdir
# clipshape, inputdir1, outputdir
# clipshape, inputdir1, inputdir2, outputdir

os.environ['SHAPE_ENCODING'] = "cp1252"

ogr.UseExceptions()
osr.UseExceptions()

# python .\batchclip.py D:\srtm\batchclip\clippol\ClipPol_SIRGAS.shp D:\MA\Trabalhos\BASE-SIG\ShapesInteresse D:\MA\Trabalhos\BASE-SIG\Inventario-MG-split D:\MA\Trabalhos\BASE-SIG\IGAM-OTTO\SoOsNomeados D:\MA\Trabalhos\BASE-SIG\IGAM-OTTO\completos D:\MA\Trabalhos\BASE-SIG\IDE-SISEMA-new D:\MA\Trabalhos\BASE-SIG\IDE-SISEMA\UCs D:\MA\Trabalhos\BASE-SIG\SOLOS-MG\CETEC-2010 D:\srtm\batchclip\outdir

def main():
	clipshape = sys.argv[1]
	outshape_PATH = str(pathlib.Path(sys.argv[len(sys.argv) - 1]).absolute())
	if os.path.isfile(sys.argv[2]):
		shapefile = sys.argv[2]
		inshape_name = sys.argv[2].split('\\')[-1].split('.')[0]
		shapeout = outshape_PATH + '\\' + inshape_name + '_clip.shp'
		cutshape(clipshape, shapefile, shapeout)

	if os.path.isdir(sys.argv[2]):
		shapefiles = []
		for dir in range(2, len(sys.argv) - 1):
			files = []
			for (dirpath, dirnames, filenames) in walk(sys.argv[dir]):
				files.extend(filenames)
				shapes_PATH = pathlib.Path(dirpath).absolute()
				break
			for each in files:
				sp = each.split('.')
				if sp[1].upper() == 'SHP' and len(sp) == 2:
					shapefiles.append(str(shapes_PATH) + '\\' + each)
		for shape in shapefiles:
			inshape_name = shape.split('\\')[-1].split('.')[0]
			shapeout = outshape_PATH + '\\' + inshape_name + '_clip.shp'
			cutshape(clipshape, shape, shapeout)

def batchclip(clipshape, input, output):
	outshape_PATH = str(pathlib.Path(output).absolute())
	if os.path.isfile(input[0]):
		shapefile = input[0]
		inshape_name = input[0].split('\\')[-1].split('.')[0]
		shapeout = outshape_PATH + '\\' + inshape_name + '_clip.shp'
		cutshape(clipshape, shapefile, shapeout)
	if os.path.isdir(input[0]):
		shapefiles = []
		for dir in input:
			files = []
			for (dirpath, dirnames, filenames) in walk(dir):
				files.extend(filenames)
				shapes_PATH = pathlib.Path(dirpath).absolute()
				break
			for each in files:
				sp = each.split('.')
				if sp[1].upper() == 'SHP' and len(sp) == 2:
					shapefiles.append(str(shapes_PATH) + '\\' + each)
		for shape in shapefiles:
			inshape_name = shape.split('\\')[-1].split('.')[0]
			shapeout = outshape_PATH + '\\' + inshape_name + '_clip.shp'
			cutshape(clipshape, shape, shapeout)

def cutshape(clipshape, shapefile, shapeout):
	print("Clipping: " + shapefile)
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapefile, 1)
	clipgeom = driver.Open(clipshape, 1)
	layer = dataSource.GetLayer()
	clipg = clipgeom.GetLayer()
	clipprojection = clipg.GetSpatialRef()
	inshapeprojection = layer.GetSpatialRef()
	layerex = layer.GetExtent()
	clipgex = clipg.GetExtent()
	if containTest(layerex, clipgex, inshapeprojection, clipprojection):
		typ = layer.GetGeomType()
		schema = layer.schema
		geom = clipg[0]
		geomclip = geom.GetGeometryRef()
		shapedontexist = True
		destFID = 0
		for feat in layer:
			FID = feat.GetFID()
			geomin = feat.GetGeometryRef()
			if inshapeprojection != clipprojection:
				transform = osr.CoordinateTransformation(inshapeprojection, clipprojection)
				geomin.Transform(transform)
			try:
				polcut = geomclip.Intersection(geomin)
				# gcount = geomTest(polcut) # Abandoned
				if not "EMPTY" in polcut.ExportToWkt()[0:30]:
					if shapedontexist:
						shapedontexist = False
						if typ == 2:
							geomobj = ogr.wkbLineString
						elif typ == 5:
							geomobj = ogr.wkbMultiLineString
						elif typ == 6 or typ == 3:
							geomobj = ogr.wkbPolygon
						elif typ == 1 or typ == 4:
							geomobj = ogr.wkbPoint
						driver2 = ogr.GetDriverByName("ESRI Shapefile")
						outDataSource = driver2.CreateDataSource(shapeout)

						outLayer = outDataSource.CreateLayer('', clipprojection, geom_type=geomobj)
						for reg in schema:
							fieldName = reg.GetName()
							fieldType = reg.GetType()
							crField = ogr.FieldDefn(fieldName, fieldType)
							outLayer.CreateField(crField)
					featureDefn = outLayer.GetLayerDefn()
					feature = ogr.Feature(featureDefn)
					feature.SetGeometry(polcut)
					for reg in schema:
						fname = reg.GetName()
						fvalue = feat.GetField(fname)
						# fieldType = reg.GetType()
						if fvalue == None:
							fvalue = ''
						feature.SetField(fname, fvalue)
					feature = fixInConsistence(feature,outLayer, featureDefn, shapefile, FID, destFID)
					outLayer.CreateFeature(feature)
					destFID += 1
			except Exception as inst:
				err = str(inst) + "| source FID: " + str(FID) + " | Dest. FID: " + str(destFID)
				print(err)
			feature = None
		outDataSource = None

def fixInConsistence(feature, outLayer, featureDefn, shapefile, FID, destFID):
	ft = feature.GetGeometryRef()
	fg = ft.GetGeometryType()
	lt = outLayer.GetGeomType()
	if (lt == 3 or lt == 6) and fg == 5: # MULTILINESTRING in a (MULTI)POLYGON layer
		msg = "WARNING! MULTILINESTRING in a (MULTI)POLYGON layer | " + shapefile + " | source FID: " + str(FID)
		points = []
		for line in ft:
			pts = line.GetPoints()
			for pt in pts:
				points.append(pt)
		fil = points[0]
		lil = points[-1]
		if fil != lil:
			points.append(fil)
		shapering = ogr.Geometry(ogr.wkbLinearRing)
		for c in points:
			coord = [c[0], c[1]]
			shapering.AddPoint_2D(*coord)
		shapeg = ogr.Geometry(ogr.wkbPolygon)
		shapeg.AddGeometry(shapering)
		feature = ogr.Feature(featureDefn)
		feature.SetGeometry(shapeg)
		msg = msg + " | FIXED " + "dest. FID: " + str(destFID)
		print(msg)
		return feature
	else:
		return feature

def containTest(shape, clip, shapeproj, clipproj):  # Make it faster by testing intersection first
	shapepol = [(shape[0], shape[2]), (shape[1], shape[2]), (shape[1], shape[3]),
	            (shape[0], shape[3]), (shape[0], shape[2])]
	clippol = [(clip[0], clip[2]), (clip[1], clip[2]), (clip[1], clip[3]),
	           (clip[0], clip[3]), (clip[0], clip[2])]
	shapering = ogr.Geometry(ogr.wkbLinearRing)
	clipring = ogr.Geometry(ogr.wkbLinearRing)
	for c in shapepol:
		coord = [c[0], c[1]]
		shapering.AddPoint_2D(*coord)
	for c in clippol:
		coord = [c[0], c[1]]
		clipring.AddPoint_2D(*coord)
	shapeg = ogr.Geometry(ogr.wkbPolygon)
	shapeg.AddGeometry(shapering)
	clipg = ogr.Geometry(ogr.wkbPolygon)
	clipg.AddGeometry(clipring)
	dest_srs = osr.SpatialReference()
	dest_srs.ImportFromEPSG(4326)
	transform = osr.CoordinateTransformation(shapeproj, dest_srs)
	transform2 = osr.CoordinateTransformation(clipproj, dest_srs)
	shapeg.Transform(transform)
	clipg.Transform(transform2)
	clipresult = clipg.Intersection(shapeg)
	clipresult = clipresult.GetGeometryCount()
	if clipresult > 0:
		return True

# Abandoned after getting 'Fatal Python error: deallocating None'
# def geomTest(polcut):  # This is the best I can do for now
	# test = False
	# cuttype = polcut.GetGeometryType() # https://gist.github.com/walkermatt/7121427
	# if cuttype == 2 or cuttype == 5 or cuttype == -2147483646 or cuttype == -2147483643:
	# 	pt = polcut.GetPoints()
	# 	if pt is not None: <------------------------------------------------------------- 'Fatal Python error: deallocating None'
	# 		test = True
	# if cuttype == 3 or cuttype == 6 or cuttype == -2147483645 or cuttype == -2147483642:
	# 	gcount = polcut.GetGeometryCount()
	# 	if gcount > 0:
	# 		test = True
	# if cuttype == 1 or cuttype == 4 or cuttype == -2147483647 or cuttype == -2147483644:
	# 	ptt = polcut.GetPoints()[0][0]
	# 	if ptt != 0.0:
	# 		test = True
	# return test

if __name__ == "__main__":
	main()