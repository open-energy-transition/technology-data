# Datasets

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

`technologydata` ships parsed versions of the following datasets.
Load any of them with `DataAccessor(data_source="<key>", version="<version>").load()`.

| Dataset | Key | Versions | Region | Technologies | License |
|---|---|---|---|---|---|
| [DEA Technology Data for Energy Storage](dea_energy_storage.md) | `dea_energy_storage` | `v10` | EU | Electricity, heat, gas and hydrogen storage | CC-BY-4.0 |
| [PyPSA technology-data manual inputs for the USA](manual_input_usa.md) | `manual_input_usa` | `v0.13.4` | USA | Electrolysis, batteries, CCS power plants, Fischer-Tropsch, direct air capture | CC-BY-4.0 |

Each fact sheet follows the same structure: at a glance, available versions, accessing the data, contents, field mapping, naming conventions, assumptions and deviations from the source, reproduce, known limitations, citation.
The front matter of each page holds the same key facts in machine-readable form.
The code blocks on every fact sheet are tested against the shipped data.

To add a dataset, see [Adding a dataset](../contributing/adding_a_dataset.md).
