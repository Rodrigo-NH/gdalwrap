from random import random
import os
from osgeo import ogr
from gdalwrap import Datasource
from gdalwrap import makepol
from gdalwrap import Layergrid
from gdalwrap import layerclip
from gdalwrap import splitvertices
from gdalwrap import splitrings
from gdalwrap import makepoint
from gdalwrap import makecircle
from gdalwrap import geomptcount
from gdalwrap import Transformation

# os.environ['SHAPE_ENCODING'] = "cp1252"
# ZIP with files used in these examples: https://github.com/Rodrigo-NH/assets/blob/main/files/gdalwrap/examples.zip
# Set examplespath pointing to folder containing files extracted from ZIP
examplespath = r'e:\shapes'

# Set and configure postgreSQL access or comment out postgreSQL examples (needs PostGIS)
dbserver = "192.168.0.113"
dbport = "5432"
dbname = "geotest"
dbuser = "geo"  # Use superuser account and example30() if you want to CREATE required potsgis extensions for the DB
dbpassw = "4bnyK5XMDGQZmGEmdMye"  # Not a password leak
connstr = 'postgresql://%s:%s@%s:%s/%s' % (dbuser, dbpassw, dbserver, dbport, dbname)


def main():
    # Pick your example or batch run:
    example01()  # Iterate over shapefile attributes and geoms
    example02()  # Create memory dataset, populate, export to multiple formats, get/set/change attributes
    example03()  # Layergrid grid generator function example
    example04()  # layerclip function
    example05()  # splitvertices function
    example06()  # splitrings + splitvertices function
    example07()  # Iterate over KML/KMZ file features
    example08()  # Saves a shapefile to GPKG and KML files, reproject output
    example09()  # Export KMZ to a multilayer GPKG
    example10()  # Export KMZ to multiple SHP files grouped by geometry type, reproject output
    example11()  # Create a KML file and apply style
    example12()  # Filter by attribute and delete features
    example13()  # Merge shapefiles
    example30()  # PostGIS Enable PostGIS extensions on DB
    example31()  # PostGIS create layer and fill with 100000 random polygons
    example32()  # PostGIS test iterator
    example33()  # PostGIS manipulate data
    example34()  # Save SHP and GPKG to postGIS tables


def example01():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    inshp = Datasource(inputshape, Action='open r')
    print(inshp.datasource)  # Direct access to gdal datasource object
    layer = inshp.getlayer(0)
    print(layer.layer)  # Direct access to gdal layer object
    fields = layer.getattrtable()  # python list with [fieldname, fieldtype]
    print(fields)
    print("This layer has " + str(layer.getfeaturecount()) + " features.")

    iter = layer.iterfeatures()
    for feature in iter:
        FID = feature.getfid()
        print("FID: " + str(FID))
        fieldval = feature.getfield(fields[4][0])
        print("Field: " + fields[4][0] + ' --> ' + str(fieldval))
        geomc = feature.getgeom()  # geom class
        print(geomc.geom)  # Direct access to gdal geometry object
        print('===================================================================================')


def example02():
    outshp = Datasource('myMemLayer', Action='memory')
    outshp.Newlayer('polygons_1', '4326', Type='polygon')
    layer = outshp.getlayer('polygons_1')
    layer.createfield('Name', 'string')  # Create attribute field
    layer.createfield('NIindex', 'integer')
    for t in range(0, 10):
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        feat = layer.Newfeature()
        feat.setgeom(geom)
        feat.insert()  # Saves/insert newly created Feature to layer
        FID = feat.getfid()  # We can retrieve FID After geom inserted on layer
        feat.setfield('Name', 'P1-' + str(FID))
        feat.setfield('NIindex', t)

    filepath = os.path.join(examplespath, 'example02.shp')  # Save results until now to shapefile
    outshp.savefile(filepath)
    filepath = os.path.join(examplespath, 'example02.geojson')  # Save results until now to geojson
    outshp.savefile(filepath)

    fidtable = []
    featureiterator = layer.iterfeatures(Action='reset')
    for feat in featureiterator:
        FID = feat.getfid()
        fidtable.append(FID)

    outshp.Newlayer('polygons_2', '4326', Type='polygon')
    ly = outshp.getlayer('polygons_2')
    ly.createfield('Name', 'string')
    outshp.Newlayer('intersections', '4326', Type='polygon')
    ly = outshp.getlayer('intersections')
    ly.createfield('Name', 'string')

    lyi = outshp.getlayer('polygons_1')
    for index in range(0, lyi.getfeaturecount()):
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        ly1 = outshp.getlayer('polygons_2')
        feat = ly1.Newfeature()
        feat.setgeom(geom)
        feat.insert()
        feat.setfield('Name', 'P2-' + str(fidtable[index]))
        ly2 = outshp.getlayer('polygons_1')
        fin = ly2.getfeature(fidtable[index])
        geom3 = fin.getgeom().geom
        geom3 = geom.Intersection(geom3)
        ly3 = outshp.getlayer('intersections')
        feat = ly3.Newfeature()
        feat.setgeom(geom3)
        feat.insert()
        feat.setfield('Name', 'I-' + str(fidtable[index]))

    filepath = os.path.join(examplespath, 'example02.gpkg')  # Save final result to geopackage
    outshp.savefile(filepath)

    filepath = os.path.join(examplespath, 'example02.shp')
    rework = Datasource(filepath, Action='open rw')  # Open recently created shape in RW mode
    ly = rework.getlayer(0)
    print(ly.getspatialref())
    print(ly.getfeaturecount())  # Prints number of features in the shape
    rf = ly.getfeature(5)  #  # Random access. Get feature FID=5 (and makes it the current feature),
    rf.setfield('Name', 'NotInterested')  # Change current selected feature attr field


def example03():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outputshape = os.path.join(examplespath, 'example03.shp')
    inshp = Datasource(inputshape, Action='open r')

    outshp = Datasource(outputshape, Action='create')
    outshp.Newlayer('', inshp.getlayer(0).getspatialref(), Type=inshp.getlayer(0).getgeomtypename())
    ly1 = outshp.getlayer(0)
    ly1.createfield('gridIndex', 'string')

    grid = Layergrid(inshp.getlayer(0).layer, 10, 5, Type='tilenumbers')  # Creates a grid layer
    print(grid.getspatialref())  # Layergrid inherits srs from input shapefile
    gridcol = grid.getgrid()  # get list of polygons from grid
    for t in range(0, len(gridcol)):
        geom = gridcol[t]
        feat = ly1.Newfeature()
        feat.setgeom(geom)
        feat.insert()
        gridindex = grid.gridindex[t]  # get autogenerated index for grid tile
        feat.setfield('gridIndex', gridindex)  # set attribute value for giving feature


def example04():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outputshape = os.path.join(examplespath, 'example04.shp')
    inshp = Datasource(inputshape, Action='open r')
    inly = inshp.getlayer(0)
    outshp = Datasource(outputshape, Action='create')
    outshp.Newlayer('', inly.getspatialref(), Type='polygon')
    outly = outshp.getlayer(0)

    grid = Layergrid(inly.layer, 10, 5, Type='mapunits')
    gridcol = grid.getgrid()  # get list of polygons from grid
    fields = inly.getattrtable()
    outly.setattrtable(fields)
    for t in range(0, len(gridcol)):
        clipfeatures = layerclip(inly.layer, gridcol[t])
        for feature in clipfeatures:
            nfeat = outly.Newfeature()
            nfeat.setfeature(feature)
            nfeat.insert()


def example05():
    inshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outshape = os.path.join(examplespath, 'example05.shp')
    inshp = Datasource(inshape, Action='open r')
    ly1 = inshp.getlayer(0)
    outshp = Datasource('mymemlayer', Action='memory')
    outshp.Newlayer('layer1', ly1.getspatialref(), Type='Polygon')
    oly = outshp.getlayer('layer1')
    fields = ly1.getattrtable()
    oly.setattrtable(fields)
    fi = ly1.iterfeatures()  # Wraps OGR '.GetNextFeature()'
    for featc in fi:
        featset = splitvertices(featc.feature, 50)
        for each in featset:
            nfeat = oly.Newfeature()
            nfeat.setfeature(each)
            nfeat.insert()
    outshp.savefile(outshape)


def example06():
    inshape = os.path.join(examplespath, 'rings.shp')
    outshape = os.path.join(examplespath, 'example06.shp')
    inshp = Datasource(inshape, Action='open r')
    inly = inshp.getlayer(0)
    outshp = Datasource('mymemlayer', Action='memory')
    outshp.Newlayer('', inly.getspatialref(), Type='Polygon')
    oly = outshp.getlayer(0)
    fields = inly.getattrtable()
    oly.setattrtable(fields)
    for t in range(0, inly.getfeaturecount()):
        ife = inly.getfeature(t)
        featset = splitrings(ife.feature)
        for each in featset:
            featset2 = splitvertices(each, 50)
            for f in featset2:
                nfeat = oly.Newfeature()
                nfeat.setfeature(f)
                nfeat.insert()
    outshp.savefile(outshape)


def example07():
    filepath = os.path.join(examplespath, 'examplekmz.kmz')
    kmzset = Datasource(filepath, Action='open r')
    for g in range(0, kmzset.getlayercount()):
        inly = kmzset.getlayer(g)
        attrbt = inly.getattrtable()
        print(attrbt)
        fi = inly.iterfeatures(Action='reset')
        for feat in fi:
            ff = feat.getfield('Name')
            print(ff)
            print(feat.getgeom().geom)


def example08():
    input = os.path.join(examplespath, 'example02.shp')
    dest = Datasource(input, Action='open r')

    output = os.path.join(examplespath, 'example08.gpkg')
    dest.savefile(output, Transform='4276')
    output = os.path.join(examplespath, 'example08.kml')
    dest.savefile(output)
    output = os.path.join(examplespath, 'example08.pdf')
    dest.savefile(output)
    output = os.path.join(examplespath, 'example08.geojson')
    dest.savefile(output)


def example09():  # Export KMZ to a multilayer GPKG. KMZ contains mixed geometry types per 'layer'.
    # Separate geoms by type, create a separate layer for each type and save to GPKG

    input = os.path.join(examplespath, 'examplekmz.kmz')
    output1 = os.path.join(examplespath, 'example09.gpkg')
    output2 = os.path.join(examplespath, 'example09.pdf')
    output3 = os.path.join(examplespath, 'example09.shp')
    work = Datasource(input, Action='open r')
    tempw = Datasource('tempsource', Action='memory')

    geomtypes = []
    for li in range(0, work.getlayercount()):
        ly1 = work.getlayer(li)
        attrbt = ly1.getattrtable()
        fi = ly1.iterfeatures()
        for feature in fi:
            gt = feature.getgeom().getgeomtypename()
            if gt not in geomtypes:
                geomtypes.append(gt)
                tempw.Newlayer(gt, '4326', Type=gt)
                ly2 = tempw.getlayer(gt)
                ly2.setattrtable(attrbt)
            layindex = geomtypes.index(gt)
            ly2 = tempw.getlayer(layindex)
            nfeat = ly2.Newfeature()
            nfeat.setfeature(feature.feature)
            nfeat.insert()
    tempw.savefile(output1)
    tempw.savefile(output2)
    tempw.savefile(output3)


def example10():  # Export KMZ to multiple SHP files. KMZ contains mixed geometry types per 'layer'.
    # Separate geoms by type, create a separate SHP file for each type

    input = os.path.join(examplespath, 'examplekmz.kmz')
    output = os.path.join(examplespath, 'example10.shp')
    work = Datasource(input, Action='open r')

    geomtypes = []
    tempsources = []
    for li in range(0, work.getlayercount()):
        ly1 = work.getlayer(li)
        attrbt = ly1.getattrtable()
        fi = ly1.iterfeatures()
        for tf in fi:
            gt = tf.getgeom().getgeomtypename()
            if gt not in geomtypes:
                tempw = Datasource(gt, Action='memory')
                geomtypes.append(gt)
                tempw.Newlayer(gt, '4326', Type=gt)
                ly2 = tempw.getlayer(gt)
                ly2.setattrtable(attrbt)
                tempsources.append(tempw)
            sourceindex = geomtypes.index(gt)
            tw = tempsources[sourceindex]
            ly3 = tw.getlayer(0)
            nf = ly3.Newfeature()
            nf.setfeature(tf.feature)
            nf.insert()

    for index in range(0, len(geomtypes)):
        sptx = os.path.splitext(output)
        outfile = os.path.join(sptx[0] + '_' + geomtypes[index].replace(' ', '') + sptx[1])
        tw = tempsources[index]
        tw.savefile(outfile, Transform='4326')


def example11():
    pol = [[-2, 0], [2, 0], [0, 2]]
    pol2 = makepol(pol)
    point = [0, 1]
    point2 = makepoint(point)

    outkml = os.path.join(examplespath, 'example11.kml')
    outstyletable = os.path.join(examplespath, 'styletable.txt')
    out = Datasource(outkml, Action='create')
    out.Newlayer('Folder', '4326', Type='Polygon')
    ly1 = out.getlayer('Folder')
    style_table = ogr.StyleTable()
    style_table.AddStyle('CoCoNuT', 'PEN(c:#C81B75FF,w:5.0px);BRUSH(fc:#1d8aa8C8)')
    style_table.AddStyle('CoCoNuT2',
                         'SYMBOL(id:"http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",'
                         'c:#FFAA00FF,s:1.2);LABEL(c:#FFFF00FF)')
    style_table.SaveStyleTable(outstyletable)  # Optional
    out.datasource.SetStyleTable(style_table)

    ly1.createfield('Name', 'string')
    feat = ly1.Newfeature()
    feat.setgeom(pol2)
    feat.setfield('Name', 'Some Polygon')
    feat.feature.SetStyleString('@CoCoNuT')
    feat.insert()

    feat2 = ly1.Newfeature()
    feat2.setgeom(point2)
    feat2.setfield('Name', 'Some Point')
    feat2.feature.SetStyleString('@CoCoNuT2')
    feat2.insert()

    outpdf = os.path.join(examplespath, 'example11.pdf')
    out.savefile(outpdf)


def example12():
    shpp = os.path.join(examplespath, 'example04.shp')
    shpout = os.path.join(examplespath, 'example12.shp')
    gpout = os.path.join(examplespath, 'example12.gpkg')
    shp = Datasource(shpp, Action='open r')
    print("Save to SHP and GPKG")
    shp.savefile(shpout)
    shp.savefile(gpout)

    nshp = Datasource(shpout, Action='open rw')
    npkg = Datasource(gpout, Action='open rw')

    dc = [npkg, nshp]
    for source in dc:
        ly1 = source.getlayer(0)
        attr = ly1.getattrtable()
        print("Delete attributes ")
        for field in attr:
            ly1.deletefield(field[0])
        ly1.createfield('isDel', Type='integer')
        it = ly1.iterfeatures(Action='reset')
        ct = 0
        print("Set new attributes ")
        for feat in it:
            if ct == 0:
                feat.setfield('isDel', 0)
                ct = 1
            else:
                feat.setfield('isDel', 1)
                ct = 0
        ly1.attributefilter('isDel = 1')
        it = ly1.iterfeatures(Action='reset')  # iterate again now filtered
        print("Delete features ")
        for feat in it:
            feat.delete()


def example13():
    shp1f = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    shp2f = os.path.join(examplespath, 'example12.shp')
    shpoutf = os.path.join(examplespath, 'example13.shp')
    shp1 = Datasource(shp1f, Action='open r')
    shp2 = Datasource(shp2f, Action='open r')
    shptemp = Datasource(shp1f, Action='memory')

    at1 = shp1.getlayer('').getattrtable()
    at2 = at1 + shp2.getlayer('').getattrtable()
    attrtable = []
    [attrtable.append(x) for x in at2 if x not in attrtable]

    shptemp.Newlayer('', shp1.getlayer('').getspatialref(), Type=shp1.getlayer('').getgeomtypename())
    temply = shptemp.getlayer('')
    temply.setattrtable(attrtable)
    inlayers = [shp1.getlayer(''), shp2.getlayer('')]

    for ly in inlayers:
        it = ly.iterfeatures()
        for feat in it:
            nf = temply.Newfeature()
            for field in attrtable:
                if feat.getfieldindex(field[0]) > -1:
                    nf.setfield(field[0], feat.getfield(field[0]))
                    nf.setgeom(feat.getgeom().geom)
            nf.insert()

    shptemp.savefile(shpoutf)


def example30():
    conn = Datasource(connstr, Action='open rw')
    sql = conn.executesql('SELECT * FROM pg_extension')
    exts = []
    for tb in sql:
        exts.append(tb.GetField(1).upper())
    if 'POSTGIS' not in exts:
        print("Enable PostGIS extensions")
        conn.datasource.ExecuteSQL('CREATE EXTENSION postgis')
        conn.datasource.ExecuteSQL('CREATE EXTENSION postgis_topology')


def example31():
    conn = Datasource(connstr, Action='open rw')
    conn.Newlayer('randompols', '4326', Type='Polygon')
    conn.Newlayer('randompols2', '4326', Type='Polygon')
    ly1 = conn.getlayer('randompols')
    ly1.createfield('Name', 'string')
    ly1.createfield('NIindex', 'integer')
    ly2 = conn.getlayer('randompols2')
    ly2.createfield('Name', 'string')
    ly2.createfield('NIindex', 'integer')
    ct = 0
    cc = 0
    for t in range(0, 100):
        print("Create: " + str(ct))
        ct += 1
        if cc == 0:  # Slow switching
            lyw = conn.getlayer('randompols')
            cc = 1
        else:
            lyw = conn.getlayer('randompols2')
            cc = 0
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        feat = lyw.Newfeature()
        feat.setgeom(geom)
        feat.setfield('Name', 'NI-' + str(t).zfill(6))
        feat.setfield('NIindex', t)
        feat.insert()


def example32():
    conn = Datasource(connstr, Action='open rw')
    ly1 = conn.getlayer('randompols')
    politer = ly1.iterfeatures(Action='reset')  # '.ResetReading()' is passed to layer when "Action='reset'"
    ct = 0
    for feature in politer:
        print(ct)
        print(feature.getgeom().getgeomtypename())
        print(feature.getgeom().geom)
        ct += 1


def example33():
    conn = Datasource(connstr, Action='open rw')
    ly1 = conn.getlayer('randompols')
    ly1.createfield('isEven', 'integer')
    ly1.createfield('circleOfFID', 'integer')
    ly1.createfield('conferfid', 'integer')
    ly1.createfield('geomVcount', 'string')
    ct = 0
    it = ly1.iterfeatures(Action='reset')
    for feature in it:
        feature.setfield('conferfid', feature.getfid())
        centroidpoint = feature.getgeom().geom.Centroid()
        if (feature.getfid() % 2) == 0:
            adds = [1, 10]
        else:
            adds = [0, 1]
        feature.setfield('isEven', adds[0])
        crcgeom = makecircle(centroidpoint, 0.09, adds[1])
        nfeat = ly1.Newfeature()
        nfeat.setgeom(crcgeom)
        nfeat.setfield('Name', 'Centroid')
        nfeat.setfield('circleOfFID', feature.getfid())
        verticecount = geomptcount(crcgeom)
        nfeat.setfield('geomVcount', 'Polygon has ' + str(verticecount) + ' vertices')
        nfeat.insert()
        nfeat.setfield('conferfid', nfeat.getfid())
        print("Processing: " + str(ct))
        ct += 1


def example34():
    gpinp = os.path.join(examplespath, 'example09.gpkg')
    gpin = Datasource(gpinp, Action='open rw')
    gpin.savefile(connstr)

    shpip = os.path.join(examplespath, 'example12.shp')
    shpi = Datasource(shpip, Action='open rw')
    shpi.savefile(connstr)


if __name__ == "__main__":
    main()
