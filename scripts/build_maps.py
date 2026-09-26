#!/usr/bin/env python3
from pathlib import Path
import geopandas as gpd, folium
ROOT=Path(__file__).resolve().parents[1]
for commodity in ['manganese','chromite','iron']:
 p=ROOT/f'data/processed/{commodity}_prospectivity.geojson'; g=gpd.read_file(p).to_crs(4326)
 if g.empty: continue
 c=g.geometry.union_all().centroid
 m=folium.Map(location=[c.y,c.x],zoom_start=11,tiles='OpenStreetMap')
 folium.GeoJson(g.to_json(),name=commodity,style_function=lambda f:{'color':'#b91c1c' if commodity=='manganese' else '#2563eb','weight':2,'fillOpacity':0.18}).add_to(m)
 folium.LayerControl().add_to(m); m.save(ROOT/f'outputs/maps/{commodity}_prospectivity_map.html')
print('maps written')

# Version 4 target polygons are rendered separately so the legacy screening
# maps remain reproducible and backwards compatible.
v4 = ROOT/'data/processed/manganese_targets_v4.geojson'
if v4.exists():
 g = gpd.read_file(v4).to_crs(4326)
 if not g.empty:
  c = g.geometry.union_all().centroid
  m = folium.Map(location=[c.y,c.x], zoom_start=11, tiles='OpenStreetMap')
  folium.GeoJson(g.to_json(), name='manganese_targets_v4', style_function=lambda f:{'color':'#15803d','weight':3,'fillOpacity':0.28}, tooltip=folium.GeoJsonTooltip(fields=['candidate_id','rank','manganese_score','elevation_m','slope_deg','relief_m_local'], aliases=['Target','Rank','Score','Elevation m','Slope deg','Local relief m'])).add_to(m)
  folium.LayerControl().add_to(m); m.save(ROOT/'outputs/maps/manganese_targets_v4_map.html')
