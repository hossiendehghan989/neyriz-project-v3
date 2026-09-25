#!/usr/bin/env python3
"""Create deterministic interactive maps for existing prospectivity layers."""
from pathlib import Path

import folium
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

for commodity in ["manganese", "chromite", "iron"]:
    path = ROOT / f"data/processed/{commodity}_prospectivity.geojson"
    layer_data = gpd.read_file(path).to_crs(4326)
    if layer_data.empty:
        continue

    centroid = layer_data.geometry.union_all().centroid
    map_view = folium.Map(location=[centroid.y, centroid.x], zoom_start=11, tiles=None)
    map_view._id = f"{commodity}_prospectivity_map"

    basemap = folium.TileLayer("OpenStreetMap", name="OpenStreetMap")
    basemap._id = f"{commodity}_openstreetmap"
    basemap.add_to(map_view)

    overlay = folium.GeoJson(
        layer_data.to_json(),
        name=commodity,
        style_function=lambda feature, commodity=commodity: {
            "color": "#b91c1c" if commodity == "manganese" else "#2563eb",
            "weight": 2,
            "fillOpacity": 0.18,
        },
    )
    overlay._id = f"{commodity}_prospectivity_overlay"
    overlay.add_to(map_view)

    controls = folium.LayerControl()
    controls._id = f"{commodity}_layer_control"
    controls.add_to(map_view)

    map_view.save(ROOT / f"outputs/maps/{commodity}_prospectivity_map.html")

print("maps written")
