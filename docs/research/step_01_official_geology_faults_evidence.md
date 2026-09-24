# Neyriz geology and faults — source evidence log

Research date: 2026-09-23

## Scope
Official geology and fault data for a Neyriz, Fars, Iran AOI. Claims below are verified from opened source pages or downloaded service metadata, not search snippets.

## 1. Primary authoritative map service — GSI / NGDIR, hosted by BGS / OneGeology

- **Authority / provenance**: The official Geological Survey & Mineral Exploration of Iran (GSI) website identifies the National Geosciences Database of Iran (NGDIR) as an institutional destination: https://gsi.ir/en . The BGS hosted ISO record names **NGDIR** as point of contact/data provider and states that the Iranian 1:1,000,000 bedrock-and-structural map was compiled by M.R. Sahandi and M. Soheili, contributions from S. Allah Madadai, A. Mohammadi Araghi and R. Zabihi; digitized/GIS-ready by M. Sadeghi, T. Delavar and A. Jafari Rad; cartography by A. Malek Ahmadi and M. Sadeghi.
- **Data description / scale**: `IRN GSI 1:1M bedrock geology` and `IRN GSI 1:1M faults` (nominal scale 1:1,000,000). These are national-scale thematic map layers, not a Neyriz 1:100,000 product.
- **Opened metadata record (faults, XML)**: https://hosted-metadata.bgs.ac.uk/geonetwork/srv/api/records/714fcdcf319594a80d8670851da5312994ff932c/formatters/xml
- **Opened metadata record (bedrock, XML)**: https://hosted-metadata.bgs.ac.uk/geonetwork/srv/api/records/3510e0262fde45dd815b425d8801ba60f846f122/formatters/xml
- **Opened service record (licensing and operations)**: https://hosted-metadata.bgs.ac.uk/geonetwork/srv/api/records/00d05ddbbb67477716d7d3d200fe65c594d81a71 . It is ISO 19119 service metadata, revision/date stamp 2019-01-28; service type OGC WMS 1.3.0; no fee.
- **Exact machine endpoint**: `https://ogc.bgs.ac.uk/cgi-bin/BGS_GSI_EN_Bedrock_and_Structural_Geology/ows?language=eng&service=WMS&request=GetCapabilities&version=1.3.0`
  - Verified live on 2026-09-23: 200 XML, 14,821 bytes.
  - Layers: `IRN_GSI_1M_BG` (bedrock geology) and `IRN_GSI_1M_MSF` (faults). The WMS supports `CRS:84`, `EPSG:4326`, and `EPSG:3857`.
  - Extents from returned Capabilities: bedrock 43.963618–64.736655 E, 24.732793–40.118233 N; faults 44.066930–64.687408 E, 25.079905–39.861889 N. Both include Neyriz (~54.3 E, 29.2 N).
  - Available operations shown in ISO service record: GetCapabilities, GetMap, GetFeatureInfo, DescribeLayer, GetLegendGraphic, GetStyles. There is no advertised WFS/download feature endpoint in this record; it is a map service, not a downloadable vector package.
- **AOI access verification**: A fixed `GetMap` request for a Neyriz test box (54.15–54.45 E, 29.10–29.35 N) returned valid, non-empty PNGs for both map layers. Repro script: `get_neyriz_wms.sh`. Test outputs: `neyriz_wms/IRN_GSI_1M_BG_neyriz.png`, sha256 `d68c9e8232cbd482c0638f2c2f41d41f81755bc01e5d9141e4d9b2be6f985ac9`; `neyriz_wms/IRN_GSI_1M_MSF_neyriz.png`, sha256 `1b2777c809b2857d60e4cdca7c7746b6b78f157d9e4d5b05c45c04108dc52b06`.
- **Licence / use terms**: Service record: available to all users, GSI retains copyright; no selling service based on the material without an appropriate licence; use requires cited reference; no warranty of quality/accuracy/completeness/suitability. This is not an open-data licence (e.g., CC-BY) and is not permission to redistribute extracted files.
- **Reproducibility conclusion**: A reproducible GIS **map-input** workflow is possible (store GetCapabilities XML; request exact WMS layer/version/CRS/BBOX/size/date; cache checksum). It is suitable as a national-scale qualitative geology/fault covariate or reference only. It is **not** a reproducible vector-feature model source: WMS offers rendered maps/possibly identify responses, not documented bulk feature download; scale is 1:1M; fixed service state may change. Do not digitize/re-distribute or use commercially beyond terms without clarification/licence.

## 2. USGS public reference dataset — Major faults in Iran (flt2cg)

- **Official record / DOI**: https://doi.org/10.5066/P9TMSOQ0 ; original metadata https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?name=flt2cg.xml . Opened both.
- **Data**: `flt2cg`: a MultiLineString shapefile of major faults; `type` (`th` thrust / `o` other) and `line` (`e` evident / `i` inferred), with source attribution to USGS. Geographic bounding box: 44.22825622558594–63.27131652832031 E, 25.07513999938965–39.400691986083984 N, therefore includes Neyriz.
- **CRS / dates / resolution**: native CRS EPSG:4326 / WGS 1984; original data time period 1999-09; original release 1999-11; public record publication date 2021-05-21. Metadata reports sources generalized from the 1:2,500,000 geological map and a stated 1.6-km RMS positional error (max roughly 6 km); it also characterizes faults as major faults significant to map at 1:25,000,000. Not AOI-scale mapping.
- **Exact attachment endpoints as exposed in official ScienceBase JSON (all required parts must be acquired)**:
  - DBF: https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?f=__disk__6c%2Fa4%2Fae%2F6ca4ae96561311d7b180600511845a8191af59ed
  - PRJ: https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?f=__disk__a9%2F04%2Fe2%2Fa904e29c648832a59ab1fed7f2ddc1abb9e4044b
  - SHP: https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?f=__disk__2c%2F66%2F40%2F2c6640ac690e8e3094404a62410848d3995d5edb
  - SHX: https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?f=__disk__69%2Fcd%2Fd6%2F69cdd6b4cab1780c087f4bbb7ed602330cdae673
  - FGDC XML: https://www.sciencebase.gov/catalog/file/get/60a82961d34ea221ce4e607a?f=__disk__91%2Fc3%2Fce%2F91c3ce97a6922d42347cc676e4d11d7d4435ab56
- **Access and license evidence**: USGS catalogue marks access `public` and applies the US Government Public Domain label (https://www.usa.gov/publicdomain/label/1.0/). However, original FGDC metadata also preserves historical ESRI restrictions applying to portions of the broader package (oil/gas centrepoints, coastline and country boundaries); **do not conflate those with the standalone fault-only file**, and retain/cite metadata. The official record lists it as a Shapefile/Downloadable dataset.
- **Actual-access caveat**: On 2026-09-23, the official record/metadata and JSON opened successfully through the research fetcher, but direct command-line attachment downloads in this sandbox triggered ScienceBase Cloudflare 403 challenge pages. Therefore no binary shapefile was claimed or packaged here. That is an environment/session anti-bot barrier, not evidence that the official endpoints do not exist. The record’s file list shows .shp/.shx/.dbf/.prj/.xml and their direct endpoints above.
- **Reproducibility conclusion**: Yes as a low-resolution, version-pinnable public fault baseline, after recording DOI, 1999 data date, EPSG:4326, checksum and file URLs. No for local alteration/fault-distance modelling where 1–6 km location uncertainty or 1:2.5M/generalized source scale is unacceptable.

## 3. No verified Neyriz-specific official downloadable detailed geology/fault vector file

- The actual GSI public site opened: https://gsi.ir/en and confirms GSI and NGDIR institutional roles, but the accessible page does not expose a Neyriz AOI data package or download endpoint.
- The official NGDIR linked site could not be text-extracted at https://www.ngdir.ir/ during research, and no opened official source demonstrated a public downloadable 1:100,000 Neyriz geology/fault vector/PDF archive. This is **absence of verification**, not a claim that it does not exist.
- Treat any detailed Neyriz geology, fault validation, outcrop alteration, structure measurements, sampling, or laboratory assay dataset as **not supplied by the verified public services**. Such inputs require an official request/licence from GSI/NGDIR (metadata contact in map record: National Geoscience Database of Iran, mehrdad.shirzad@gmail.com, +98 21 44241376), a separately verified provider, or original field/lab work. Never infer these values from the 1:1M WMS or USGS generalized fault file.

## Saved artifacts

- `evidence.md`: this complete evidence log.
- `ogc_checks/gsi_https.xml`: verified WMS 1.3.0 Capabilities response.
- `get_neyriz_wms.sh`: reproducible Neyriz `GetMap` request.
- `neyriz_wms/*.png`: retrieved, non-empty AOI map images.
- `check_ogc.sh`: WMS endpoint test and published USGS OWS attempt.
- `metadata_extract.txt`: direct USGS attachment URL extraction from opened official ScienceBase JSON.
