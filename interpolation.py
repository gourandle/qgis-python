import math
import os
import sys
import numpy as np
import requests
import datetime
from qgis.core import *
from qgis.analysis import *
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QRectF

# create layer object from input csv
def create_rainfall_layer():
    uri = "file:///{}?type=csv&detectTypes=yes&xField={}&yField={}&crs=EPSG:{}&spatialIndex=no&subsetIndex=no&watchFile=no".format(INPUT_RAINFALL_CSV_PATH.replace('\\','/'), XFIELD, YFIELD, PROJECT_EPSG)

    layer = QgsVectorLayer(uri, 'Prediction', 'delimitedtext')

    if not layer.isValid():
        print("Could not create a valid layer from {}\nThe most common reason for this is an incorrectly set qgis prefix path. Please check this value and try again!")
        sys.exit(1)
    return layer

def project_bounding_box(inEPGS, outEPSG, bbox):
    crsDest = QgsCoordinateReferenceSystem(outEPSG)
    crsSrc = QgsCoordinateReferenceSystem(inEPGS)
    xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())

    return xform.transformBoundingBox(bbox)


# run IDW interpolation using rainfall points
def run_interpolation(rainfall_layer_utm, interpolation_data_field_index, boundary_layers):

    # do the interpolation - this outputs a .asc raster to file in UTM proj
    layer_data.interpolationAttribute =interpolation_data_field_index
    layer_data.sourceType = 0
    layer_data.zCoordInterpolation = False
    layer_data = QgsInterpolator.LayerData()
    layer_data.source = rainfall_layer_utm
    idw_interpolator = QgsIDWInterpolator([layer_data])
    export_path = os.path.join(TEMP_FOLDER, 'rainfall_layer_utm_interpolation.asc')

    if os.path.exists(export_path):
        try:
            os.remove(export_path)
        except:
            pass

    if INTERPOLATION_EXTENT_LAYER == 'boundary':


        first = True
        for lyr in boundary_layers:
            if first:
                extent = project_bounding_box(lyr.crs().authid(), rainfall_layer_utm.crs().authid(), lyr.extent())
                first = False
            else:
                extent.combineExtentWith(project_bounding_box(lyr.crs().authid(), rainfall_layer_utm.crs().authid(), lyr.extent()))
    else:
        extent = rainfall_layer_utm.extent()


    rect = extent.buffered(INTERPOLATION_PAD_DISTANCE)
    nrows = int( (rect.yMaximum() - rect.yMinimum() ) / RESOLUTION)
    ncol = int((rect.xMaximum() - rect.xMinimum()) / RESOLUTION)
    output = QgsGridFileWriter(idw_interpolator, export_path, rect, ncol, nrows)
    output.writeFile()


    # Now reproject back to WGS84
    output_path = os.path.join(OUTPUT_FOLDER, PROJECT_NAME + '.tif')
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            os.remove(output_path.replace('.tif','.tif.aux.xml'))
        except:
            pass

    params = {
        'INPUT': export_path,
        'SOURCE_CRS': rainfall_layer_utm.crs().authid(),
        'TARGET_CRS': 'EPSG:4326',
        'OUTPUT': os.path.join(OUTPUT_FOLDER, PROJECT_NAME + '.tif')
    }

    res = processing.run('gdal:warpreproject', params)
    rainfall_raster_layer = QgsRasterLayer(res['OUTPUT'], 'Rainfall in mm', 'gdal')

    return rainfall_raster_layer

# reproject input data from PROJECT_EPSG to correct utm zone
def project_to_utm(rainfall_layer):

    # if project crs is NOT wgs84, we first need to project to wgs84 in order to get the correct UTM zone
    if (PROJECT_EPSG != 4326):
        crsSrc = QgsCoordinateReferenceSystem(3857)
        crsDest = QgsCoordinateReferenceSystem(4326)
        xform = QgsCoordinateTransform(crsSrc, crsDest)
        geo_pt = xform.transform(rainfall_layer.extent().center())
    else:
        geo_pt = rainfall_layer.extent().center()

    # get epsg for utm zone
    utm_crs = QgsCoordinateReferenceSystem(convert_wgs_to_utm(geo_pt.x(), geo_pt.y()), QgsCoordinateReferenceSystem.EpsgCrsId)

    # now reproject rainfall layer to utm crs and same to temp location
    out_path = os.path.join(TEMP_FOLDER, 'rainfall_layer_utm.shp')
    if os.path.exists(out_path):
        try:
            os.remove(out_path)
        except:
            pass
    QgsVectorFileWriter.writeAsVectorFormat(rainfall_layer, out_path, 'utf-8', utm_crs, 'Esri Shapefile')

    rainfall_layer_utm = QgsVectorLayer(out_path, 'rainfall_points_utm', 'ogr')

    return rainfall_layer_utm
    
def add_google_satellite_layer():
    service_url = "mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    service_uri = "type=xyz&zmin=0&zmax=21&url=https://" + requests.utils.quote(service_url)
    google_satellite_layer = QgsRasterLayer(service_uri, "Google Satellite", "wms")
    return google_satellite_layer

    def _calculate_break_points():
    pr = rainfall_interpolation_layer.dataProvider()
    bandStats = pr.bandStatistics(1, QgsRasterBandStats.All, rainfall_interpolation_layer.extent(), 0)
    maxVal = bandStats.maximumValue
    minVal = bandStats.minimumValue
    return np.linspace(minVal,maxVal,len(COLOUR_PALLETE))

    # function that return UTM zone given a lat lng
def convert_wgs_to_utm(lon, lat):
    utm_band = str((math.floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return int(epsg_code)

def load_boundary_layers():
    i = 0
    boundary_layers = []
    for path in BOUNDARY_LAYERS_PATHS:
        boundary_layers.append(QgsVectorLayer(path, 'boundary_{}'.format(i), 'ogr'))
        i += 1
    return boundary_layers

def export_map(rainfall_points_layer, rainfall_interpolation_layer, boundary_layers, googleLayer, rainfall_points_layer_name):

    # first, load the layers to the layer registry
    mapLayers = [rainfall_points_layer] + boundary_layers + [rainfall_interpolation_layer, googleLayer] + [rainfall_points_layer_name]
    #QgsProject.instance().addMapLayers([rainfall_points_layer, rainfall_interpolation_layer, googleLayer])
    QgsProject.instance().addMapLayers(mapLayers)

    # next, style the layers by loading style files for them
    rainfall_points_layer.loadNamedStyle(RAINFALL_POINTS_STYLE_FILE)
    for lyr in boundary_layers:
        lyr.loadNamedStyle(BOUNDARY_STYLE_FILE)
    rainfall_points_layer_name.loadNamedStyle(RAINFALL_POINTS_NAME_STYLE_FILE)


    # for the interpolation layer, we need a dymanic way to style the layer - loading a style file wont work well
    # because the min / max of each interpolated raster will be different. Instead, lets use a defined colour ramp,
    # then build the renderer manually
    colorRampItems = []
    breakpoints = _calculate_break_points()
    i = 0
    for hexColorValue, breakpoint in zip(COLOUR_PALLETE, breakpoints):
        if i == 0:
            label = '<= {:.1f}'.format(breakpoint)
        else:
            label = '{:.1f} - {:.1f}'.format(breakpoints[i-1], breakpoint)
        colorRampItems.append(QgsColorRampShader.ColorRampItem(breakpoint, QColor(hexColorValue), label))
        i += 1
    colourRamp = QgsColorRampShader()
    colourRamp.setColorRampType(QgsColorRampShader.Discrete)
    colourRamp.setColorRampItemList(colorRampItems)

    # create a shader from colour ramp
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(colourRamp)

    # create a renderer from shader
    pseudoRenderer = QgsSingleBandPseudoColorRenderer(rainfall_interpolation_layer.dataProvider(), 1, shader)

    # apply renderer to layer and refresh

    rainfall_interpolation_layer.setRenderer(pseudoRenderer)
    rainfall_interpolation_layer.renderer().setOpacity(0.7)
    rainfall_interpolation_layer.triggerRepaint()



    # now setup the map layout
    project = QgsProject.instance()
    manager = project.layoutManager()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName('rainfall interpolation')
    manager.addLayout(layout)


    # map
    map = QgsLayoutItemMap(layout)
    map.setCrs(QgsCoordinateReferenceSystem(4326))
    map.setRect(QRectF(20, 20, 200, 100))  # The Rectangle will be overridden below
    extent = rainfall_interpolation_layer.extent()
    map.setExtent(extent)
    layout.addItem(map)
    map.attemptMove(QgsLayoutPoint(5, 5, QgsUnitTypes.LayoutMillimeters))
    map.attemptResize(QgsLayoutSize(292, 205, QgsUnitTypes.LayoutMillimeters))
    map.zoomToExtent(extent)

    # legend
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle('{} {}'.format(PROJECT_NAME, datetime.date.today()))

    root = QgsLayerTree()
    root.addLayer(rainfall_interpolation_layer)
    legend.model().setRootGroup(root)


    #legend.setLinkedMap(map)  # map is an instance of QgsLayoutItemMap
    layout.addItem(legend)
    legend.attemptMove(QgsLayoutPoint(5, 5, QgsUnitTypes.LayoutMillimeters))
    legend.setFrameEnabled(False)

    legend.setStyleFont(QgsLegendStyle.Subgroup , QFont('Arial',8, QFont.Bold))
    legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont('Arial',8))
    legend.setStyleFont(QgsLegendStyle.Title, QFont('Arial',10, QFont.Bold))

    legend.setSymbolHeight(3)
    legend.setSymbolWidth(5.5)


    # export it
    output_path = os.path.join(OUTPUT_FOLDER, PROJECT_NAME + '.png')
    exporter = QgsLayoutExporter(layout)
    image_export_settings = QgsLayoutExporter.ImageExportSettings()
    image_export_settings.dpi = EXPORT_DPI

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except:
            pass

    exporter.exportToImage(output_path, image_export_settings)


def cleanup():
    for f in os.listdir(TEMP_FOLDER):
        if f.startswith('rainfall_layer_utm') or f.startswith('rainfall_layer_utm_interpolation'):
            try:
                os.remove(os.path.join(TEMP_FOLDER, f))
            except:
                pass

# -----------------------------------------------------------------------------------------------------------------#

# PARAMETERS - the input rainfall csv and output location, these will likely change for each run

# project name - this will be used to name output files
# valid value type: String
PROJECT_NAME = 'Bungulla'

# path to your input rainfall csv
# valid value type: String
INPUT_RAINFALL_CSV_PATH = r"/home/yahor/distribution-map/example/Bungulla-Rainfall-Data-2019-06-09-v2.1.csv"

# field names in csv that have x and y values
# valid value type: String
YFIELD = 'Y'
XFIELD = 'X'

# name of field containing rainfall data to use in interpolation
# valid value type: String
INTERPOLATION_DATA_FIELD_NAME = 'Rainfall last 30 days'

# path(s) to boundary layer(s)
# valid value type: List of String
BOUNDARY_LAYERS_PATHS = [r"/home/yahor/distribution-map/example/Brad Farm Boundary 1.kml",
                       r"/home/yahor/distribution-map/example/Brad Farm Boundary 2.kml"
                       ]

# path to folder to place permanent output
# valid value type: String
OUTPUT_FOLDER = r"/home/yahor/distribution-map/output"

# -----------------------------------------------------------------------------------------------------------------#

# CONFIGS - you'll likely just set these once and use these settings going forward

# path to the app/qgis folder of your QGIS install
# valid value type: String
QGIS_PREFIX_PATH = r"/usr/share/qgis/"

# path to folder to store temporary files (these will be removed after script run)
# valid value type: String
TEMP_FOLDER = r"/home/yahor/Tmp"

# valid value type: String
# path to style files   
#rainfall_style_file = r"C:\Upwork Jobs\CURRENT\Annie Brox - Origo farm - pyqgis script\sample data\Style for interpolated layer.qml"
RAINFALL_POINTS_NAME_STYLE_FILE = r"/home/yahor/distribution-map/example/Style for points name layers.qml"
BOUNDARY_STYLE_FILE = r"/home/yahor/distribution-map/example/Style for boundary layers.qml"
RAINFALL_POINTS_STYLE_FILE = r"/home/yahor/distribution-map/example/Style for points layers.qml"

# color pallete to use for rainfall interpolation layer
# valid value type: List of String
COLOUR_PALLETE = ["#f7fbff","#deebf7","#c6dbef","#9ecae1","#6baed6","#4292c6","#2171b5","#08519c","#08306b"]

# epsg to use (must match that of input rainfall data)
# valid value type: Integer
PROJECT_EPSG = 4326

# output raster RESOLUTION in meters
# valid value type: Numeric (integer or double)
RESOLUTION = 30

# distance beyond bounds of rainfall points to interpolate to in meters
# valid value type: Numeric (integer or double)
INTERPOLATION_PAD_DISTANCE = 1000

# valid value type: string
# valid values: 'boundary' OR 'points'
# what layer should the interpolation extent be based on? Useful if you want to set the interpolation to cover
# the boundary layer instead of just the rainfall points
INTERPOLATION_EXTENT_LAYER = 'boundary'

# resolution of final png map
EXPORT_DPI = 300

#-----------------------------------------------------------------------------------------------------------------#


# START MAIN PROCESS

# First step is to initialize the QGIS app. I'm not sure why their library is set up this way, but you have to manually
# initialize otherwise the spatial objects you create will not be valid.
print('Initializing QGIS...')
os.environ["QT_QPA_PLATFORM"] = r"offscreen"
QgsApplication.setPrefixPath(QGIS_PREFIX_PATH, True)
qgs = QgsApplication([], False)
qgs.initQgis()

# run gdal_warp. Processing is not important as part of PyQGIS, and we actually have to make sure that the path to
# processing is added to our sys.path before we can import. Once imported, this also needs to be initialized.
# Next, we need to import the processing module. We need processing in order to re-project a raster layer. Vector data
# is easy to re-project with the normal PyQGIS library, however for rasters, the easiest way is to use Processing to
sys.path.append(os.path.join("/usr/share/qgis/", 'python', 'plugins'))
import processing
from processing.core.Processing import Processing
Processing.initialize()

# Now that everything is initialized properly, let's load the rainfall csv layer to PyQGIS and make a layer object from it.
print('Loading rainfall points from csv to QGIS layer...')
rainfall_points_layer_name = create_rainfall_layer()
rainfall_points_layer = create_rainfall_layer()
# units (ie degrees), so we can't meaningfully measure distance in that crs. This function takes the center lat / lng
# of the input rainfall csv, calculates the correct utm zone, then projects the rainfall layer to that crs
# Since you want to be able to define the RESOLUTION of the output interpolated raster in linear units (ie meters),
# we need to reproject the input data to a coordinate system that uses meters. WGS84 (ie epsg 4326) uses geographic
print('Reprojecting data to UTM coordinates for processing...')
rainfall_layer_utm = project_to_utm(rainfall_points_layer)
interpolation_data_field_index = rainfall_points_layer.fields().lookupField(INTERPOLATION_DATA_FIELD_NAME)

# function also projects the output raster back from UTM to WGS84
# Now run the actual interpolation to turn the point data in our rainfall layer to a surface (ie raster layer). The
print('Running interpolation...')
rainfall_interpolation_layer = run_interpolation(rainfall_layer_utm, interpolation_data_field_index, boundary_layers)

# Next, create layer objects for designated boundary layers. You may specify a list of boundary layers, and each will
# be loaded and thus appear in the output map.
print('Loading boundary layers...')
boundary_layers = load_boundary_layers()

# We'll load a Google Satellite layer using python's requests module
google_satellite_layer = add_google_satellite_layer()

# QGIS layer registry, styles them, then sets up and exports a .png map
# Finally, set up the May Layout and export a png map. This function adds our layers (rainfall, boundary, satellite) to the
print('Exporting map to "{}"'.format(os.path.join(OUTPUT_FOLDER, PROJECT_NAME + '.png')))
export_map(rainfall_points_layer, rainfall_interpolation_layer, boundary_layers, google_satellite_layer, rainfall_points_layer_name)

# clean up the temp folder
print('Cleaning up temp files...')
cleanup()

print('Script finished successfully')


