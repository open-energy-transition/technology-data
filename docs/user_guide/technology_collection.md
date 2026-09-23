# `TechnologyCollection` Class Documentation

## Overview

The `TechnologyCollection` class in `technologydata` represents a collection of `Technology` objects, providing tools for filtering, exporting, currency adjustment, model fitting, and projection. It is designed to manage multiple technology datasets, supporting reproducibility, scenario analysis, and future projections.

## Features

- **Collection Management**: Stores and iterates over multiple `Technology` objects.
- **Filtering**: Supports regex-based filtering by attributes `name`, `region`, `year`, `case`, and `detailed technology`.
- **Data Export**: Converts the collection to pandas DataFrame, CSV, and JSON formats, with schema export.
- **Currency Adjustment**: Harmonizes all technology parameters to a target currency, including inflation and exchange rates.
- **Formula System**: Derives missing parameters (`calculate_parameters`) and checks equation-level consistency (`check_consistency`) for every technology in the collection.
- **Model Fitting**: Fits growth models to technology parameters across the collection.
- **Projection**: Projects parameters to future years using growth models or statistical options.
- **Integration**: Designed for use with energy system modeling and technology parameter analysis.

## Usage Examples

### Creating a TechnologyCollection

```python
from technologydata import Technology, TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])
```

### Filtering Technologies

```python
from technologydata import Technology, TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

filtered = collection.get(name="Tech", region="DEU", year=2020, case="Base", detailed_technology="Solar")
print(filtered)  # TechnologyCollection with matching technologies
```

### Exporting to CSV

```python
from technologydata import Technology, TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

collection.to_csv(path_or_buf="technologies.csv")
```

### Exporting to JSON and Schema

```python
import pathlib
from technologydata import Technology, TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

collection.to_json(file_path=pathlib.Path("technologies.json"))
```

### Currency Adjustment

```python
from technologydata import Technology, TechnologyCollection

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])
converted = collection.to_currency("USD_2025", source="worldbank")
```

### Deriving Missing Parameters and Checking Consistency

`calculate_parameters` and `check_consistency` apply the corresponding
[`Technology`](./technology.md) method to every technology in the collection and
return, respectively, a new `TechnologyCollection` and a list of per-equation
status dicts (one per technology, in the same order as `collection.technologies`).

```python
from technologydata import Parameter, Technology, TechnologyCollection

tech1 = Technology(
    name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV",
    parameters={
        "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
        "wacc": Parameter(magnitude=0.07, units="dimensionless"),
        "lifetime": Parameter(magnitude=20.0, units="year"),
    },
)
collection = TechnologyCollection(technologies=[tech1])

# Derive "eac" (and any other derivable parameter) for every technology
derived = collection.calculate_parameters()
print(derived.technologies[0].parameters["eac"])

# Check consistency of every technology's "eac" against registered equations
status = derived.check_consistency(parameters=["eac"])
print(status[0])  # status dict for tech1, e.g. {'eac_annuity': True, ...}
```

### Fitting a Growth Model

```python
from technologydata import Technology, TechnologyCollection
from technologydata.technologies.growth_models import LinearGrowth

tech1 = Technology(name="Tech1", region="DEU", year=2020, case="Base", detailed_technology="Solar PV", parameters={})
tech2 = Technology(name="Tech2", region="DEU", year=2021, case="Base", detailed_technology="Wind", parameters={})
collection = TechnologyCollection(technologies=[tech1, tech2])

fitted_model = collection.fit(parameter="installed capacity", model=LinearGrowth(m=0.5, A=10))
```

### Projecting Parameters

```python
from technologydata import Technology, TechnologyCollection
from technologydata.technologies.growth_models import LinearGrowth

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

Please refer to the [API documentation](../api/technology_collection.md) for detailed information on the `TechnologyCollection` class methods and attributes.

## Notes

- **Filtering**: Regex patterns are case-insensitive and applied to non-optional attributes.
- **Export**: Default CSV export uses UTF-8 encoding and quotes all fields.
- **Schema**: JSON schema is generated automatically and includes field descriptions.
- **Type Checking**: The class uses Pydantic for validation and type enforcement.
- **Projection**: The 'closest' option for parameter projection is not yet implemented.
