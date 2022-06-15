# ESRI shapefile to IMG for Garmin GPS

This script will convert ESRI shapefiles to IMG format Garmin maps. Uses external map processors (cgsmapper or MapTk).
## Requisites
You will need Gdal python bindings installed. Change script Gdal path accordingly (e.g. 'sys.path.append(r'C:\OSGeo4W\apps\Python39\Lib\site-packages)'
## Usage
'python SHPtoIMG.py shapefilepath [MapsetName]'
- It will use shapefile archive name as mapset name If [MapsetName] is ommited.
- If shapefilepath is a directory instead of a .shp file, script will convert all .shp files to individual IMG files and then join then in a single IMG suffixed with "_JOIN.img"
## Labelling and styling
If not specified, vectors will use the styles defined in script's 'lineType', 'pointType' and 'polygonType' variables. Styling and labelling can be imported from shapefile attributes table as follow: 
- It will import styles for each feature from attribute field 'Ftype' (Text field)
- It will import labels for each feature from attribute field 'Glabel'
## Zoom levels
At the present moment script creates a fixed set of zoom levels (from 24 to 18), you can tweak that manually if you want. 
- If not specified, each feature will be tagged to show in all levels.
- It will import zoom level for each feature from attribute field 'zoomL' (Text field) following the rules: If it's a plain number (e.g. "4") it will tag the particular feature to show only on that level. If it's prefixed with the letter "n" (e.g. "n4") it will tag the feature for all levels until defined level (from 0 to 4 in this example)
## MP files
Script will not overwrite existing matching '.mp' files already present in the directory. You need to delete them manually if you want to reprocess the MP files. This is usefull as script will compile the IMG files without considering the shapefiles. For example if you need to make adjustments to MP files you can simply run the script again after changing the files.
## Map processors support
Support for available free map processors aren't great, unfortunately. There's basically two options: cgsmapper and MapTK. cgsmapper is not maintained anymore and the official page doesn't exist anymore, it's possible to download the last version though from the internet. MapTk looks great, does a good job and software is active (last version from 2021), but lacks a reliable webpage. The official webpage is http://maptk.dnsalias.com/ (self hosted) and not UP all the time.

Cgsmapper page I tested and used to get cgsmapper: https://www.gpsfiledepot.com/tools/cgpsmapper.php
