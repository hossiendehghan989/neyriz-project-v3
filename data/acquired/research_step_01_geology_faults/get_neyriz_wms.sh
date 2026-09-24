#!/usr/bin/env bash
set -euo pipefail
out=/home/ubuntu/jobs/626368693de4_a0/neyriz_wms
mkdir -p "$out"
base='https://ogc.bgs.ac.uk/cgi-bin/BGS_GSI_EN_Bedrock_and_Structural_Geology/ows'
# Neyriz AOI: 54.15–54.45 E, 29.10–29.35 N. CRS:84 specifies longitude,latitude ordering.
for layer in IRN_GSI_1M_BG IRN_GSI_1M_MSF; do
  curl -fsSLG "$base" \
    --data-urlencode 'language=eng' \
    --data-urlencode 'SERVICE=WMS' \
    --data-urlencode 'VERSION=1.3.0' \
    --data-urlencode 'REQUEST=GetMap' \
    --data-urlencode "LAYERS=${layer}" \
    --data-urlencode 'STYLES=' \
    --data-urlencode 'CRS=CRS:84' \
    --data-urlencode 'BBOX=54.15,29.10,54.45,29.35' \
    --data-urlencode 'WIDTH=1200' \
    --data-urlencode 'HEIGHT=1000' \
    --data-urlencode 'FORMAT=image/png' \
    --data-urlencode 'TRANSPARENT=TRUE' \
    -o "$out/${layer}_neyriz.png"
done
file "$out"/*.png
sha256sum "$out"/*.png
