import sys, random, os, pathlib
from subprocess import Popen, PIPE, STDOUT
from os import walk
import json
sys.path.append(r'C:\OSGeo4W\apps\Python39\Lib\site-packages')
from osgeo import osr, ogr

lineType = '0x0004'
pointType = '0x0700'
polygonType = '0x0028'
simplify = True # map processors generalization are not goot, better to simplify before sending to processor. Set this
                # value True to simplify geometries before map processor

mapEngine = r'D:\MapEngine\MapTk\MapTk.exe' # cgpsmapper or MapTk executable
gmtPath = r'D:\MapEngine\gmt.exe' # Gmaptool executable http://www.gmaptool.eu/en/content/gmaptool

def main():
    shapefiles = []
    if os.path.isfile(sys.argv[1]):
        DIR_PATH = str(pathlib.Path(sys.argv[1]).parent.absolute())
        shapefiles.append(sys.argv[1].split(str(DIR_PATH)+'\\')[1].split('.')[0])
    if os.path.isdir(sys.argv[1]):
        DIR_PATH = sys.argv[1]
        files = []
        for (dirpath, dirnames, filenames) in walk(sys.argv[1]):
            files.extend(filenames)
            break
        for each in files:
            sp = each.split('.')
            if sp[1].upper() == 'SHP' and len(sp) == 2:
                shapefiles.append(sp[0])
    for each in shapefiles:
        setmapname = False
        if len(shapefiles) == 1 and len(sys.argv) > 2:
            setmapname = True
        procshape(each, DIR_PATH, setmapname)

    if len(shapefiles) > 1:
        img = ''
        MAPSETNAME = shapefiles[0] + '_JOIN'
        for each in shapefiles:
            img = img + DIR_PATH + '\\' + each + '.img '
        try:
            if sys.argv[2]:
                MAPSETNAME = sys.argv[2]
        except: pass

        command = gmtPath + ' -j -m ' + '"' + MAPSETNAME + '"' + ' -o ' + \
                  DIR_PATH + '\\' + MAPSETNAME + '.img ' + img
        mapper = os.popen(command).read().splitlines()
        print(mapper)

def procshape(shapefile, DIR_PATH, setmapname):
    if not os.path.isfile(DIR_PATH + '\\' + shapefile + '.mp'):
        hd = header()
        MAPid = str(random.randrange(10000000, 99999999))
        hd[3] = 'ID=' + MAPid + '\n'
        if setmapname:
            hd[4] = 'Name=' + sys.argv[2] + '\n'
        else:
            hd[4] = 'Name=' + shapefile + '\n'
        MP = open(DIR_PATH + '\\' + shapefile + '.mp', 'w', encoding='latin2')
        for line in hd:
            MP.write(line)
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(DIR_PATH +'\\'+shapefile + '.shp', 1)
        layer = dataSource.GetLayer()
        sourceprj = layer.GetSpatialRef()
        targetprj = osr.SpatialReference()
        targetprj.ImportFromEPSG(4326)
        transform = osr.CoordinateTransformation(sourceprj, targetprj)
        for feat in layer:
            geometry = feat.GetGeometryRef()
            geometry.Transform(transform)
            geom = feat.geometry()
            if simplify:
                geom = geom.Simplify(0.000003)
            dd = geom.ExportToJson()
            jsondt = json.loads(dd)
            ftype = ftypes(jsondt['type'])[0]
            ftypef = ftypes(jsondt['type'])[1]
            customlabel = ';Label='
            customzoom = '\nEndLevel=5' + '\nData0='
            try:
                customzoomf = feat.GetField('zoomL')
                if customzoomf:
                    if 'n' in customzoomf:
                        lv = customzoomf.split('n')[1]
                        customzoom = '\nEndLevel=' + lv + '\nData0='
                    else:
                        customzoom = '\nData' + customzoomf + '='
            except: pass
            try:
                getftypef = feat.GetField('Ftype')
                if getftypef:
                    ftypef = getftypef
            except: pass
            try:
                getcustomlabel = "Label="+feat.GetField('Glabel')
                if getcustomlabel:
                    customlabel = getcustomlabel
            except: pass

            coorddata = jsondt['coordinates']
            if ftype == '[POLYGON]':
                coorddata = coorddata[0][:-1]
            if ftype == '[POI]':
                coordinner = []
                coordinner.append(coorddata)
                coorddata = coordinner
            datapart = ftype + '\nType=' + ftypef + '\n' + customlabel + customzoom
            coordline = ''
            for each in coorddata:
                x = str(each[0])
                y = str(each[1])
                coordline = coordline + '(' + y + ',' + x +'),'
            datapart = datapart + coordline[:-1] + '\n[END]\n\n'
            MP.write(datapart)
        MP.close()

    me = mapEngine.split('\\')[-1].split('.')[0].upper()
    if me == 'MAPTK':
        ci = ' '
    if me == 'CGPSMAPPER':
        ci = ' -o '

    command = mapEngine + ' ' + DIR_PATH + '\\' + shapefile + '.mp' + ci + DIR_PATH + '\\' + shapefile + '.img'
    print("Processing: " + shapefile + '.shp')
    mapper = Popen(command, stdout = PIPE, stderr = STDOUT, shell = True)
    for line in mapper.stdout:
        print(line.decode('ansi').strip('\n'))

def header():
    hd = [
        '[IMG ID]\n',
        'CodePage=1252\n',
        'LblCoding=9\n',
        'ID=?',
        'Name=?\n',
        'Preprocess=F\n',
        'TreSize=700\n',
        'TreMargin=0.00000\n',
        'RgnLimit=127\n',
        'Transparent=S\n',
        'POIIndex=Y\n',
        'Levels=7\n',
        'Level0=24\n',
        'Level1=23\n',
        'Level2=22\n',
        'Level3=21\n',
        'Level4=20\n',
        'Level5=19\n',
        'Level6=18\n',
        'Zoom0=0\n',
        'Zoom1=1\n',
        'Zoom2=2\n',
        'Zoom3=3\n',
        'Zoom4=4\n',
        'Zoom5=5\n',
        'Zoom6=6\n',
        '[END-IMG ID]\n'
    ]
    return hd

def ftypes(type):
    typeo = []
    if type == 'LineString':
        typeo.append('[POLYLINE]')
        typeo.append(lineType)
    elif type == 'Polygon':
        typeo.append('[POLYGON]')
        typeo.append(polygonType)
    elif type == 'Point':
        typeo.append('[POI]')
        typeo.append(pointType)
    return typeo

if __name__ == "__main__":
        main()