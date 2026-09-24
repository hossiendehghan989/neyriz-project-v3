#!/usr/bin/env bash
set -uo pipefail
out=/home/ubuntu/jobs/626368693de4_a0/ogc_checks
mkdir -p "$out"
ua='Mozilla/5.0'
for scheme in https http; do
  base="${scheme}://ogc.bgs.ac.uk/cgi-bin/BGS_GSI_EN_Bedrock_and_Structural_Geology/ows"
  curl -A "$ua" -L -sS --connect-timeout 30 --max-time 90 -D "$out/gsi_${scheme}.headers" \
    "${base}?language=eng&service=WMS&request=GetCapabilities&version=1.3.0" \
    -o "$out/gsi_${scheme}.xml" -w "${scheme}: http=%{http_code} type=%{content_type} bytes=%{size_download}\n" || true
done
# The USGS mapping endpoint advertised by the DOI landing page: inspect whether it exposes a WFS suitable for feature retrieval.
base='https://www.sciencebase.gov/catalogMaps/mapping/ows/60a82961d34ea221ce4e607a'
curl -A "$ua" -L -sS --connect-timeout 30 --max-time 90 -D "$out/usgs_wfs.headers" \
  "${base}?service=WFS&request=GetCapabilities&version=2.0.0" \
  -o "$out/usgs_wfs.xml" -w "usgs-wfs: http=%{http_code} type=%{content_type} bytes=%{size_download}\n" || true
for f in "$out"/*.xml; do echo "--- $(basename "$f")"; file "$f"; grep -oE '<(Name|Title|CRS|SRS|DefaultCRS|OtherCRS|FeatureType|Layer)[^>]*>[^<]*' "$f" | head -80 || true; done
