After initial excitement about GDAL python bindings possibilities I realized something was wrong, as my code could not work as expected. Fortunately checked that there’s anything wrong about it but [Python Gotchas](https://gdal.org/api/python_gotchas.html)  
Summing-up: Python gdal/ogr objects are pointers to [SWIG](https://www.swig.org/) objects and these pointers will be collected by Python's garbage collector earlier than expected in code execution. In practice the problem is it makes writing code tied to a very monolithic approach.  
After trying alternatives to make it more usable for Python I eventually found a way that's working until now: keeping theses pointers busy, allocated. In this case this is done by having key elements (datasources e.g.) 'grabbed' by class objects.  
This repository is Beta/under construction and contains some basic features and some processing tools. For now I will use it to keep adding functionality and helper functions for my recurring tasks while working with shapefiles.  
Usage can be checked in the [examples.py](https://github.com/Rodrigo-NH/gdalwrap/blob/main/src/examples.py) file  
[Recipe](https://gist.github.com/Rodrigo-NH/7b9cbb9ea45edc13fc3f6606417d10ee) to get all gdal/gdal bindings parts installed and configured in Windows
## Classes/commands
## Setsource:
Used to open/create shapefiles or memory datasets and set/get data (attributes, geometries, srs etc). 
  
**Class Setsource:**  

```Setsource(<shapefile>, <srs>, [Action={'open r'}], [Type={'polygon'}])```  

```shapefile: path to shapefile```  

```srs: SRS for the dataset in either OpenGIS Well Known Text format or EPSG code```  

```Action= 'open r', 'open rw', 'create', 'memory'```  
 
*Methods:*  

```.layer()``` -> Get OGR layer

```.getsrs()``` -> Get SRS in OpenGIS Well Known Text format

```.getattrtable()``` -> Get attribute table in list format [['fieldname', 'fieldtype'], ... ]  

```.setattrtable(<fields>)``` -> Create attribute table from list  

```.getfeature(<FID>)``` -> Get feature OGR object by FID  

```.createfeature(<feature>)``` -> Insert/record feature to dataset  

```.savefile(<path>)``` -> Save memory dataset to shapefile  

```.getgeom()``` -> Get current geometry  

```.featurecount()``` -> Return the number of features

```.createattr(<name>, <type>)``` -> Create a new attribute table entry  

```.geom2feature(<geom>)``` -> Create a new feature and insert a geom (optionally returns the newly created feature)  

```.setfield(<attribute>, <value>)``` -> Change/set attribute value of current feature  

**Method makepol:**  


```makepol(<[[x1,y1],[x1,y2]...]>)``` -> Returns polygon geom from a list of coordinates

**Method layerclip:**

Clips features in a layer and returns resulting feature list. Replicates attribute table values. Doesn't change input layer.  

```layerclip(<layer>, <clipgeom>)``` -> Returns list of output features


**Class Layergrid:**   

Creates a grid with total extent of a given layer. X and Y steps in current map units. Inherits srs from layer. User inputs 'Xstep' and 'Ystep' will be adjusted (changed) to match layer's extent exactly.

```Layergrid(<layer>, <Xstep>, <Ystep>)```  

*Methods:*  

```.getgrid()``` -> Get a list with all grid geoms   


```.gridindex()``` -> Get a STR list with grid index in the format "xi_yi"  

```.getsrs()``` -> Get grid's associated SRS

**Method splitrings:**  

Removes rings from feature but keeping overall aspect (a polygon with one ring will be transformed to two polygons respecting the empty space of the ring). Returns a list of features. replicates source attributes.  

```splitrings(<feature>)``` -> Returns a list of resulting features

![N|Solid](https://github.com/Rodrigo-NH/assets/blob/main/img/removerings.png)  

**Method splitvertices:** 

Split polygons features based on max number of vertices threshold.  

```splitvertices(<feature>, <threshold>)``` -> Returns a list of resulting features
