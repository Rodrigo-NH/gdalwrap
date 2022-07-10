After initial excitement about GDAL python bindings possibilities I realized something was wrong, as my code could not work as expected. Fortunately checked that there’s anything wrong about it but [Python Gotchas](https://gdal.org/api/python_gotchas.html)  
Summing-up: Python gdal/ogr objects are pointers to [SWIG](https://www.swig.org/) objects and these pointers will be collected by Python's garbage collector earlier than expected in code execution. In practice the problem is it makes writing code tied to a very monolithic approach.  
After trying alternatives to make it more usable for Python I eventually found a way that's working until now: keeping these pointers busy, allocated. In this case this is done by having key elements (datasources e.g.) 'grabbed' by class objects.  
This repository is Beta/under construction and contains some basic features and some processing tools. For now I will use it to keep adding functionality and helper functions for my recurring tasks while working with shapefiles.  
Usage can be checked in the [examples.py](https://github.com/Rodrigo-NH/gdalwrap/blob/main/examples/examples.py) file  
[Recipe](https://gist.github.com/Rodrigo-NH/7b9cbb9ea45edc13fc3f6606417d10ee) to get all gdal/gdal bindings parts installed and configured in Windows
## Installation  
pip install --user gdalwrap
## Classes/commands
Core commands (file core.py)
## Setsource:
Used to open/create shapefiles or memory datasets and set/get data (attributes, geometries, srs etc). Native OGR objects can be accessed through class attributes so you can use these directly. These attributes are updated under appropriated conditions. For example opening a shapefile will set many of the attributes, selecting a feature will update access to ‘.geom’ attribute (with the geom associated with the selected feature). (actually using 'osrs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)')
  
**Class Setsource:** 

```Setsource(<shapefile>, <srs>, [Action={'open r'}], [Type={'polygon'}])```  

```shapefile: path to shapefile```  

```srs: SRS for the dataset in either OpenGIS Well Known Text format or EPSG code```  

```Action= 'open r', 'open rw', 'create', 'memory'```  
 
 *Attributes:*  
 
 The following class attributes are set after class object creation
 
```.shapepath``` -> Full path of shapefile  

```.datasource``` -> OGR datasource  

```.layer``` -> OGR layer  

```.layerdef``` -> OGR layer definition  

```.layertype``` -> OGR layer  type (int)  

```.layertypestr``` -> OGR layer type (string)  

```.srs``` -> SRS (OpenGIS Well Known Text format)


The following class attributes are set accordingly specific conditions  

```.feature``` -> OGR current feature. Set after '.getfeature()' method
  

```.geom``` -> OGR current  geom. Also set after '.getfeature()' method  

```.fid``` -> Current FID number. Also set after '.getfeature()' method

*Methods:*  


```.getattrtable()``` -> Get attribute table in list format [['fieldname', 'fieldtype'], ... ]  


```.getlyrextent()``` -> Returns layer extent in a list (in map units)

```.setattrtable(<fields>)``` -> Create attribute table from list  

```.getfeature(<FID>)``` -> Get and return feature OGR object by FID. Calling this method will update '.geom', '.feature' and '.fid' class attributes.

```.createfeature(<feature>)``` -> Insert/record feature to dataset. Calling this method will update '.geom', '.feature' and '.fid' class attributes.

```.savefile(<path>)``` -> Save memory dataset to disk (shapefile)  


```.featurecount()``` -> Return the number of features

```.createattr(<name>, <type>)``` -> Create a new attribute table entry  

```.geom2feature(<geom>)``` -> Create a new feature and insert a geom (returns the newly created OGR feature). Calling this method will update '.geom', '.feature' and '.fid' class attributes.  

```.setfield(<attribute>, <value>)``` -> Change/set attribute value of current feature. (e.g. actual feature after .getfeature() or .createfeature() or .geom2feature())

**Class Transformation:**  

For transformations. (reprojections etc). Takes input in either OpenGIS Well Known Text format or string with EPSG code. [Example](https://github.com/Rodrigo-NH/gdalwrap/blob/main/examples/batchclip.py)

```Transformation(<sourceproj>, <destproj>)```  

sourceproj -> The source projection  

destproj -> The destination projection


*Methods:*  

```.transform(<geom>)``` -> Apply transformation to a give geom and returns the resulting geom. Important: It does not transform the original geom.

**General methods:**  

```getfeatgeom(<feature>)``` -> Returns  OGR geom for any given OGR feature  

```geomptcount(<geom>)``` -> Returns total number of points/vertices of a given geometry  

```multi2list(<geom>)``` -> Return a list of individual geometries from multigeometry (multipolygon, multiline, etc)  

```splithalf(<geom>)``` -> Split geom in half and returns a list with resulting geoms  

```makepol(<[[x1,y1],[x1,y2]...]>)``` -> Returns polygon geom from a list of coordinates. (No need to repeat first coordinate)


## Tools
Tools, utils and helper functions. (file tools.py)


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

Split polygons features based on max number of vertices threshold.  

```splitvertices(<feature>, <threshold>)``` -> Returns a list of resulting features  

 
