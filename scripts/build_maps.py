#!/usr/bin/env python3
from pathlib import Path
import geopandas as gpd, folium
ROOT=Path(__file__).resolve().parents[1]
for commodity in ['manganese','chromite','iron']:
 p=ROOT/f'data/processed/{commodity}_prospectivity.geojson'; g=gpd.read_file(p).to_crs(4326)
 if g.empty: continue
 c=g.geometry.unary_union.centroid
 m=folium.Map(location=[c.y,c.x],zoom_start=11,tiles='OpenStreetMap')
 folium.GeoJson(g.to_json(),name=commodity,style_function=lambda f:{'color':'#b91c1c' if commodity=='manganese' else '#2563eb','weight':2,'fillOpacity':0.18}).add_to(m)
 folium.LayerControl().add_to(m); m.save(ROOT/f'outputs/maps/{commodity}_prospectivity_map.html')
print('maps written')
