from qgis.core import (
    QgsProject,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsVectorLayer,
    QgsField,
    QgsWkbTypes
)
from PyQt5.QtCore import QVariant

# --- SETTINGS ---
layer_name = "markers"   # your layer name
distances = [10, 1]      # distances in map units (meters if projected CRS)
directions = {
    "N": (0, 1),
    "S": (0, -1),
    "E": (1, 0),
    "W": (-1, 0),
}

# --- GET MARKERS LAYER ---
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# --- CREATE OUTPUT MEMORY LAYER ---
epsg = layer.crs().authid()
out_layer = QgsVectorLayer(f"Point?crs={epsg}", "marker_offsets", "memory")
prov = out_layer.dataProvider()

# Add fields: copy from original + add direction and distance
prov.addAttributes(layer.fields())
prov.addAttributes([
    QgsField("direction",  QVariant.String),
    QgsField("distance_m", QVariant.Double)
])
out_layer.updateFields()

# --- GENERATE OFFSET POINTS ---
for feature in layer.getFeatures():
    geom = feature.geometry()
    if geom.isEmpty() or geom.type() != QgsWkbTypes.PointGeometry:
        continue
    point = geom.asPoint()
    x, y = point.x(), point.y()

    for dist in distances:
        for dir_name, (dx, dy) in directions.items():
            new_x = x + dx * dist
            new_y = y + dy * dist

            new_feat = QgsFeature(out_layer.fields())
            new_feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y)))
            new_feat.setAttributes(feature.attributes() + [dir_name, dist])
            prov.addFeature(new_feat)

# --- ADD TO PROJECT ---
out_layer.updateExtents()
QgsProject.instance().addMapLayer(out_layer)

print("✅ Offset points layer created successfully!")

