from gdalwrap import *

def main():
    inputdxf = r'D:\shapes\testing.dxf'  # Tested AutoCAD 2000/LT2000 DXF file
    outputgpkg = r'D:\shapes\testing.gpkg'
    declaredSRS = '31983'  # Inform the 'declared' SRS for the DXF file

    work = Setsource(inputdxf, Action='open r')
    tempw = Setsource('tempsource', Action='memory')
    geomtypes = []
    for li in range(0, work.layercount()):
        work.getlayer(li)
        attrbt = work.getattrtable()
        ct = 0
        fi = work.iterfeatures()
        for feature in fi:
            gt = work.geomtypestr
            if gt not in geomtypes:
                geomtypes.append(gt)
                tempw.createlayer(gt, declaredSRS, Type=gt)
                tempw.setattrtable(attrbt)
            layindex = geomtypes.index(gt)
            tempw.getlayer(layindex)
            tempw.createfeature(feature)
            ct += 1
            print("Processing feature: " + str(ct))
    tempw.savefile(outputgpkg)


if __name__ == "__main__":
    main()