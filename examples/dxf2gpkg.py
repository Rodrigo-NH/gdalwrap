from gdalwrap import *
import time

def main():
    inputdxf = r'D:\shapes\testing.dxf'  # Tested AutoCAD 2000/LT2000 DXF file
    outputgpkg = r'D:\shapes\testing.gpkg'
    declaredSRS = '31983'  # Inform the 'declared' SRS for the DXF file
    s1 = time.time()
    work = Setsource(inputdxf, Action='open r')
    tempw = Setsource('tempsource', Action='memory')
    geomtypes = []
    for li in range(0, work.layercount()):
        work.getlayer(li)
        attrbt = work.getattrtable()
        ct = 0
        it = work.iterfeatures(Action='reset')
        for feature in it:
            gt = work.geomtypestr
            if gt not in geomtypes:
                geomtypes.append(gt)
                tempw.createlayer(gt, declaredSRS, Type=gt)
                tempw.getlayer(gt)
                tempw.setattrtable(attrbt)
            layindex = geomtypes.index(gt)
            tempw.getlayer(layindex)
            tempw.createfeature(feature)
            ct += 1
            print("Processing feature: " + str(ct))
    tempw.savefile(outputgpkg)
    s2 = time.time()
    print("Exec time 1-> " + str(round((s2 - s1), 2)))

if __name__ == "__main__":
    main()