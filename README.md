After initial excitement about GDAL python bindings possibilities I realized something was wrong, as my code could not work as expected. Fortunately checked that there’s anything wrong about it but [Python Gotchas](https://gdal.org/api/python_gotchas.html)  
Summing-up: Python gdal/ogr objects are pointers to [SWIG](https://www.swig.org/) objects and these pointers will be collected by Python's garbage collector earlier than expected in code execution. In practice the problem is it makes writing code tied to a very monolithic approach.  
After trying alternatives to make it more usable for Python I eventually found a way that's working until now: keeping these pointers busy, allocated. In this case this is done by having key elements (datasources e.g.) 'grabbed' by class objects.  
This repository is Beta/under construction and contains some basic features and some processing tools. I will use it to keep adding functionality and helper functions for my recurring tasks while working with GIS files.  
Usage can be checked in the [examples.py](https://github.com/Rodrigo-NH/gdalwrap/blob/main/examples/examples.py) file  
[Recipe](https://gist.github.com/Rodrigo-NH/94d1fe07646052ad32133824c85b4221) to get all gdal/gdal bindings parts installed and configured in Windows  

## Installation  
pip install --user gdalwrap
## Classes/commands
Core commands (file core.py)  

The gdalwrap idea is to wrap OGR classes into Python classes, circumventing some of the Python gotchas. Respecting OGR higther classes hierarchy (datasource/layers/features/geometries) while permitting easy access to native OGR objects. Considering python is 'just' making reference to OGR object pointers, it's possible to work directly with the OGR objects (using the bindings directly) without breaking the code logic constructed with gdalwrap.  

Example:  

```python
temps = Datasource(geopackagepath, Action="open rw")  # Open a file
print(temps.datasource)  # Native OGR datasource object
newlayer = temps.Newlayer('polygons_1', '4326', Type='polygon')  # Create a new layer
existinglayer = temps.getlayer('somelayer')  # Pick some existing layer
print(newlayer.layer)  # Native OGR layer object
print(existinglayer.layer)  # Native OGR layer object
somefeature = existinglayer.getfeature(0)  # Random access by FID
print(somefeature.feature)  # Native OGR feature object

iter = existinglayer.iterfeatures()  # Feature iterator (wraps OGR '.GetNextFeature())'
for feature in iter:
	fg = feature.getgeom()
	print(fg.geom)  # Native OGR geometry object
```
You can check the examples.py for usage until a better README arises.


## Tools
Some useful tools. (file tools.py)


**Method splithalf:**  


```splithalf(<geom>)``` -> Split geom in half and returns a list with resulting geoms


**Method layerclip:**

Clips features in a layer and returns resulting feature list. Replicates attribute table values. Doesn't change input layer.  

```layerclip(<layer>, <clipgeom>)``` -> Returns list of output features  

layer -> The input layer to be clipped  

clipgeom -> The geom used as clip mask


**Class Layergrid:**   

Creates a grid with the total extent of a given layer. X and Y steps in current map units or total number of tiles. Inherits srs from layer. User inputs 'Xstep' and 'Ystep' will be adjusted (changed) to match layer's extent exactly.

```Layergrid(<layer>, <Xstep>, <Ystep>, [Type='mapunits'])```  

Type=  
'mapunits' -> Default. Xstep and Ytep in map units  
'tilenumbers' -> Xstep and Ytep as total number of tiles (e.g. Xstep=4, Ystep=4 for a 16 tiles grid)

*Methods:*  

```.getgrid()``` -> Get a list with all grid geoms   


```.gridindex()``` -> Get a string list with grid index in the format "xi_yi"  

```.getsrs()``` -> Get grid's associated SRS

**Method splitrings:**  

Removes rings from feature but keeping overall aspect (a polygon with one ring will be transformed to two polygons respecting the empty space of the ring). Returns a list of features. replicates source attributes.  

```splitrings(<feature>)``` -> Returns a list of resulting features

![N|Solid](https://github.com/Rodrigo-NH/assets/blob/main/img/removerings.png)  

**Method splitvertices:** 

Split features based on max number of vertices threshold.  

```splitvertices(<feature>, <threshold>)``` -> Returns a list of resulting features  

 
