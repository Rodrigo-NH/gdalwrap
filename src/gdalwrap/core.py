try:
    from osgeo import ogr
    from osgeo import osr
except ImportError as error:
    raise Exception("""ERROR: Could not find the GDAL/OGR Python library bindings.""")
import os
import warnings

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


# https://gdal.org/doxygen/classGDALDataset.html#a8cfa4d17c68e441614118931b17cd7fa
# https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html
class Datasource:
    def __init__(self, inputshape, Action='Open r'):
        self.datasource = None

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

    def executesql(self, sql):
        return self.datasource.ExecuteSQL(sql)

    def getlayercount(self):
        return self.datasource.GetLayerCount()

    def getdriver(self):
        return self.datasource.GetDriver()

    def getdrivername(self):
        return self.datasource.GetDriver().GetName()

    def getlayer(self, ln):
        if ln == '':
            ln = 0
        return self._Layer(self, ln)

    def deletelayer(self, ln):
        self.datasource.DeleteLayer(ln)

    def Newlayer(self, name, srs, Type):
        return self._Layer(self, 0, name=name, srs=srs, Type=Type, New=True)

    def savefile(self, filename, Transform=None):
        driver = ogr.GetDriverByName(filternames(filename))
        dest = driver.CreateDataSource(filename)
        drivername = dest.GetDriver().GetName()
        style_table = self.datasource.GetStyleTable()
        dest.SetStyleTable(style_table)
        for ind in range(0, self.getlayercount()):
            layer = self.getlayer(ind)
            layergeomtype = layer.getgeomtypename()
            if layergeomtype == 'Unknown (any)':  # Layer without a geometry type (e.g. KML)
                infeat = layer.getfeature(0)  # Not secure, must improve
                geome = infeat.getgeom()
                layergeomtype = geome.gettypename()
            else:
                layergeomtype = _conformgpkg(drivername, layergeomtype)
            destsrs = layer.layer.GetSpatialRef()
            if Transform is not None:
                trans = Transformation(layer.layer.GetSpatialRef(), Transform)
                destsrs = Transform
            dest.CreateLayer(layer.layer.GetName(), _getsrs(destsrs), layertypes(layergeomtype))
            olayer = dest.GetLayer(layer.layer.GetName())
            if olayer is None:
                olayer = dest.GetLayer()
            inatt = layer.getattrtable()
            for field in inatt:
                fieldtype = fieldtypes(field[1])
                olayer.CreateField(ogr.FieldDefn(field[0], fieldtype))
            it = layer.iterfeatures(Action='reset')
            for feat in it:
                featstyle = feat.feature.GetStyleString()
                geom = feat.getgeom().geom
                layer.layer.GetSpatialRef()
                if Transform is not None:
                    geom = trans.transform(geom)
                ofeature = ogr.Feature(olayer.GetLayerDefn())
                geom = _conformgpkggeom(drivername, geom, layergeomtype)
                ofeature.SetGeometry(geom)
                ofeature.SetStyleString(featstyle)
                for f in range(0, feat.feature.GetFieldCount()):
                    ft = feat.feature.GetField(f)
                    ofeature.SetField(f, ft)
                olayer.CreateFeature(ofeature)
    dest = None

    # https://gdal.org/doxygen/classGDALDataset_1_1Layers.html
    class _Layer:
        def __init__(self, Datasource, ln, **kwargs):
            self.Datasource = Datasource
            self.layer = None
            self.layerdef = None
            if 'New' in kwargs:
                typ = layertypes(kwargs['Type'])
                self.Datasource.datasource.CreateLayer(kwargs['name'], _getsrs(kwargs['srs']), typ)
            else:
                self.layer = self.Datasource.datasource.GetLayer(ln)
                self.layerdef = self.layer.GetLayerDefn()
        # self.featcopy = []

        def attributefilter(self, filter):
            self.layer.SetAttributeFilter(filter)

        def getattrtable(self):
            sch = []
            schema = self.layer.schema
            for reg in schema:
                fieldName = reg.GetName()
                fieldType = reg.GetTypeName()
                sch.append([fieldName, fieldType])
            self.attrtable = sch
            return sch

        def getfeaturecount(self):
            fc = self.layer.GetFeatureCount()
            return fc

        def getspatialref(self):
            return self.layer.GetSpatialRef()

        def getgeomtype(self):
            return self.layerdef.GetGeomType()

        def getgeomtypename(self):
            return ogr.GeometryTypeToName(self.layerdef.GetGeomType())

        def iterfeatures(self, Action=None):
            if Action == 'reset':
                self.layer.ResetReading()
            ftv = self.layer.GetNextFeature()
            while ftv is not None:
                nft = self.Datasource._Feature(self, 0, Iterator=True, Fdata=ftv)  # 'new'
                yield nft
                ftv = self.layer.GetNextFeature()
        # nft.feature = None

        def createfield(self, name, Type='integer'):
            # driver = ogr.GetDriverByName("MEMORY")
            # ds = driver.CreateDataSource('createfieldtempsource')
            # nl = ds.CreateLayer('fieldtempsource', self.layer.GetSpatialRef(), self.layerdef.GetGeomType())
            # nld = nl.GetLayerDefn()
            # inatt = self.getattrtable()
            # for field in inatt:
            # 	fieldtype = fieldtypes(field[1])
            # 	nl.CreateField(ogr.FieldDefn(field[0], fieldtype))
            #
            # featuredata = []
            # idx = 0
            # for i in self.featcopy:
            # 	if i.feature is None:
            # 		self.featcopy.pop(idx)
            # 	else:
            # 		attr = []
            # 		fid = i.feature.GetFID()
            # 		nft = ogr.Feature(nld)
            # 		nft.SetFrom(i.feature)
            # 		i.feature = None
            # 		attr.append(fid)
            # 		attr.append(nft)
            # 		featuredata.append(attr)
            # 	idx += 1

            fieldtype = fieldtypes(Type)
            fdn = ogr.FieldDefn(name, fieldtype)
            self.layer.CreateField(fdn)

            # idx = 0
            # for i in self.featcopy:
            # 	nft = ogr.Feature(self.layerdef)
            # 	nft.SetFrom(featuredata[idx][1])
            # 	nft.SetFID(featuredata[idx][0])
            # 	i.feature = nft
            # 	idx += 1

        def deletefeature(self, fid):
            self.layer.DeleteFeature(fid)

        def deletefield(self, fieldname):
            at = self.getattrtable()
            atn = []
            for i in at:
                atn.append(i[0])
            id = atn.index(fieldname)
            self.layer.DeleteField(id)

        def getfeature(self, fn):
            ft = self.Datasource._Feature(self, fn)
            # self.featcopy.append(ft)
            return ft

        def Newfeature(self, *args, **kwargs):
            nft = self.Datasource._Feature(self, 0, New=True)
            # self.featcopy.append(nft)
            return nft

        def setattrtable(self, attrtable):
            actl = self.getattrtable()
            actualtable = [x[0].upper() for x in actl]
            create = True
            for field in attrtable:  # recreates attribute table
                if self.Datasource.getdrivername() == 'DXF':
                    create = _dxffieldfilter(field[0])  # Unssopported by DXF driver if create = False
                if create:
                    if field[0].upper() not in actualtable:
                        fieldtype = fieldtypes(field[1])
                        self.layer.CreateField(ogr.FieldDefn(field[0], fieldtype))

    # https://gdal.org/doxygen/classOGRFeature.html
    class _Feature:
        def __init__(self, _Layer, fn, **kwargs):
            self._Layer = _Layer
            if 'New' in kwargs:
                self.feature = ogr.Feature(self._Layer.layerdef)
            elif 'Iterator' in kwargs:
                self.feature = kwargs['Fdata']
            else:
                self.feature = self._Layer.layer.GetFeature(fn)

        def getfid(self):
            fid = self.feature.GetFID()
            return fid

        def getfield(self, attr):
            fv = self.feature.GetField(attr)
            return fv

        def getfieldindex(self, field):
            return self.feature.GetFieldIndex(field)

        def getfieldcount(self):
            return self.feature.GetFieldCount()

        def setfeature(self, feat):
            self.feature = feat

        def setfield(self, attr, value):
            self.feature.SetField(attr, value)
            fid = self.feature.GetFID()
            if fid != -1:
                self._Layer.layer.SetFeature(self.feature)

        def getgeom(self):
            ft = self._Layer.Datasource._Geom(self)
            return ft

        def setgeom(self, geom):
            self.feature.SetGeometry(geom)

        def insert(self):
            self._Layer.layer.CreateFeature(self.feature)

        def delete(self):
            fid = self.feature.GetFID()
            if fid != -1:
                self._Layer.layer.DeleteFeature(fid)
            self.feature = None
            try:
                idx = self._Layer.featcopy.index(self)
                self._Layer.featcopy.pop(idx)
            except:
                pass

    class _Geom:
        def __init__(self, _Feature, **kwargs):
            self._Feature = _Feature
            self.geom = self._Feature.feature.GetGeometryRef()

        def getgeomtype(self):
            tp = self.geom.GetGeometryType()
            return tp

        def getgeomtypename(self):
            gn = self.geom.GetGeometryName()
            return gn

        def exportwkt(self):
            wkt = self.geom.ExportToWkt()
            return wkt


def _copyfields(src, dest):
    for f in range(0, src.GetFieldCount()):
        ft = src.feature.GetField(f)
        dest.SetField(f, ft)


def _testmultitypes(setsourceobject):
    shptypes = []
    for sh in range(0, setsourceobject.getlayercount()):
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
    ltypes = [
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
        ['LINESTRING', ogr.wkbLineString],
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
    def __init__(self, sourceprj, targetprj):
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


def _g2b(geom):
    tbyte = geom.ExportToWkb()
    return tbyte


def _b2g(tbyte):
    geom = ogr.CreateGeometryFromWkb(tbyte)
    return geom


def geomptcount(geom):
    strange = []  # Will lose SWIG object reference in debug mode after ..GetGeometryCount(), if not appended
    # (like pointer having a short lifetime or something else)
    tp = _g2b(geom)
    temp = [tp]
    pc = 0
    while len(temp) > 0:
        # tg = None
        pp = temp.pop(0)
        tg = _b2g(pp)
        # strange.append(tg)
        ct = tg.GetGeometryCount()
        if ct == 0:
            ptt = tg.GetPointCount()
            pc += ptt
        else:
            for t in range(0, ct):
                # tc = None
                geomo = tg.GetGeometryRef(t)
                gt = geomo.GetGeometryName()
                if gt == 'LINEARRING':  # workaround because linearring to WKT or WKB doesn't work..
                    ptt = geomo.GetPointCount()
                    pc += ptt
                    pc -= 1  # linearring duplicates 1 vertice
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
    if 'POSTGRESQL' in path.upper():
        path = 'conn.POSTGRESQL'
    cp = os.path.splitext(path)
    ext = os.path.basename(cp[1]).upper()

    ogt = [
        ['.SHP', 'ESRI Shapefile'],
        ['.KML', 'LIBKML'],
        ['.KMZ', 'LIBKML'],
        # ['.KML', 'KML'],
        # ['.KMZ', 'KML'],
        ['.GPKG', 'GPKG'],
        ['.GEOJSON', 'GEOJSON'],
        ['.PDF', 'PDF'],
        ['.DXF', 'DXF'],
        ['.POSTGRESQL', 'POSTGRESQL']
    ]

    for each in ogt:
        if each[0] == ext:
            return each[1]


def _dxffieldfilter(field):
    validfields = ['LAYER', 'PAPERSPACE', 'SUBCLASSES', 'EXTENDEDENTITY',
                   'RAWCODEVALUES', 'LINETYPE', 'ENTITYHANDLE', 'TEXT']

    if field.upper() not in validfields:
        return False
    else:
        return True


def _conformgpkg(dn, layergeomtype):  # https://github.com/qgis/QGIS/issues/26684#issuecomment-495888046
    dn = dn.upper()
    lu = layergeomtype.upper()
    if dn == 'GPKG' or dn == 'POSTGRESQL':
        if 'POLYGON' in lu or 'LINE' in lu:
            if 'MULTI' not in lu:
                pts = lu.split(' ')
                if 'POLYGON' in pts:
                    mi = 1
                if 'LINE' in pts:
                    mi = 2
                pts.insert(len(pts) - mi, 'MULTI')
                lu = ' '.join(pts)
                ws = "Warning: will upgrade polygons/lines to multi type for consistency with " + dn
                warnings.warn(ws)
    return lu


def _conformgpkggeom(dn, geom, layergeomtype):  # https://github.com/qgis/QGIS/issues/26684#issuecomment-495888046
    dn = dn.upper()
    lu = layergeomtype.upper()
    geomtname = ogr.GeometryTypeToName(geom.GetGeometryType()).upper()
    if dn == 'GPKG' or dn == 'POSTGRESQL':
        if 'POLYGON' in lu and 'MULTI' not in geomtname:
            mp = ogr.Geometry(ogr.wkbMultiPolygon)
            mp.AddGeometry(geom)
            geom = ogr.CreateGeometryFromWkb(mp.ExportToWkb())
        if 'LINE' in lu and 'MULTI' not in geomtname:
            mp = ogr.Geometry(ogr.wkbMultiLineString)
            mp.AddGeometry(geom)
            geom = ogr.CreateGeometryFromWkb(mp.ExportToWkb())
    return geom
