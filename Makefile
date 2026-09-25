PYTHON ?= python3

.PHONY: help install run model maps terrain sentinel2 validate test ci

help:
	@printf '%s\n' \
	  'Neyriz project commands:' \
	  '  make install  - install runtime dependencies' \
	  '  make run      - build model, maps, terrain products, and validate all outputs' \
	  '  make terrain  - build checksum-verified DEM terrain derivatives only' \
	  '  make sentinel2 - re-acquire the pinned low-cloud scene and clip it to AOI' \
	  '  make validate - run evidence, provenance, project, and raster checks' \
	  '  make test     - run unit tests' \
	  '  make ci       - compile, test, run, and validate (same contract as CI)'

install:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-geospatial.txt

run: model maps terrain validate

model:
	$(PYTHON) scripts/merge_project_inputs.py
	$(PYTHON) scripts/build_multicommodity_prospectivity.py

maps:
	$(PYTHON) scripts/build_maps.py

terrain:
	$(PYTHON) scripts/build_terrain_derivatives.py

sentinel2:
	$(PYTHON) scripts/acquire_sentinel2_scene.py

validate:
	$(PYTHON) scripts/validate_data_provenance.py
	$(PYTHON) scripts/validate_evidence_gates.py
	$(PYTHON) scripts/evaluate_independent_validation.py
	$(PYTHON) scripts/evaluate_spatial_validation.py
	$(PYTHON) scripts/validate_project.py
	$(PYTHON) scripts/validate_terrain_outputs.py
	$(PYTHON) scripts/validate_sentinel2_outputs.py

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

ci:
	$(PYTHON) -m compileall -q scripts
	$(MAKE) test
	$(MAKE) run
