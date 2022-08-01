from random import random
import os, time
from copy import deepcopy, copy
from osgeo import ogr
from gdalwrap import Setsource
from gdalwrap import makepol
from gdalwrap import Layergrid
from gdalwrap import layerclip
from gdalwrap import splitvertices
from gdalwrap import splitrings
from gdalwrap import makepoint
from gdalwrap import getfid
from gdalwrap import makecircle
from gdalwrap import geomptcount
from gdalwrap import Transformation

# ZIP with files used in these examples: https://github.com/Rodrigo-NH/assets/blob/main/files/gdalwrap/examples.zip
# Set examplespath pointing to folder containing files extracted from ZIP
examplespath = r'D:\shapes'

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
    # example30()  # PostGIS Enable PostGIS extensions on DB
    # example31()  # PostGIS create layer and fill with 100000 random polygons
    # example32()  # PostGIS test iterator
    # example33()  # PostGIS manipulate data
    # example34()  # Save SHP and GPKG to postGIS tables


def example01():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    inshp = Setsource(inputshape, Action='open r')
    inshp.getlayer(0)
    fields = inshp.getattrtable()

    for t in range(0, inshp.featurecount()):
        fj = inshp.getfeature(t)  # returns exported OGR feature JSON (optionally) and set
        # class attributes ('.geom' etc)
        FID = getfid(inshp.feature)
        print(str(t) + " = " + str(FID))
        print("Field: " + fields[4][0] + ' --> ' + str(inshp.feature.GetField(fields[4][0])))
        print(inshp.geom)
        print(fj)
        print('===================================================================================')


def example02():
    outshp = Setsource('myMemLayer', Action='memory')
    outshp.createlayer('polygons_1', '4326', Type='polygon')
    outshp.getlayer('polygons_1')
    outshp.createattr('Name', 'string')  # Create attribute field
    outshp.createattr('NIindex', 'integer')
    for t in range(0, 10):
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        feat = outshp.createfeatgeom(geom)  # creates and return new feature
        outshp.createfeature(feat)
        FID = getfid(feat)  # We can retrieve FID After geom inserted on layer
        outshp.setfield(feat, 'Name', 'P1-' + str(FID))
        outshp.setfield(feat, 'NIindex', t)

    filepath = os.path.join(examplespath, 'example02.shp')  # Save results until now to shapefile
    outshp.savefile(filepath)
    filepath = os.path.join(examplespath, 'example02.geojson')  # Save results until now to geojson
    outshp.savefile(filepath)

    fidtable = []
    featureiterator = outshp.iterfeatures(Action='reset')
    for feature in featureiterator:
        FID = getfid(feature)
        fidtable.append(FID)

    outshp.createlayer('polygons_2', '4326', Type='polygon')
    outshp.getlayer('polygons_2')
    outshp.createattr('Name', 'string')
    outshp.createlayer('intersections', '4326', Type='polygon')
    outshp.getlayer('intersections')
    outshp.createattr('Name', 'string')

    outshp.getlayer('polygons_1')
    for index in range(0, outshp.featurecount()):
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        outshp.getlayer('polygons_2')
        feat = outshp.createfeatgeom(geom)
        outshp.createfeature(feat)
        outshp.setfield(feat, 'Name', 'P2-' + str(fidtable[index]))
        outshp.getlayer('polygons_1')
        geom2 = outshp.exportgeom(fidtable[index])
        geom3 = geom.Intersection(geom2)
        outshp.getlayer('intersections')
        feat = outshp.createfeatgeom(geom3)
        outshp.createfeature(feat)
        outshp.setfield(feat, 'Name', 'I-' + str(fidtable[index]))

    filepath = os.path.join(examplespath, 'example02.gpkg')  # Save final result to geopackage
    outshp.savefile(filepath)

    filepath = os.path.join(examplespath, 'example02.shp')
    rework = Setsource(filepath, Action='open rw')  # Open recently created shape in RW mode
    rework.getlayer(0)
    print(rework.srs)  # Prints shape SRS OpenGIS Well Known Text format
    print(rework.featurecount())  # Prints number of features in the shape
    rework.getfeature(5)  # Get feature FID=5 (and makes it the current feature),
    # returns the feature to a variable (geojson), optionally
    rework.setfield(rework.feature, 'Name', 'NotInterested')  # Change current selected feature attr field


def example03():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outputshape = os.path.join(examplespath, 'example03.shp')
    inshp = Setsource(inputshape, Action='open r')
    inshp.getlayer('')
    outshp = Setsource(outputshape, Action='create')
    outshp.createlayer('grid', inshp.srs, Type=inshp.layertypestr)
    outshp.getlayer('grid')
    outshp.createattr('gridIndex', 'string')

    grid = Layergrid(inshp.layer, 10, 5, Type='tilenumbers') # Creates a grid layer, steps in map units (e.g. decimal degrees)
    print(grid.getsrs()) #Layergrid inherits srs from input shapefile
    gridcol = grid.getgrid() #get list of polygons from grid
    for t in range(0,len(gridcol)):
        geom = gridcol[t]
        feat = outshp.createfeatgeom(geom) # creates and return new feature
        outshp.createfeature(feat)
        gridindex = grid.gridindex[t] #get autogenerated index for grid tile
        outshp.setfield(feat, 'gridIndex', gridindex) #set attribute value for giving feature


def example04():
    inputshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outputshape = os.path.join(examplespath, 'example04.shp')
    inshp = Setsource(inputshape, Action='open r')
    inshp.getlayer(0)
    outshp = Setsource(outputshape, Action='create')
    outshp.createlayer('layer1', inshp.srs, Type='polygon')
    outshp.getlayer('layer1')
    inlayer = inshp.layer
    grid = Layergrid(inlayer, 10, 5, Type='mapunits')
    gridcol = grid.getgrid()  # get list of polygons from grid
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    for t in range(0, len(gridcol)):
        clipfeatures = layerclip(inlayer, gridcol[t])
        for feature in clipfeatures:
            outshp.createfeature(feature)


def example05():
    inshape = os.path.join(examplespath, 'TM_WORLD_BORDERS_SIMPL-0.3.shp')
    outshape = os.path.join(examplespath, 'example05.shp')
    inshp = Setsource(inshape, Action='open r')
    inshp.getlayer(0)
    outshp = Setsource('mymemlayer', Action='memory')
    outshp.createlayer('layer1', inshp.srs, Type='Polygon')
    outshp.getlayer('layer1')
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    fi = inshp.iterfeatures()   # Wraps OGR '.GetNextFeature()' iterator, updating all related class attributes
                                # each iteration. Returns feature each iteration
    for feature in fi:
        featset = splitvertices(feature, 50)  # Same as passing '.feature' class attribute
        for each in featset:
            outshp.createfeature(each)
    outshp.savefile(outshape)


def example06():
    inshape = os.path.join(examplespath, 'rings.shp')
    outshape = os.path.join(examplespath, 'example06.shp')
    inshp = Setsource(inshape, Action='open r')
    inshp.getlayer(0)
    outshp = Setsource('mymemlayer', Action='memory')
    outshp.createlayer('layer1', inshp.srs, Type='Polygon')
    outshp.getlayer('layer1')
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    for t in range(0, inshp.featurecount()):
        inshp.getfeature(t)
        featset = splitrings(inshp.feature)
        for each in featset:
            featset2 = splitvertices(each, 50)
            for f in featset2:
                outshp.createfeature(f)
    outshp.savefile(outshape)


def example07():
    filepath = os.path.join(examplespath, 'examplekmz.kmz')
    kmzset = Setsource(filepath, Action='open r')
    for g in range(0, kmzset.layercount()):
        kmzset.getlayer(g)
        attrbt = kmzset.getattrtable()
        print(attrbt)
        fi = kmzset.iterfeatures()
        for feat in fi:
            ff = kmzset.getfield('Name')
            print(ff)
            print(kmzset.geom)


def example08():
    input = os.path.join(examplespath, 'example02.shp')
    dest = Setsource(input, Action='open r')

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
    work = Setsource(input, Action='open r')
    tempw = Setsource('tempsource', Action='memory')

    geomtypes = []
    for li in range(0, work.layercount()):
        work.getlayer(li)
        attrbt = work.getattrtable()
        fi = work.iterfeatures()
        for feature in fi:
            tg = work.geom
            gt = work.geomtypestr
            if gt not in geomtypes:
                geomtypes.append(gt)
                tempw.createlayer(gt, '4326', Type=gt)
                tempw.getlayer(gt)
                tempw.setattrtable(attrbt)
            layindex = geomtypes.index(gt)
            tempw.getlayer(layindex)
            tempw.createfeature(feature)
    tempw.savefile(output1)
    tempw.savefile(output2)


def example10():  # Export KMZ to multiple SHP files. KMZ contains mixed geometry types per 'layer'.
                # Separate geoms by type, create a separate SHP file for each type

    input = os.path.join(examplespath, 'examplekmz.kmz')
    output = os.path.join(examplespath, 'example10.shp')
    work = Setsource(input, Action='open r')

    geomtypes = []
    tempsources = []
    for li in range(0, work.layercount()):
        work.getlayer(li)
        attrbt = work.getattrtable()
        fi = work.iterfeatures()
        for tf in fi:
            tg = work.geom
            gt = work.geomtypestr
            if gt not in geomtypes:
                tempw = Setsource(gt, Action='memory')
                geomtypes.append(gt)
                tempw.createlayer(gt, '4326', Type=gt)
                tempw.getlayer(gt)
                tempw.setattrtable(attrbt)
                tempsources.append(tempw)
            sourceindex = geomtypes.index(gt)
            tw = tempsources[sourceindex]
            tw.getlayer(0)
            tw.createfeature(tf)

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
    out = Setsource(outkml, Action='create')
    out.createlayer('Folder', '4326', Type='Polygon')
    out.getlayer('Folder')
    style_table = ogr.StyleTable()
    style_table.AddStyle('CoCoNuT', 'PEN(c:#C81B75FF,w:5.0px);BRUSH(fc:#1d8aa8C8)')
    style_table.AddStyle('CoCoNuT2',
                         'SYMBOL(id:"http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",'
                         'c:#FFAA00FF,s:1.2);LABEL(c:#FFFF00FF)')
    style_table.SaveStyleTable(outstyletable)  # Optional
    out.datasource.SetStyleTable(style_table)

    out.createattr('Name', 'string')
    feature = out.createfeatgeom(pol2)
    out.setfield(feature, 'Name', 'Some Polygon')
    feature.SetStyleString('@CoCoNuT')
    out.createfeature(feature)

    feature2 = out.createfeatgeom(point2)
    out.setfield(feature2, 'Name', 'Some Point')
    feature2.SetStyleString('@CoCoNuT2')
    out.createfeature(feature2)

    outpdf = os.path.join(examplespath, 'example11.pdf')
    out.savefile(outpdf)


def example12():
    shpp = os.path.join(examplespath, 'example04.shp')
    shpout = os.path.join(examplespath, 'example12.shp')
    gpout = os.path.join(examplespath, 'example12.gpkg')
    shp = Setsource(shpp, Action='open r')
    print("Save to SHP and GPKG")
    shp.savefile(shpout)
    shp.savefile(gpout)

    nshp = Setsource(shpout, Action='open rw')
    npkg = Setsource(gpout, Action='open rw')

    dc = [npkg, nshp]
    for source in dc:
        source.getlayer(0)
        attr = source.getattrtable()
        print("Delete attributes ")
        # print("Delete attributes " + source.datasourcename)
        for field in attr:
            source.delattr(field[0])
        source.createattr('isDel', Type='integer')
        it = source.iterfeatures(Action='reset')
        ct = 0
        print("Set new attributes ")
        # print("Set new attributes " + source.datasourcename)
        for feat in it:
            if ct == 0:
                source.setfield(feat, 'isDel', 0)
                ct = 1
            else:
                source.setfield(feat, 'isDel', 1)
                ct = 0
        source.attributefilter('isDel = 1')
        it = source.iterfeatures(Action='reset')  # iterate again now filtered
        print("Delete features ")
        # print("Delete features " + source.datasourcename)
        for feat in it:
            source.delfeature(feat)


def example30():
    conn = Setsource(connstr, Action='open rw')
    sql = conn.datasource.ExecuteSQL('SELECT * FROM pg_extension')
    exts = []
    for tb in sql:
        exts.append(tb.GetField(1).upper())
    if 'POSTGIS' not in exts:
        print("Enable PostGIS extensions")
        conn.datasource.ExecuteSQL('CREATE EXTENSION postgis')
        conn.datasource.ExecuteSQL('CREATE EXTENSION postgis_topology')


def example31():
    conn = Setsource(connstr, Action='open rw')
    conn.createlayer('randompols', '4326', Type='Polygon')
    conn.createlayer('randompols2', '4326', Type='Polygon')
    conn.getlayer('randompols')
    conn.createattr('Name', 'string')
    conn.createattr('NIindex', 'integer')
    conn.getlayer('randompols2')
    conn.createattr('Name', 'string')
    conn.createattr('NIindex', 'integer')
    ct = 0
    cc = 0
    for t in range(0, 1000):
        print("Create: " + str(ct))
        ct += 1
        if cc == 0:  # Slow switching
            conn.getlayer('randompols')
            cc = 1
        else:
            conn.getlayer('randompols2')
            cc = 0
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        feat = conn.createfeatgeom(geom)  # creates and return new feature
        conn.setfield(feat, 'Name', 'NI-' + str(t).zfill(6))
        conn.setfield(feat, 'NIindex', t)
        conn.createfeature(feat)


def example32():
    conn = Setsource(connstr, Action='open rw')
    conn.getlayer('randompols')
    s1 = time.time()
    politer = conn.iterfeatures(Action='reset')  # '.ResetReading()' is passed to layer when "Action='reset'"
    ct = 0
    for feature in politer:  # Same effect as iterating with native OGR '.GetNextFeature()'. That's
        # external changes (e.g. featurer delete) on layer's features will not be accounted while iterating (see testing
        # conditions at the end of this file)
        # but just after a '.ResetReading()' is issued on layer (or Action='reset')
        print(ct)
        print(conn.geomtypestr)
        ct += 1

    s2 = time.time()

    # Do it again no prints overhead
    politer = conn.iterfeatures(Action='reset')
    for feature in politer:
        gt = conn.geomtypestr

    s3 = time.time()

    print("Exec time 1-> " + str(round((s2 - s1), 2)))
    print("Exec time 2-> " + str(round((s3 - s2), 2)))


def example33():
    conn = Setsource(connstr, Action='open rw')
    conn.getlayer('randompols')
    conn.createattr('isEven', 'integer')
    conn.createattr('circleOfFID', 'integer')
    conn.createattr('conferfid', 'integer')
    conn.createattr('geomVcount', 'string')
    ct = 0
    it = conn.iterfeatures(Action='reset')
    for feature in it:
        FID = getfid(feature)
        conn.setfield(feature, 'conferfid', FID)
        centroidpoint = conn.geom.Centroid()
        if (FID % 2) == 0:
            adds = [1, 10]
        else:
            adds = [0, 1]
        conn.setfield(feature, 'isEven', adds[0])
        crcgeom = makecircle(centroidpoint, 0.09, adds[1])
        nfeat = conn.createfeatgeom(crcgeom)
        conn.createfeature(nfeat)
        conn.setfield(nfeat, 'Name', 'Centroid')
        conn.setfield(nfeat,'circleOfFID', FID)
        verticecount = geomptcount(crcgeom)
        conn.setfield(nfeat, 'geomVcount', 'Polygon has ' + str(verticecount) + ' vertices')
        print("Processing: " + str(ct))
        ct += 1

def example34():
    gpinp = os.path.join(examplespath, 'example09.gpkg')
    gpin = Setsource(gpinp, Action='open r')
    gpin.savefile(connstr)

    shpip = os.path.join(examplespath, 'example12.shp')
    shpi = Setsource(shpip, Action='open r')
    shpi.savefile(connstr)



if __name__ == "__main__":
    main()

# Test conditions for '.GetNextFeature()' reported in example14():
# Postgis server on virtual LAN (VM same computer). In example14() Consider adding the following condition on iterator:
#     for feature in politer:
#         print(ct)
#         print(conn.geomtypestr)
#         if conn.FID == 51
#                input("STOP1")
#         if conn.FID == 100
#                input("STOP2")
#         ct += 1
# While waiting 'STOP1' feature FID == 100 was deleted acessing the DB in QGIS and saved.
# After pressing ENTER the loop stops again at 'STOP2'
# Class Setsource '.iterfeatures()' makes direct calls to OGR '.GetNextFeature()'