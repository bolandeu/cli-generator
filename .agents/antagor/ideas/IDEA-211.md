---
id: IDEA-211
title: 'Template test_antagor_project_config: allow longer prefixes and a set mode'
created: '2026-10-16T11:29:02+00:00'
source_project: dataio
source_path: /Users/bolandau/Work/tools/dataio
status: new
for_path: /Users/bolandau/Work/tools/cli-generator
---

tests/test_scripts.py::test_antagor_project_config asserts prefix [A-Z]{2,4} and 'mode' not in antagor.toml. The prefix must equal the Plane project identifier (dataio: DATAIO, 6 letters), and the Human may set a mode (antagor mode set fast). dataio had to change this existing test (commit after 97492cb). Suggest: prefix [A-Z]{2,12}, mode in the allowed set.
