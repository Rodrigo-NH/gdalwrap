from random import random
from gdalwrap import Setsource
from gdalwrap import makepol
from gdalwrap import Layergrid
from gdalwrap import layerclip
from gdalwrap import splitvertices
from gdalwrap import splitrings

def main():
    # shapefile used in the examples: https://thematicmapping.org/downloads/TM_WORLD_BORDERS_SIMPL-0.3.zip
    # other shapefile used in the examples: https://github.com/Rodrigo-NH/assets/blob/main/files/rings.zip
    # Pick your example:
    example01() #Iterate over shapefile attributes and geoms
    example02() #Create memory shapefile, populate with random polygons, get/set/change attributes
    example03() #Layergrid grid generator function example
    example04() #layerclip function
    example05() #splitvertices function
    example06() #splitrings + splitvertices function

def example01():
    inputshape = r'D:\shapes\TM_WORLD_BORDERS_SIMPL-0.3.shp'
    inshp = Setsource(inputshape, '', Action='open r')
    fields = inshp.getattrtable()
    print(fields)
    for t in range(0, inshp.featurecount()):
        feature = inshp.getfeature(t) #return OGR feature and set current objects for the other methods (.getgeom() e.g.)
        geom = inshp.getgeom()
        FID = feature.GetFID()
        print(str(t) + " = " + str(FID))
        print("Field: " + fields[4][0] + ' --> ' + str(feature.GetField(fields[4][0])))
        print(geom)

def example02():
    outshp = Setsource('myMemLayer', '4326', Action='memory', Type='polygon')
    outshp.createattr('NIname', 'string')  # Create attribute field
    outshp.createattr('NIindex', 'integer')
    for t in range(0, 10):
        randompol = [[random(), -abs(random())], [random(), random()],
                     [-abs(random()), random()], [-abs(random()), -abs(random())]]
        geom = makepol(randompol)
        outshp.geom2feature(geom)  #creates new feature and record geom (returns the feature to a variable, optionally)
        outshp.setfield('NIname', 'NI-' + str(t))
        outshp.setfield('NIindex', t)

    filepath = r'D:\shapes\example02.shp'
    outshp.savefile(filepath)  # Save from memory to file

    rework = Setsource(filepath, '', Action='open rw')  # Open recently created shape in RW mode
    print(rework.getsrs())  # Prints shape SRS OpenGIS Well Known Text format
    print(rework.featurecount())  # Prints number of features in the shape
    rework.getfeature(5)  # Get feature FID=5 (and makes it the current feature),
                            # returns the feature to a variable, optionally
    rework.setfield('NIname', 'NotInterested')  # Change current selected feature attr field

def example03():
    inputshape = r'D:\shapes\TM_WORLD_BORDERS_SIMPL-0.3.shp'
    outputshape = r'D:\shapes\example03.shp'
    inshp = Setsource(inputshape, '', Action='open r')
    outshp = Setsource(outputshape, inshp.getsrs(), Action='create', Type='polygon')
    outshp.createattr('gridIndex', 'string')

    grid = Layergrid(inshp.layer(), 2, 2) # Creates a grid layer, steps in map units (e.g. decimal degrees)
    print(grid.getsrs()) #Layergrid inherits srs from input shapefile
    gridcol = grid.getgrid() #get list of polygons from grid
    for t in range(0,len(gridcol)):
        geom = gridcol[t]
        outshp.geom2feature(geom) #record feature (returns the feature to a variable, optionally)
        gridindex = grid.gridindex[t] #get autogenerated index for grid tile
        outshp.setfield('gridIndex', gridindex) #set attribute value for current, working feature

def example04():
    inputshape = r'D:\shapes\TM_WORLD_BORDERS_SIMPL-0.3.shp'
    outputshape = r'D:\shapes\example04.shp'
    inshp = Setsource(inputshape, '', Action='open r')
    outshp = Setsource(outputshape, inshp.getsrs(), Action='create', Type='polygon')
    inlayer = inshp.layer()
    grid = Layergrid(inlayer, 10, 10)
    gridcol = grid.getgrid()  # get list of polygons from grid
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    for t in range(0, len(gridcol)):
        clipfeatures = layerclip(inlayer, gridcol[t])
        for feature in clipfeatures:
            outshp.createfeature(feature)

def example05():
    inshape = r'D:\shapes\TM_WORLD_BORDERS_SIMPL-0.3.shp'
    outshape = r'D:\shapes\example05.shp'
    inshp = Setsource(inshape, '', Action='open r')
    outshp = Setsource('mymemlayer', inshp.getsrs(), Action='memory')
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    for t in range(0, inshp.featurecount()):
        featset = splitvertices(inshp.getfeature(t), 50)
        for each in featset:
            outshp.createfeature(each)
    outshp.savefile(outshape)

def example06():
    inshape = r'D:\shapes\rings.shp'
    outshape = r'D:\shapes\example06.shp'
    inshp = Setsource(inshape, '', Action='open r')
    outshp = Setsource('mymemlayer', inshp.getsrs(), Action='memory')
    fields = inshp.getattrtable()
    outshp.setattrtable(fields)
    for t in range(0, inshp.featurecount()):
        featset = splitrings(inshp.getfeature(t))
        for each in featset:
            featset2 = splitvertices(each, 50)
            for f in featset2:
                outshp.createfeature(f)
    outshp.savefile(outshape)

if __name__ == "__main__":
    main()