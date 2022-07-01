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


def layerclip(layer, clipgeom):
	schema = getschema(layer)
	features = []
	defn = layer.GetLayerDefn()
	layer.SetSpatialFilter(clipgeom)
	for f in layer:
		d = f.GetGeometryRef()
		cut = clipgeom.Intersection(d)
		feature = ogr.Feature(defn)
		feature.SetGeometry(cut)
		for field in schema:
			fvalue = f.GetField(field[0])
			feature.SetField(field[0], fvalue)
		features.append(feature)
	return features

def _getsrs(srs):
	if len(str(srs)) > 7: #Can expect 'OpenGIS Well Known Text format'
		return srs
	elif len(srs) == 0:
		return None
	else:
		osrs = osr.SpatialReference()
		osrs.ImportFromEPSG(int(srs))
		return osrs

class Setsource:
	def __init__(self, inputshape, srs, Action='Open r', Type='polygon'):
		self.action = Action
		self.inputshape = inputshape
		self.srsv = _getsrs(srs)
		self.defnn = None
		self.ly = None
		self.seldatasource = None
		self.selgeom = None
		self.selfeat = None
		self.geomtype = None

		if Action.upper() == 'CREATE' or Action.upper() == 'MEMORY':
			if Action.upper() == 'CREATE':
				driver = ogr.GetDriverByName("ESRI Shapefile")
				ds = driver.CreateDataSource(inputshape)
			if Action.upper() == 'MEMORY':
				driver = ogr.GetDriverByName("MEMORY")
				ds = driver.CreateDataSource(inputshape)
			if Type.upper() == 'POLYGON':
				gt = ogr.wkbPolygon
			elif Type.upper() == 'POINT':
				gt = ogr.wkbPoint
			elif Type.upper() == 'LINE':
				gt = ogr.wkbLineString
			elif Type.upper() == 'MULTIPOINT':
				gt = ogr.wkbMultiPoint
			elif Type.upper() == 'MULTILINE':
				gt = ogr.wkbMultiLineString
			elif Type.upper() == 'MULTIPOLYGON':
				gt = ogr.wkbMultiPolygon
			self.ly = ds.CreateLayer('', self.srsv, gt)
			self.defnn = self.ly.GetLayerDefn()
			self.seldatasource = ds
			self.geomtype = gt
		if Action.upper()[:4] == 'OPEN':
			driver = ogr.GetDriverByName("ESRI Shapefile")
			if Action.upper()[4:].strip() == 'R':
				rw = 0
			elif Action.upper()[4:].strip() == 'RW':
				rw = 1
			ds = driver.Open(inputshape, rw)
			self.ly = ds.GetLayer()
			self.srsv = self.ly.GetSpatialRef()
			self.defnn = self.ly.GetLayerDefn()
			self.seldatasource = ds

	def savefile(self, filename):
		if self.action.upper() != 'MEMORY':
			print("Not a memory dataset")
		else:
			driver = ogr.GetDriverByName("ESRI Shapefile")
			ds = driver.CreateDataSource(filename)
			outly = ds.CreateLayer('', self.srsv, self.geomtype)
			fields = self.getattrtable()
			for field in fields:  # recreates attribute table on output shapefile
				fieldtype = fieldtypes(field[1])
				outly.CreateField(ogr.FieldDefn(field[0], fieldtype))
			for feature in self.ly:
				outly.CreateFeature(feature)
			ds = None

	def getsrs(self):
		return self.srsv

	def getgeom(self):
		return self.selgeom

	def getfeature(self,FID):
		self.selfeat = self.ly.GetFeature(FID)
		self.selgeom = self.selfeat.GetGeometryRef()
		return self.selfeat

	def featurecount(self):
		return len(self.ly)

	def getattrtable(self):
		sch = []
		schema = self.ly.schema
		for reg in schema:
			fieldName = reg.GetName()
			fieldType = reg.GetTypeName()
			sch.append([fieldName,fieldType])
		return sch

	def setattrtable(self, attrtable):
		for field in attrtable:  # recreates attribute table on output shapefile
			fieldtype = fieldtypes(field[1])
			self.ly.CreateField(ogr.FieldDefn(field[0], fieldtype))

	def createattr(self, name, Type='integer'):
		fieldtype = fieldtypes(Type)
		self.ly.CreateField(ogr.FieldDefn(name, fieldtype))

	def createfeature(self, feature):
		self.ly.CreateFeature(feature)
		self.selfeat = feature
		return feature

	def geom2feature(self, geom): # velho createfeture from geom
		feature = ogr.Feature(self.defnn)
		feature.SetGeometry(geom)
		self.ly.CreateFeature(feature)
		self.selfeat = feature
		return feature

	def setfield(self, attr, value):
		self.selfeat.SetField(attr, value)
		self.ly.SetFeature(self.selfeat)

	def layer(self):
		return self.ly

	def defn(self):
		return self.defnn


def splitvertices(feature, vcount):
	strange = [] #Will lose SWIG object reference in debug mode after .GetGeometryType(), if not appended
						# (like pointer having a short lifetime)
	polcoll = []
	temppoll = []
	featpoll = []
	geom = feature.GetGeometryRef().ExportToWkb()
	temppoll.append(geom)
	while len(temppoll) > 0:
		current = temppoll.pop(0)
		igeom = ogr.CreateGeometryFromWkb(current)
		# strange.append(igeom)
		gtype = igeom.GetGeometryType()
		if gtype == 6:
			gc = igeom.GetGeometryCount()
			for i in range(0, gc):
				g = igeom.GetGeometryRef(i)
				temppoll.append(g.ExportToWkb())
			current = temppoll.pop()
			igeom = ogr.CreateGeometryFromWkb(current)
		fa = igeom.GetGeometryCount()
		pointcount = 0
		for t in range(0, fa):
			go = igeom.GetGeometryRef(t)
			pc = go.GetPointCount()
			pointcount += pc
		if pointcount > vcount:
			env = igeom.GetEnvelope()
			Yhalf = env[2] + (env[3] - env[2]) / 2
			upcutcoords = [(env[0], env[3]), (env[1], env[3]), (env[1], Yhalf), (env[0], Yhalf)]
			downcutcoords = [(env[0], Yhalf), (env[1], Yhalf), (env[1], env[2]), (env[0], env[2])]
			upcutpol = makepol(upcutcoords)
			downcutpol = makepol(downcutcoords)
			result = [upcutpol.Intersection(igeom), downcutpol.Intersection(igeom)]
			for each in result:
				temppoll.append(each.ExportToWkb())
		else:
			polcoll.append(current)
	for each in polcoll:
		geom = ogr.CreateGeometryFromWkb(each)
		dfn = feature.GetDefnRef()
		ofeature = ogr.Feature(dfn)
		ofeature.SetGeometry(geom)
		for f in range(0, feature.GetFieldCount()):
			ft = feature.GetField(f)
			ofeature.SetField(f, ft)
		featpoll.append(ofeature)
	return featpoll

def splitrings(feature):
	polcoll = []
	temppoll = []
	featpoll = []
	geom = feature.GetGeometryRef().ExportToWkb()
	temppoll.append(geom)
	while len(temppoll) > 0:
		current = temppoll.pop(0)
		igeom = ogr.CreateGeometryFromWkb(current)
		gtype = igeom.GetGeometryType()
		if gtype == 6: #Clip operation may create multipolygon
			for geom in igeom:
				temppoll.append(geom.ExportToWkb())
			current = temppoll.pop()
		geom = ogr.CreateGeometryFromWkb(current)
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
			leftcutcoords = [(Xstart, Ystart), (Xhalf, Ystart), (Xhalf, Yend), (Xstart, Yend)]
			rightcutcoords = [(Xhalf, Ystart), (Xend, Ystart), (Xend, Yend), (Xhalf, Yend)]
			rightcutpol = makepol(rightcutcoords)
			leftcutpol = makepol(leftcutcoords)
			result = [leftcutpol.Intersection(geom),rightcutpol.Intersection(geom)]
			for each in result:
				if each.GetGeometryCount() == 1:
					polcoll.append(each.ExportToWkb())
				else:
					temppoll.append(each.ExportToWkb())
		else:
			polcoll.append(current)

	for each in polcoll:
		dfn = feature.GetDefnRef()
		ofeature = ogr.Feature(dfn)
		ofeature.SetGeometry(ogr.CreateGeometryFromWkb(each))
		for f in range(0, feature.GetFieldCount()):
			ft = feature.GetField(f)
			ofeature.SetField(f, ft)
		featpoll.append(ofeature)
	return featpoll

class Layergrid:
	def __init__(self, layer,xsteps, ysteps):
		self.layer = layer
		self.xsteps = xsteps
		self.ysteps = ysteps
		self.grid = []
		self.gridindex = []
		self.srsv = layer.GetSpatialRef()

		extent = layer.GetExtent()
		totalX = abs(extent[0] - extent[1])
		totalY = abs(extent[2] - extent[3])
		divX = int(round(totalX / xsteps))
		divY = int(round(totalX / ysteps))
		Xstep = totalX / divX
		Ystep = totalY / divY
		Xpos = extent[0]
		Ypos = extent[3]
		# gridcount = divX * divY
		# print(str(gridcount) + ' TILES')
		xindex = 0
		yindex = 0
		for Ytile in range(0, divY):
			for Xtile in range(0, divX):
				coords = [[Xpos, Ypos], [Xpos + Xstep, Ypos], [Xpos + Xstep, Ypos - Ystep], [Xpos, Ypos - Ystep]]
				index = str(xindex) + '_' + str(yindex)
				self.gridindex.append(index)
				self.grid.append(makepol(coords))
				Xpos = Xpos + Xstep
				xindex += 1
			Xpos = extent[0]
			Ypos = Ypos - Ystep
			yindex += 1
			xindex = 0

	def getgrid(self):
		return self.grid

	def gridindex(self, index):
		return self.gridindex[index]

	def getsrs(self):
		return self.srsv

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

def getschema(layer):
	sch = []
	schema = layer.schema
	for reg in schema:
		fieldName = reg.GetName()
		fieldType = reg.GetTypeName()
		sch.append([fieldName, fieldType])
	return sch
