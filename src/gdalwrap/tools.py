try:
	from osgeo import ogr
	from osgeo import osr
except ImportError as error:
	raise Exception("""ERROR: Could not find the GDAL/OGR Python library bindings.""")

ogr.UseExceptions()
osr.UseExceptions()

from gdalwrap.core import *
from gdalwrap.core import _g2b, _b2g


def layerclip(layer, clipgeom):
	sch = []
	schema = layer.schema
	for reg in schema:
		fieldName = reg.GetName()
		fieldType = reg.GetTypeName()
		sch.append([fieldName, fieldType])

	features = []
	defn = layer.GetLayerDefn()
	layer.SetSpatialFilter(clipgeom)
	for f in layer:
		d = f.GetGeometryRef()
		cut = clipgeom.Intersection(d)
		feature = ogr.Feature(defn)
		feature.SetGeometry(cut)
		for field in sch:
			fvalue = f.GetField(field[0])
			feature.SetField(field[0], fvalue)
		features.append(feature)
	return features


def splitvertices(feature, vcount):
	featpoll = []
	if vcount < 3:
		featpoll.append(feature)
	else:
		geom = feature.GetGeometryRef()
		g = _g2b(geom)
		temppoll = []
		temppoll.append(g)
		polcoll = []
		strange = [] # Will lose SWIG object reference in debug mode after .GetGeometryType(), if not appended
							# (like pointer having a short lifetime or something else)

		while len(temppoll) > 0:
			ct = temppoll.pop(0)
			el = None
			el = _b2g(ct)
			# strange.append(el)
			gl = multi2list(el)
			for geom in gl:
				gcount = geomptcount(geom)
				if gcount > vcount:
					# TS = True
					gsplit = splithalf(geom)
					temppoll.append(_g2b(gsplit[0]))
					temppoll.append(_g2b(gsplit[1]))
				else:
					polcoll.append(_g2b(geom))

		for each in polcoll:
			geom = _b2g(each)
			dfn = feature.GetDefnRef()
			ofeature = ogr.Feature(dfn)
			ofeature.SetGeometry(geom)
			for f in range(0, feature.GetFieldCount()):
				ft = feature.GetField(f)
				ofeature.SetField(f, ft)
			featpoll.append(ofeature)

	return featpoll


def splitrings(feature):
	geom = feature.GetGeometryRef()
	igeom = _g2b(geom)
	tg = _b2g(igeom)
	typ = tg.GetGeometryType()
	featpoll = []
	if typ == 6 or typ == 3:
		polcoll = []
		temppoll = []
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
	else:
		featpoll.append(feature)

	return featpoll


class Layergrid:
	def __init__(self, layer,xsteps, ysteps, Type='mapunits'):
		self.type = Type
		self.layer = layer
		self.xsteps = xsteps
		self.ysteps = ysteps
		self.grid = []
		self.gridindex = []
		self.srsv = layer.GetSpatialRef()

		extent = layer.GetExtent()
		totalX = abs(extent[0] - extent[1])
		totalY = abs(extent[2] - extent[3])
		if self.type.upper() == 'MAPUNITS':
			divX = int(round(totalX / xsteps))
			divY = int(round(totalY / ysteps))
		elif self.type.upper() == 'TILENUMBERS':
			divX = xsteps
			divY = ysteps

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

	def getspatialref(self):
		return self.srsv

def scanfiles(folder, extension):
	files = []
	filesout = []
	for (dirpath, dirnames, filenames) in os.walk(folder):
		files.extend(filenames)
		break
	for each in files:
		basename = os.path.basename(each)
		sp = basename.split('.')
		if sp[1].upper() == extension.upper() and len(sp) == 2:
			cp = os.path.join(folder, each)
			filesout.append(cp)
	return filesout
