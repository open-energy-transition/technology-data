# `DataAccessor` Class Documentation

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

## Overview

The `DataAccessor` class provides a standardized way to access and load technology datasets from versioned data sources. It simplifies the process of selecting a specific data source and version, automatically handling the resolution of file paths and loading the data into a `DataPackage` object. It also provides an interface to run the parsers that generate this data.

It is designed to work with a specific directory structure where datasets are organized by name and version.

## Features

- **Data Source Selection**: Easily specify which dataset to load using the `DataSourceName` enumeration.
- **Version Management**: Load a specific version of a dataset or automatically detect and use the latest available version.
- **Standardized Loading**: Loads a `DataPackage` from a versioned folder, which is expected to contain `technologies.json` and optionally `sources.json`.
- **Parsing Interface**: Provides a `parse()` method to run the appropriate parser for a given data source and version to generate the data files.
- **Error Handling**: Raises `FileNotFoundError` if the specified data source or version directories cannot be found, and `ValueError` for unsupported sources or versions.
- **Seamless Integration**: The `load()` method returns a `DataPackage` object, ready for use with other components of the `technologydata` library.
- **Path Safety Helper**: Provides `ensure_path_exists()` to create missing directories (including parents) safely.

## Usage Examples

### Creating a DataAccessor

To use `DataAccessor`, create an instance with `data_source`. If the `version` is not provided, the `DataAccessor` will automatically determine the latest available data version and use it. Best practice is to always specify the version to ensure reproducibility, otherwise package updates may change the data returned when newer versions for this package become available.
Finally, you can optionally override `data_path`.

```python
from technologydata.parsers.data_accessor import DataAccessor

# Create an accessor for a specific version
accessor_v1 = DataAccessor(
    data_source="manual_input_usa",
    version="v1.0.0"
)
```

### Loading Data

Once the `DataAccessor` is instantiated, call the `load()` method to load the dataset. The method handles finding the correct directory and then calls `DataPackage.from_json()` on that directory.

The directory structure is expected to be: `src/technologydata/parsers/<data_source_name>/<version>/`.

The `load()` method will look for the exact version specified during instantiation. If the version is not provided or not found, it will raise a `ValueError` and inform you of the latest available version.

```python
# Assuming the path .../parsers/manual_input_usa/v1.0.0/ exists
dp_v1 = accessor_v1.load()

# dp_v1 is now a DataPackage object containing the data from v1.0.0
print(type(dp_v1))
# <class 'technologydata.datapackage.DataPackage'>
```

### Parsing Raw Data

The `parse()` method is used to execute the data processing pipeline for a specific data source and version. It takes the raw data file as input and generates the structured `technologies.json` and `sources.json` files.

```python
from technologydata.parsers.data_accessor import DataAccessor

# Create an accessor for the version to be parsed
parser_accessor = DataAccessor(
    data_source="dea_energy_storage",
    version="v10"
)

# Run the parser
parser_accessor.parse(
    input_file_name="dea_energy_storage_v10.xlsx",
    num_digits=2,
    archive_source=True
)
```

## API Reference

Please refer to the [API documentation](../api/data_accessor.md) for detailed information on the `DataAccessor` class methods and attributes.

## Limitations & Notes

-   **Directory Structure**: The `DataAccessor` expects a specific directory structure within the project: `src/technologydata/parsers/<data_source_name>/<version>/ unless `data_path` is overridden.
-   **Version Naming**: Version directories must be prefixed with a `v` and follow a pattern that can be parsed by `packaging.version` (e.g., `v1`, `v2.0`, `v1.0.1-alpha`). Directories that do not match this pattern will be ignored when searching for the latest version.
-   **Target Data**: The `load()` method is designed to load a `DataPackage` from a folder. See the [DataPackage](./datapackage.md) documentation for more details on the expected contents of that folder (i.e.,`technologies.json`).
- **Input Location for Parse**: `parse()` expects `input_file_name` under `data_path/raw/`.
