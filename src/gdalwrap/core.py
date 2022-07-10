try:
	from osgeo import ogr
	from osgeo import osr
except ImportError as error:
	raise Exception("""ERROR: Could not find the GDAL/OGR Python library bindings.""")
ogr.UseExceptions()
osr.UseExceptions()


def makepol(input):
	ta = input + [input[0]]
	tap = []
	for t in ta:
		tap.append(str(t[0]) + ' ' + str(t[1]))
	st = 'POLYGON((' + ','.join(tap) + '))'
	poly = ogr.CreateGeometryFromWkt(st)
	# poly = poly.ExportToWkb()
	return poly


def _getsrs(srs):
	if len(str(srs)) > 7: #Can expect 'OpenGIS Well Known Text format'
		return srs
	elif len(srs) == 0:
		return None
	else:
		osrs = osr.SpatialReference()
		osrs.ImportFromEPSG(int(srs))
		osrs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
		return osrs


class Setsource:
	def __init__(self, inputshape, srs, Action='Open r', Type='polygon'):
		self.action = Action
		self.shapepath = inputshape
		self.srs = _getsrs(srs)
		self.layer = None
		self.layerdef = None
		self.layertype = None
		self.layertypestr = None
		self.datasource = None
		self.geom = None
		self.feature = None
		self.fid = None

		if Action.upper() == 'CREATE' or Action.upper() == 'MEMORY':
			if Action.upper() == 'CREATE':
				driver = ogr.GetDriverByName("ESRI Shapefile")
				ds = driver.CreateDataSource(inputshape)
			if Action.upper() == 'MEMORY':
				driver = ogr.GetDriverByName("MEMORY")
				ds = driver.CreateDataSource(inputshape)
			gt = layertypes(Type)
			self.layer = ds.CreateLayer('', self.srs, gt)
			self.layertype = gt
			self.layerdef = self.layer.GetLayerDefn()
			self.layertypestr = ogr.GeometryTypeToName(self.layerdef.GetGeomType())

		if Action.upper()[:4] == 'OPEN':
			driver = ogr.GetDriverByName("ESRI Shapefile")
			if Action.upper()[4:].strip() == 'R':
				rw = 0
			elif Action.upper()[4:].strip() == 'RW':
				rw = 1
			ds = driver.Open(inputshape, rw)
			self.layer = ds.GetLayer()
			self.srs = self.layer.GetSpatialRef()
			self.layerdef = self.layer.GetLayerDefn()
			self.layertype = self.layerdef.GetGeomType()
			self.layertypestr = ogr.GeometryTypeToName(self.layerdef.GetGeomType())

		self.datasource = ds

	def getfeature(self, FID):
		self.feature = self.layer.GetFeature(FID)
		self.geom = self.feature.GetGeometryRef()
		self.fid = FID
		return self.feature

	def savefile(self, filename):
		if self.action.upper() != 'MEMORY':
			print("Not a memory dataset")
		else:
			driver = ogr.GetDriverByName("ESRI Shapefile")
			ds = driver.CreateDataSource(filename)
			outly = ds.CreateLayer('', self.srs, self.layertype)
			fields = self.getattrtable()
			for field in fields:  # recreates attribute table on output shapefile
				fieldtype = fieldtypes(field[1])
				outly.CreateField(ogr.FieldDefn(field[0], fieldtype))
			for feature in self.layer:
				outly.CreateFeature(feature)
			ds = None

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
		self.layer.CreateField(ogr.FieldDefn(name, fieldtype))

	def createfeature(self, feature):
		self.layer.CreateFeature(feature)
		self.feature = feature
		self.geom = self.feature.GetGeometryRef()
		self.fid = feature.GetFID()
		return feature

	def geom2feature(self, geom):
		feature = ogr.Feature(self.layerdef)
		feature.SetGeometry(geom)
		self.layer.CreateFeature(feature)
		self.feature = feature
		self.geom = self.feature.GetGeometryRef()
		self.fid = feature.GetFID()
		return feature

	def setfield(self, attr, value):
		self.feature.SetField(attr, value)
		self.layer.SetFeature(self.feature)

	def getlyrextent(self):
		extent = []
		le = self.layer.GetExtent()
		for t in le:
			extent.append(t)
		return extent


def layertypes(name):
	ltypes =[
		[ '3D MULTI POLYGON', ogr.wkbMultiPolygon25D ],
		['3D MULTI LINE STRING', ogr.wkbMultiLineString25D],
		['3D MULTI POINT', ogr.wkbMultiPoint25D],
		['3D LINE STRING', ogr.wkbLineString25D],
		['3D POINT', ogr.wkbPoint25D],
		['3D POLYGON', ogr.wkbPolygon25D],
		['POLYGON', ogr.wkbPolygon],
		['POINT', ogr.wkbPoint],
		['LINE', ogr.wkbLineString],
		['LINE STRING', ogr.wkbLineString],
		['MULTI POINT', ogr.wkbMultiPoint],
		['MULTILINE', ogr.wkbMultiLineString],
		['MULTIPOLYGON', ogr.wkbMultiPolygon]
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


def g2b(geom):
	tbyte = geom.ExportToWkb()
	return tbyte


def b2g(tbyte):
	geom = ogr.CreateGeometryFromWkb(tbyte)
	return geom


def geomptcount(geom):
	strange = [] # Will lose SWIG object reference in debug mode after ..GetGeometryCount(), if not appended
						# (like pointer having a short lifetime or something else)
	tp = g2b(geom)
	temp = [tp]
	pc = 0
	while len(temp) > 0:
		tg = None
		pp = temp.pop(0)
		tg = b2g(pp)
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
					tc = g2b(geomo)
					temp.append(tc)
	return pc


def multi2list(geom):
	geomlist = []
	cc = geom.GetGeometryCount()
	ct = geom.GetGeometryType()
	if ct == 6 or ct == 5:
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