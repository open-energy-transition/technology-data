# `TechnologyCollection` Class Documentation

<!--
SPDX-FileCopyrightText: The technology-data authors

SPDX-License-Identifier: MIT

-->

## Overview

The `TechnologyCollection` class in `technologydata` represents a collection of `Technology` objects, providing tools for filtering, exporting, currency adjustment, model fitting, and projection. It is designed to manage multiple technology datasets, supporting reproducibility, scenario analysis, and future projections.

## Features

- **Collection Management**: Stores and iterates over multiple `Technology` objects.
- **Filtering**: Supports regex-based filtering by attributes `name`, `region`, `year`, `case`, and `detailed technology`.
- **Data Export**: Converts the collection to pandas DataFrame, CSV, and JSON formats, with schema export.
- **Currency Adjustment**: Harmonizes all technology parameters to a target currency, including inflation and exchange rates.
- **Model Fitting**: Fits growth models to technology parameters across the collection.
- **Projection**: Projects parameters to future years using growth models or statistical options.
- **Integration**: Designed for use with energy system modeling and technology parameter analysis.

## Usage Examples

### Creating a TechnologyCollection

```python
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])
```

### Filtering Technologies

```python
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

filtered = collection.get(name="Tech", region="DEU", year=2020, case="Base", detailed_technology="Solar")
print(filtered)  # TechnologyCollection with matching technologies
```

### Exporting to CSV

```python
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

collection.to_csv(path_or_buf="technologies.csv")
```

### Exporting to JSON and Schema

```python
import pathlib
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

collection.to_json(file_path=pathlib.Path("technologies.json"))
```

### Currency Adjustment

```python
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])
converted = collection.to_currency("USD_2025", source="worldbank")
```

### Fitting a Growth Model

```python
from technologydata.technologies.growth_models import LinearGrowth
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

fitted_model = collection.fit(parameter="installed capacity", model=LinearGrowth(m=0.5, A=10))
```

### Projecting Parameters

```python
from technologydata.technologies.growth_models import LinearGrowth
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

projected = collection.project(
    to_years=[2030, 2040],
    parameters={
        "installed capacity": LinearGrowth(m=0.5, A=10),
        "lifetime": "mean",
        "efficiency": "NaN"
    }
)
```

## API Reference

### Attributes

- `technologies`: list[Technology]
  - List of Technology objects in the collection.

### Methods

- `__iter__() -> Iterator[Technology]`
  - Iterate over the technologies in the collection.
- `__len__() -> int`
  - Return the number of technologies in the collection.
- `get(name, region, year, case, detailed_technology) -> TechnologyCollection`
  - Filter technologies using regex patterns for key attributes.
- `to_dataframe() -> pandas.DataFrame`
  - Convert the collection to a pandas DataFrame.
- `to_csv(**kwargs)`
  - Export the collection to a CSV file.
- `to_json(file_path, schema_path=None)`
  - Export the collection to a JSON file and schema.
- `from_json(file_path) -> TechnologyCollection`
  - Load a collection from a JSON file.
- `to_currency(target_currency, overwrite_country=None, source='worldbank') -> TechnologyCollection`
  - Adjust all technology parameters to the target currency.
- `fit(parameter, model, p0=None) -> GrowthModel`
  - Fit a growth model to a specified parameter across all technologies.
- `project(to_years, parameters) -> TechnologyCollection`
  - Project specified parameters for all technologies to future years.

## Limitations & Notes

- **Filtering**: Regex patterns are case-insensitive and applied to non-optional attributes.
- **Export**: Default CSV export uses UTF-8 encoding and quotes all fields.
- **Schema**: JSON schema is generated automatically and includes field descriptions.
- **Type Checking**: The class uses Pydantic for validation and type enforcement.
- **Projection**: The 'closest' option for parameter projection is not yet implemented.
