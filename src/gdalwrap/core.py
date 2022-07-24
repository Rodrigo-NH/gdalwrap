try:
	from osgeo import ogr
	from osgeo import osr
except ImportError as error:
	raise Exception("""ERROR: Could not find the GDAL/OGR Python library bindings.""")
import os
ogr.UseExceptions()
osr.UseExceptions()


def makecircle(pointgeom, buffer, pdensity):
	circle = pointgeom.Buffer(buffer, pdensity)
	return circle


def makepoint(input):
	st = 'POINT(' + str(input[0]) + ' ' + str(input[1]) + ')'
	point = ogr.CreateGeometryFromWkt(st)
	return point


def makepol(input):
	ta = input + [input[0]]
	tap = []
	for t in ta:
		tap.append(str(t[0]) + ' ' + str(t[1]))
	st = 'POLYGON((' + ','.join(tap) + '))'
	poly = ogr.CreateGeometryFromWkt(st)
	# poly = poly.ExportToWkb()
	return poly


def getfid(feature):
	fid = feature.GetFID()
	return fid


def _getsrs(srs):
	if len(str(srs)) > 7:  # Can expect 'OpenGIS Well Known Text format'
		return srs
	elif len(srs) == 0:
		return None
	else:
		osrs = osr.SpatialReference()
		osrs.ImportFromEPSG(int(srs))
		osrs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
		return osrs


class Setsource:
	def __init__(self, inputshape, Action='Open r'):
		self.action = Action
		self.shapepath = inputshape
		self.srs = None
		self.layer = None
		self.layerdef = None
		self.layertype = None
		self.layertypestr = None
		self.datasource = None
		self.geom = None
		self.geomtype = None
		self.geomtypestr = None
		self.feature = None
		self.fid = None
		self.layername = None
		self.fidtable = []
		# self.featurecollection = []
		# self.fidindex = True

		if Action.upper() == 'CREATE' or Action.upper() == 'MEMORY':
			if Action.upper() == 'CREATE':
				driver = ogr.GetDriverByName(filternames(inputshape))
				ds = driver.CreateDataSource(inputshape)
			if Action.upper() == 'MEMORY':
				driver = ogr.GetDriverByName("MEMORY")
				ds = driver.CreateDataSource(inputshape)
		if Action.upper()[:4] == 'OPEN':
			if Action.upper()[4:].strip() == 'R':
				rw = 0
			elif Action.upper()[4:].strip() == 'RW':
				rw = 1
			ds = ogr.Open(inputshape, rw)
		self.datasource = ds

	# def updatefidtable(self):
	# 	self.fidtable = []
	# 	self.featurecollection = []
	# 	self.layer.ResetReading()
	# 	if self.fidindex:
	# 		ftv = self.layer.GetNextFeature()
	# 		while ftv is not None:
	# 			fid = ftv.GetFID()
	# 			self.fidtable.append(fid)
	# 			# self.featurecollection.append(ftv)
	# 			ftv = self.layer.GetNextFeature()
	# 	# else:
	# 	# 	self.fidtable = range(0,self.featurecount())
	# 	# self.layer.ResetReading()

	def createlayer(self, name, srs, Type='Polygon'):
		gt = layertypes(Type)
		self.srs = _getsrs(srs)
		self.layer = self.datasource.CreateLayer(name, self.srs, gt)
		# layer = self.datasource.CreateLayer(name, _getsrs(srs), gt)
		self.layertype = gt
		self.layerdef = self.layer.GetLayerDefn()
		self.layertypestr = ogr.GeometryTypeToName(self.layerdef.GetGeomType())
		self.layername = self.layer.GetDescription()
		return self.layer
		# return layer

	def getlayer(self, id):
		self.layer = self.datasource.GetLayer(id)
		self.srs = self.layer.GetSpatialRef()
		self.layerdef = self.layer.GetLayerDefn()
		self.layertype = self.layerdef.GetGeomType()
		self.layertypestr = ogr.GeometryTypeToName(self.layerdef.GetGeomType())
		self.layername = self.layer.GetDescription()
		# self.updatefidtable()
		return self.layer

	def getfeature(self, findex):
		# if self.fidindex:
		# 	self.feature = self.featurecollection[findex]
		# else:
		self.feature = self.layer.GetFeature(findex)
		self.geom = self.feature.GetGeometryRef()
		self.geomtype = self.geom.GetGeometryType()
		self.geomtypestr = ogr.GeometryTypeToName(self.geomtype)
		self.fid = self.feature.GetFID()
		exportfeature = self.feature.ExportToJson()
		# return self.feature
		return exportfeature

	def exportgeom(self, FID):
		ft = self.layer.GetFeature(FID)
		geom = ft.GetGeometryRef()
		igeom = geom.ExportToWkb()
		exportgeom = ogr.CreateGeometryFromWkb(igeom)
		return exportgeom

	def iterfeatures(self, Action=None):
		if Action == 'reset':
			self.layer.ResetReading()
		ftv = self.layer.GetNextFeature()
		while ftv is not None:
			self.feature = ftv
			self.geom = self.feature.GetGeometryRef()
			self.geomtype = self.geom.GetGeometryType()
			self.geomtypestr = ogr.GeometryTypeToName(self.geomtype)
			self.fid = self.feature.GetFID()
			ftv = self.layer.GetNextFeature()
			yield self.feature


	def savefile(self, filename, Transform=None):
		dest = Setsource(filename, Action='create')
		style_table = self.datasource.GetStyleTable()
		dest.datasource.SetStyleTable(style_table)
		for ind in range(0, self.layercount()):
			inlay = self.getlayer(ind)
			layergeomtype = self.layertypestr
			if layergeomtype == 'Unknown (any)': # Layer without a geometry type (e.g. KML)
				self.getfeature(0)  # Insecure, must improve
				geome = self.geom
				layergeomtype = ogr.GeometryTypeToName(geome.GetGeometryType())

			destsrs = self.srs
			if Transform is not None:
				trans = Transformation(self.srs, Transform)
				destsrs = Transform

			dest.createlayer(self.layername, destsrs, Type=layergeomtype)
			inatt = self.getattrtable()
			dest.setattrtable(inatt)
			it = self.iterfeatures(Action='reset')
			for feature in it:
			# for g in range(self.featurecount()):
			# 	self.getfeature(g)
				featstyle = self.feature.GetStyleString()
				geom = self.geom
				if Transform is not None:
					geom = trans.transform(geom)
				ofeature = ogr.Feature(dest.layerdef)
				ofeature.SetGeometry(geom)
				ofeature.SetStyleString(featstyle)
				for f in range(0, self.feature.GetFieldCount()):
					ft = self.feature.GetField(f)
					ofeature.SetField(f, ft)
				dest.createfeature(ofeature)
		dest = None

	def layercount(self):
		return(len(self.datasource))

	def featurecount(self):
		return len(self.layer)

	def getattrtable(self):
		sch = []
		schema = self.layer.schema
		for reg in schema:
			fieldName = reg.GetName()
			fieldType = reg.GetTypeName()
			sch.append([fieldName, fieldType])
		return sch

	def setattrtable(self, attrtable):
		for field in attrtable:  # recreates attribute table
			fieldtype = fieldtypes(field[1])
			self.layer.CreateField(ogr.FieldDefn(field[0], fieldtype))

	def createattr(self, name, Type='integer'):
		fieldtype = fieldtypes(Type)
		fdn = ogr.FieldDefn(name, fieldtype)
		self.layer.CreateField(fdn)


	def createfeature(self, feature):
		# featurecounter = len(self.layer)
		# feature.SetFID(featurecounter)
		self.layer.CreateFeature(feature)
		# self.feature = feature
		# self.geom = self.feature.GetGeometryRef()
		# self.fid = feature.GetFID()
		# fid = feature.GetFID()
		# if self.fidindex:
		# 	self.fidtable.append(fid)
			# self.featurecollection.append(feature)

	def geom2feature(self, geom):
		feature = ogr.Feature(self.layerdef)
		feature.SetGeometry(geom)
		# self.layer.CreateFeature(feature)
		# self.feature = feature
		# self.geom = self.feature.GetGeometryRef()
		# self.fid = feature.GetFID()
		# exportfeature = feature.ExportToJson()
		# return self.feature
		# return exportfeature
		return feature

	def setfield(self, feature, attr, value):
		feature.SetField(attr, value)
		# self.layer.SetFeature(feature)
		fid = feature.GetFID()
		if fid != -1:
			self.layer.SetFeature(feature)


			# raise ValueError('A very specific bad thing happened.')

		# else:
		# 	self.layer.SetFeature(feature)
		# if self.fidindex and fid == -1:
		# 	self.layer.SetFeature(self.feature)
		# 	nfid = feature.GetFID()
		# 	self.fidindex.append(nfid)

	# def updatefield(self, attr, value):
	# 	self.feature.SetField(attr, value)
	# 	self.layer.SetFeature(self.feature)
		# self.updatefidtable()

	def getfield(self, field):
		fv = self.feature.GetField(field)
		return fv

	def getlyrextent(self):
		extent = []
		le = self.layer.GetExtent()
		for t in le:
			extent.append(t)
		return extent


def _testmultitypes(setsourceobject):
	shptypes = []
	for sh in range(0, setsourceobject.layercount()):
		setsourceobject.getlayer(sh)
		for feat in range(0, setsourceobject.featurecount()):
			setsourceobject.getfeature(feat)
			geom = setsourceobject.geom
			ttype = geom.GetGeometryType()
			tstype = ogr.GeometryTypeToName(ttype)
			if tstype not in shptypes:
				shptypes.append(tstype)
	if len(shptypes) > 1:
		return True
	else:
		return False


def layertypes(name):
	# Clue:
	# for name in dir(ogr):
	# 	if name.startswith('wkb'):
	# 		i = getattr(ogr, name)
	# 		print('%s : %d : %r' % (name, i, ogr.GeometryTypeToName(i)))
	ltypes =[
		['3D UNKNOWN (ANY)', ogr.wkb25Bit],
		['3D UNKNOWN (ANY)', ogr.wkb25DBit],
		['CIRCULAR STRING', ogr.wkbCircularString],
		['MEASURED CIRCULAR STRING', ogr.wkbCircularStringM],
		['3D CIRCULAR STRING', ogr.wkbCircularStringZ],
		['3D MEASURED CIRCULAR STRING', ogr.wkbCircularStringZM],
		['COMPOUND CURVE', ogr.wkbCompoundCurve],
		['MEASURED COMPOUND CURVE', ogr.wkbCompoundCurveM],
		['3D COMPOUND CURVE', ogr.wkbCompoundCurveZ],
		['3D MEASURED COMPOUND CURVE', ogr.wkbCompoundCurveZM],
		['CURVE', ogr.wkbCurve],
		['MEASURED CURVE', ogr.wkbCurveM],
		['CURVE POLYGON', ogr.wkbCurvePolygon],
		['MEASURED CURVE POLYGON', ogr.wkbCurvePolygonM],
		['3D CURVE POLYGON', ogr.wkbCurvePolygonZ],
		['3D MEASURED CURVE POLYGON', ogr.wkbCurvePolygonZM],
		['3D CURVE', ogr.wkbCurveZ],
		['3D MEASURED CURVE', ogr.wkbCurveZM],
		['GEOMETRY COLLECTION', ogr.wkbGeometryCollection],
		['3D GEOMETRY COLLECTION', ogr.wkbGeometryCollection25D],
		['MEASURED GEOMETRY COLLECTION', ogr.wkbGeometryCollectionM],
		['3D MEASURED GEOMETRY COLLECTION', ogr.wkbGeometryCollectionZM],
		['LINE STRING', ogr.wkbLineString],
		['3D LINE STRING', ogr.wkbLineString25D],
		['MEASURED LINE STRING', ogr.wkbLineStringM],
		['3D MEASURED LINE STRING', ogr.wkbLineStringZM],
		['UNRECOGNIZED: 101', ogr.wkbLinearRing],
		['MULTI CURVE', ogr.wkbMultiCurve],
		['MEASURED MULTI CURVE', ogr.wkbMultiCurveM],
		['3D MULTI CURVE', ogr.wkbMultiCurveZ],
		['3D MEASURED MULTI CURVE', ogr.wkbMultiCurveZM],
		['MULTI LINE STRING', ogr.wkbMultiLineString],
		['3D MULTI LINE STRING', ogr.wkbMultiLineString25D],
		['MEASURED MULTI LINE STRING', ogr.wkbMultiLineStringM],
		['3D MEASURED MULTI LINE STRING', ogr.wkbMultiLineStringZM],
		['MULTI POINT', ogr.wkbMultiPoint],
		['3D MULTI POINT', ogr.wkbMultiPoint25D],
		['MEASURED MULTI POINT', ogr.wkbMultiPointM],
		['3D MEASURED MULTI POINT', ogr.wkbMultiPointZM],
		['MULTI POLYGON', ogr.wkbMultiPolygon],
		['3D MULTI POLYGON', ogr.wkbMultiPolygon25D],
		['MEASURED MULTI POLYGON', ogr.wkbMultiPolygonM],
		['3D MEASURED MULTI POLYGON', ogr.wkbMultiPolygonZM],
		['MULTI SURFACE', ogr.wkbMultiSurface],
		['MEASURED MULTI SURFACE', ogr.wkbMultiSurfaceM],
		['3D MULTI SURFACE', ogr.wkbMultiSurfaceZ],
		['3D MEASURED MULTI SURFACE', ogr.wkbMultiSurfaceZM],
		['POINT', ogr.wkbNDR],
		['NONE', ogr.wkbNone],
		['POINT', ogr.wkbPoint],
		['3D POINT', ogr.wkbPoint25D],
		['MEASURED POINT', ogr.wkbPointM],
		['3D MEASURED POINT', ogr.wkbPointZM],
		['POLYGON', ogr.wkbPolygon],
		['3D POLYGON', ogr.wkbPolygon25D],
		['MEASURED POLYGON', ogr.wkbPolygonM],
		['3D MEASURED POLYGON', ogr.wkbPolygonZM],
		['POLYHEDRALSURFACE', ogr.wkbPolyhedralSurface],
		['MEASURED POLYHEDRALSURFACE', ogr.wkbPolyhedralSurfaceM],
		['3D POLYHEDRALSURFACE', ogr.wkbPolyhedralSurfaceZ],
		['3D MEASURED POLYHEDRALSURFACE', ogr.wkbPolyhedralSurfaceZM],
		['SURFACE', ogr.wkbSurface],
		['MEASURED SURFACE', ogr.wkbSurfaceM],
		['3D SURFACE', ogr.wkbSurfaceZ],
		['3D MEASURED SURFACE', ogr.wkbSurfaceZM],
		['TIN', ogr.wkbTIN],
		['MEASURED TIN', ogr.wkbTINM],
		['3D TIN', ogr.wkbTINZ],
		['3D MEASURED TIN', ogr.wkbTINZM],
		['TRIANGLE', ogr.wkbTriangle],
		['MEASURED TRIANGLE', ogr.wkbTriangleM],
		['3D TRIANGLE', ogr.wkbTriangleZ],
		['3D MEASURED TRIANGLE', ogr.wkbTriangleZM],
		['UNKNOWN (ANY)', ogr.wkbUnknown],
		['UNKNOWN (ANY)', ogr.wkbXDR]
			]
	for each in ltypes:
		if each[0] == name.upper():
			return each[1]


def fieldtypes(name):
	ogt = [
	['INTEGER', ogr.OFTInteger],
	['INTEGERLIST', ogr.OFTIntegerList],
	['REAL', ogr.OFTReal],
	['REALLIST', ogr.OFTRealList],
	['STRING', ogr.OFTString],
	['STRINGLIST', ogr.OFTStringList],
	['WIDESTRING', ogr.OFTWideString],
	['WIDESTRINGLIST', ogr.OFTWideStringList],
	['BINARY', ogr.OFTBinary],
	['DATE', ogr.OFTDate],
	['TIME', ogr.OFTTime],
	['DATETIME', ogr.OFTDateTime],
	['INTEGER64', ogr.OFTInteger64],
	['INTEGER64LIST', ogr.OFTInteger64List],
	['NONE', ogr.OFSTNone],
	['BOOLEAN', ogr.OFSTBoolean],
	['INT16', ogr.OFSTInt16],
	['FLOAT32', ogr.OFSTFloat32],
	['JSON', ogr.OFSTJSON],
	['UUID', ogr.OFSTUUID]
	]
	for each in ogt:
		if each[0] == name.upper():
			return each[1]


class Transformation:
	def __init__(self, sourceprj,targetprj):
		self.sourceprj = _getsrs(sourceprj)
		self.targetprj = _getsrs(targetprj)
		self.transformi = osr.CoordinateTransformation(self.sourceprj, self.targetprj)

	def transform(self, inputgeom):
		outputgeom = ogr.CreateGeometryFromWkb(inputgeom.ExportToIsoWkb())
		if self.sourceprj != self.targetprj:
			outputgeom.Transform(self.transformi)
		return outputgeom


def getschema(layer):
	sch = []
	schema = layer.schema
	for reg in schema:
		fieldName = reg.GetName()
		fieldType = reg.GetTypeName()
		sch.append([fieldName, fieldType])
	return sch


def getfeatgeom(feature):
	geom = feature.GetGeometryRef()
	return geom


def _g2b(geom):
	tbyte = geom.ExportToWkb()
	return tbyte


def _b2g(tbyte):
	geom = ogr.CreateGeometryFromWkb(tbyte)
	return geom


def geomptcount(geom):
	strange = [] # Will lose SWIG object reference in debug mode after ..GetGeometryCount(), if not appended
						# (like pointer having a short lifetime or something else)
	tp = _g2b(geom)
	temp = [tp]
	pc = 0
	while len(temp) > 0:
		tg = None
		pp = temp.pop(0)
		tg = _b2g(pp)
		# strange.append(tg)
		ct = tg.GetGeometryCount()
		if ct == 0:
			ptt = tg.GetPointCount()
			pc += ptt
		else:
			for t in range(0, ct):
				tc = None
				geomo = tg.GetGeometryRef(t)
				gt = geomo.GetGeometryName()
				if gt == 'LINEARRING': # workaround because linearring to WKT or WKB doesn't work..
					ptt = geomo.GetPointCount()
					pc += ptt
					pc -= 1 # linearring duplicates 1 vertice
				else:
					tc = _g2b(geomo)
					temp.append(tc)
	return pc


def multi2list(geom):
	geomlist = []
	cc = geom.GetGeometryCount()
	ct = geom.GetGeometryType()
	if ct == 6 or ct == 5 or ct == 4 or ct == -2147483642 or ct == -2147483643 or ct == -2147483644:
		for t in range(0, cc):
			geomo = geom.GetGeometryRef(t)
			geomlist.append(geomo)
	else:
		geomlist.append(geom)

	return geomlist


def splithalf(geom):
	out = []
	env = geom.GetEnvelope()
	Yhalf = env[2] + (env[3] - env[2]) / 2
	upcutcoords = [(env[0], env[3]), (env[1], env[3]), (env[1], Yhalf), (env[0], Yhalf)]
	downcutcoords = [(env[0], Yhalf), (env[1], Yhalf), (env[1], env[2]), (env[0], env[2])]
	upcutpol = makepol(upcutcoords)
	downcutpol = makepol(downcutcoords)
	result = [upcutpol.Intersection(geom), downcutpol.Intersection(geom)]
	for each in result:
		rn = ogr.CreateGeometryFromWkb(each.ExportToWkb())
		out.append(rn)
	return out


def filternames(path):
	cp = os.path.splitext(path)
	ext = os.path.basename(cp[1]).upper()
	ogt = [
		[ '.SHP', 'ESRI Shapefile' ],
		['.KML', 'LIBKML'],
		['.KMZ', 'LIBKML'],
		# ['.KML', 'KML'],
		# ['.KMZ', 'KML'],
		['.GPKG', 'GPKG'],
		['.GEOJSON', 'GEOJSON']
	]

	for each in ogt:
		if each[0] == ext:
			return each[1]
