## This script generates points on a transect. Two layers are required to run this script, a marker layer and a transect layer. 
## The points are generated in a given distance (e.g. +-10m) from the markers.


from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY
)
from PyQt5.QtCore import QVariant

# === SETTINGS ===
transect_layer_name = "transect"
marker_layer_name = "markers"
distance_offset = 10  # meters

# === LOAD LAYERS ===
project = QgsProject.instance()
transect_layer = project.mapLayersByName(transect_layer_name)[0]
marker_layer = project.mapLayersByName(marker_layer_name)[0]

# Merge all transect features into one geometry
transect_geom = QgsGeometry.unaryUnion([f.geometry() for f in transect_layer.getFeatures()])
transect_length = transect_geom.length()
print(f"Transect length: {transect_length:.2f} m")

# === CREATE OUTPUT LAYERS ===
def create_layer(name):
    layer = QgsVectorLayer("Point?crs=" + transect_layer.crs().authid(), name, "memory")
    provider = layer.dataProvider()
    provider.addAttributes([
        QgsField("marker_id", QVariant.Int),
        QgsField("marker_dist", QVariant.Double),
        QgsField("offset", QVariant.String)
    ])
    layer.updateFields()
    QgsProject.instance().addMapLayer(layer)
    return layer, provider

plus_layer, plus_provider = create_layer("plus10_points")
minus_layer, minus_provider = create_layer("minus10_points")

# === PROCESS EACH MARKER ===
for i, marker in enumerate(marker_layer.getFeatures()):
    marker_geom = marker.geometry()
    marker_point = marker_geom.asPoint()

    # Snap marker to transect
    closest_point_info = transect_geom.closestSegmentWithContext(marker_point)
    snapped_point = QgsPointXY(closest_point_info[1])  # point on transect

    # Distance along transect
    marker_distance = transect_geom.lineLocatePoint(QgsGeometry.fromPointXY(snapped_point))
    print(f"Marker {i+1}: marker_distance = {marker_distance:.2f} m")

    # +10 m
    plus_distance = marker_distance + distance_offset
    if plus_distance <= transect_length:
        plus_point = transect_geom.interpolate(plus_distance)
        plus_feat = QgsFeature(plus_layer.fields())
        plus_feat.setGeometry(plus_point)
        plus_feat.setAttributes([i+1, marker_distance, "+10m"])
        plus_provider.addFeatures([plus_feat])
        print("  Added +10m")
    else:
        print("  Skipped +10m (beyond transect)")

    # -10 m
    minus_distance = marker_distance - distance_offset
    if minus_distance >= 0:
        minus_point = transect_geom.interpolate(minus_distance)
        minus_feat = QgsFeature(minus_layer.fields())
        minus_feat.setGeometry(minus_point)
        minus_feat.setAttributes([i+1, marker_distance, "-10m"])
        minus_provider.addFeatures([minus_feat])
        print("  Added -10m")
    else:
        print("  Skipped -10m (before start)")

plus_layer.updateExtents()
minus_layer.updateExtents()

print("✅ Finished creating ±10 m points")

