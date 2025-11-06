# `DataPackage` Class Documentation

<!--
SPDX-FileCopyrightText: The technology-data authors

SPDX-License-Identifier: MIT

-->

## Overview

The `DataPackage` class in `technologydata` provides a container for managing collections of `Technology` and `Source` objects, supporting batch operations and import/export utilities. It is designed to facilitate the organization, sharing, and processing of technology datasets, including provenance tracking and source management.

## Features

- **Technology Collection**: Stores a collection of `Technology` objects via the `TechnologyCollection` class.
- **Source Collection**: Stores a collection of `Source` objects via the `SourceCollection` class.
- **Batch Operations**: Supports batch export to JSON and CSV formats.
- **Source Extraction**: Automatically extracts and aggregates sources from all parameters in the technology collection.
- **Loading Utilities**: Provides methods to load a data package from JSON files.

## Usage Examples

### Creating a DataPackage

You can create a `DataPackage` by instantiating it directly or by loading from JSON files.

```python
from technologydata.datapackage import DataPackage
from technologydata.technology_collection import TechnologyCollection
from technologydata.source_collection import SourceCollection

# Create a DataPackage with existing collections
dp = DataPackage(
    technologies=TechnologyCollection(...),
    sources=SourceCollection(...),
)
```

### Loading from JSON

To load a `DataPackage` from a folder containing `technologies.json` and (optionally) `sources.json`:

```python
from technologydata.datapackage import DataPackage
dp = DataPackage.from_json("path/to/data_package_folder")
```

This will automatically extract sources from the technologies if not already present.

### Exporting to JSON

Export the data package to JSON files in a specified folder:

```python
from technologydata.datapackage import DataPackage
from technologydata.technology_collection import TechnologyCollection
from technologydata.source_collection import SourceCollection

# Create a DataPackage with existing collections
dp = DataPackage(
    technologies=TechnologyCollection(...),
    sources=SourceCollection(...),
)
dp.to_json("path/to/output_folder")
```

### Exporting to CSV

Export the data package to CSV files:

```python
from technologydata.datapackage import DataPackage
from technologydata.technology_collection import TechnologyCollection
from technologydata.source_collection import SourceCollection

# Create a DataPackage with existing collections
dp = DataPackage(
    technologies=TechnologyCollection(...),
    sources=SourceCollection(...),
)

dp.to_csv("path/to/output_folder")
# Creates technologies.csv and sources.csv in the output folder
```

### Extracting Source Collection

If you want to extract and aggregate all sources from the technology collection:

```python
from technologydata.datapackage import DataPackage
from technologydata.technology_collection import TechnologyCollection

# Create a DataPackage with existing collections
dp = DataPackage(
    technologies=TechnologyCollection(...),
)

# Populate dp.sources with all unique sources from the technology collection
dp.get_source_collection()
```

## API Reference

### Attributes

- `technologies`: Optional `TechnologyCollection` containing technology objects.
- `sources`: Optional `SourceCollection` containing source objects.

### Methods

- `get_source_collection()`: Extracts all sources from the technology collection and populates the `sources` attribute.
- `from_json(path_to_folder)`: Loads a `DataPackage` from JSON files in the specified folder.
- `to_json(folder_path)`: Exports the data package to JSON files.
- `to_csv(folder_path)`: Exports the data package to CSV files.

## Limitations & Notes

- **Error Handling**: If neither technologies nor sources are available, source extraction will raise a `ValueError`.
- **No Data Validation**: The class assumes that the underlying `TechnologyCollection` and `SourceCollection` are valid and compatible.
