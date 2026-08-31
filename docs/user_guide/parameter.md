# `Parameter` Class Documentation

## Overview

The `Parameter` class in `technologydata` encapsulates a value, its unit, provenance, notes, sources, and additional attributes required to describe technology parameters, such as carrier and heating value. It is designed for use in energy system modeling workflows, supporting unit handling, currency/inflation adjustments, and provenance tracking.

## Features

- **Value and Units**: Stores a numerical value (`magnitude`) and its associated units (`units`). Units are handled using `pint` and support custom currency units (e.g., `USD_2020/kW`). The [pint default units definition](https://github.com/hgrecco/pint/blob/master/pint/default_en.txt) file is available for reference. Be mindful of false unit-friends, e.g. `t = metric_ton = tonne != ton = US_ton`
- **Currency Unit Convention**: Currency units must follow the pattern `XYZ_YYYY`, where `XYZ` is the 3-letter [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) currency code (e.g., `USD`, `EUR`, `CNY`) and `YYYY` is the 4-digit year (e.g., `USD_2020`). This allows for both currency and inflation adjustments.
- **Carrier and Heating Value**: Optionally specify an energy carrier (e.g., `H2`) and a heating value type (`LHV` or `HHV`).
- **Provenance and Notes**: Track the origin of the data and any additional notes.
- **Sources**: Attach a `SourceCollection` of references for traceability.
- **Unit Conversion**: Convert between compatible units (excluding currency conversion) using `.to()`.
- **Currency/Inflation Adjustment**: Convert between currencies and adjust for inflation using `.to_currency()`.
- **Arithmetic Operations**: Supports addition, subtraction, multiplication, and division with other `Parameter` objects, with compatibility checks for carrier and heating value. **Note:** Some operations will fail if heating values or carriers are incompatible, raising a `ValueError`.

## Usage Examples

### Creating a Parameter

```python
from technologydata import Parameter, Source, SourceCollection

param = Parameter(
    magnitude=1000,
    units="USD_2020/kW",
    carrier="H2",
    heating_value="LHV",
    provenance="Directly extracted from literature",
    note="Estimated",
    sources=SourceCollection(sources=[
        Source(title="Example Title", authors="some authors")
    ]),
)

>>> param
Parameter(magnitude=1000.0, units='USD_2020/kW', carrier='H2', heating_value='LHV', provenance='literature', note='Estimated', sources=SourceCollection(sources=[Source(title='Example Title', authors='some authors', )]))
```

### Unit Conversion (excluding currency)

```python
converted = param.to("USD_2020 / megawatt")
>>> print(converted.magnitude, converted.units)
1000000.0 USD_2020 / megawatt
```

### Currency and Inflation Adjustment

```python
# Convert to EUR_2023 with inflation adjustment for Germany, using World Bank data
euro_param = param.to_currency("EUR_2023", "DEU", source="worldbank")
>>> print(euro_param.magnitude, euro_param.units)
950.0 EUR_2023 / kilowatt
```

Currency conversion and inflation adjustment are also available for `Technology` and `TechnologyCollection` objects. This allows to quickly adjust and harmonise the currency of all parameters in a technology or collection.

```python
# for a Technology
from technologydata import Technology
tech = Technology(
    name="Example Tech",
    detailed_technology="Detailed Example Tech",
    case="Scenario",
    region="DEU",
    year="2020",
    parameters={"cost": param}
)
converted_tech = tech.to_currency("USD_2020", source="worldbank")
>>> print(converted_tech.parameters["cost"].units)
USD_2020 / kilowatt

# and for a TechnologyCollection
from technologydata import TechnologyCollection
tech_collection = TechnologyCollection(technologies=[tech])
converted_collection = tech_collection.to_currency("USD_2020", source="worldbank")
>>> print(converted_collection.technologies[0].parameters["cost"].units)
USD_2020 / kilowatt
```

Compared to the `to_currency()` method of the `Parameter` class, the `to_currency()` methods of `Technology` and `TechnologyCollection` do not require specifying a country for inflation adjustment.
By default, the `region` field of the `Technology` object or the `Technology` objects in the `TechnologyCollection` are used for inflation adjustment.
If the value of the `region` field should not be used or is not suitable, because e.g. it is not a valid ISO 3166 alpha-3 country code, the optional `overwrite_country` argument can be used to specify a different country code for inflation adjustment.

```python
>>> print(tech.region)
DEU
converted_tech = tech.to_currency("USD_2020")  # uses tech.region (DEU) for inflation adjustment

converted_tech = tech.to_currency("USD_2020", overwrite_country="FRA")  # uses FRA for inflation adjustment
>>> print(converted_tech.region) # the region remains unchanged
DEU
```

### Arithmetic Operations

```python
from technologydata import Parameter

param2 = Parameter(magnitude=500, units="USD_2020/kW", carrier="H2", heating_value="LHV")
sum_param = param + param2
>>> print(sum_param.magnitude, sum_param.units)
1500.0 USD_2020 / kilowatt
```

**Note:** If you try to add or subtract parameters with different carriers or heating values, a `ValueError` will be raised:

```python
from technologydata import Parameter

param_hhv = Parameter(magnitude=1, units="USD_2020/kW", carrier="H2", heating_value="HHV")
param + param_hhv
>>> # ValueError: Cannot add parameters with different heating values
```

### Working with Series Data

The `Parameter` class also supports using pandas Series or lists as the `magnitude` value, allowing you to work with time series or multiple scenarios simultaneously:

```python
import pandas as pd
from technologydata.parameter import Parameter

# Create a parameter with time series data
years = pd.Series([2020, 2025, 2030, 2035, 2040])
costs = pd.Series([1000, 800, 600, 400, 300], index=years)

param_series = Parameter(
    magnitude=costs,
    units="USD_2020/kW",
    carrier="H2",
    heating_value="LHV",
    provenance="Cost projection",
    note="Declining costs over time"
)

>>> print(param_series.magnitude)
2020    1000
2025     800
2030     600
2035     400
2040     300
dtype: int64

# Unit conversion preserves the series structure
converted_series = param_series.to("EUR_2020/MW")
>>> print(converted_series.magnitude)
2020    1000000.0
2025     800000.0
2030     600000.0
2035     400000.0
2040     300000.0
dtype: float64

# Arithmetic operations work element-wise with scalars
multiplier = 1.25  # Simple scalar multiplication
adjusted_costs = param_series * multiplier
>>> print(adjusted_costs.magnitude)
2020    1250.0
2025    1000.0
2030     750.0
2035     500.0
2040     375.0

# You can also use lists instead of pandas Series
param_list = Parameter(
    magnitude=[100, 200, 300],
    units="kW",
    note="List-based data"
)
>>> print(param_list.magnitude)
[100, 200, 300]

# Operations between series and scalar parameters
base_load = Parameter(magnitude=50, units="kW")
total_load = param_list + base_load
>>> print(total_load.magnitude)
0    150
1    250
2    350
dtype: int64
```

**Series Features:**

- **Index Preservation**: When using pandas Series, the index is preserved through arithmetic operations and conversions
- **Element-wise Operations**: All arithmetic operations (`+`, `-`, `*`, `/`, `**`) work element-wise on series data
- **Mixed Operations**: You can perform operations between series and scalar parameters
- **Currency Conversion**: Currency conversion works on all elements of a series
- **Heating Value Conversion**: Heating value changes are applied to all elements in a series

## Notes on Currency Conversion and pydeflate

- **pydeflate Integration**: Currency and inflation adjustments are performed using the `pydeflate` package. This package uses data from either the World Bank or the International Monetary Fund. In order to use `pydeflate` with currency codes, we make some opinioated assumptions about the mapping from currency codes to countries which should in most cases be correct, but may not always be accurate for all currencies or years.
- **Country Mapping**: To see which country was used for a given currency code during conversion, inspect the mapping in `pydeflate` or use the helper functions in `technologydata.utils.units` (e.g., `get_iso3_from_currency_code`). The country code you provide to `.to_currency()` determines the inflation adjustment, but the mapping from currency code to country is handled internally by pydeflate and may be checked in its documentation or by printing the mapping used in your environment.
- **Data availability**: Since we use World Bank or IMF data, the availability of currency conversion data may vary by year and currency, depending on the most recent publication. World Bank data is based on the [World Bank DataBank](https://databank.worldbank.org/home.aspx) and IMF data is based on the [World Economic Outlook](https://www.imf.org/en/Publications/WEO). If IMF data is used, this means that also short-term projections can be accessed, usually e.g. GDP deflators for up to 2 years into the future.
- **Updating Data**: If `pydeflate` notices that data is older than 50 days, it will display a warning. It will also periodically try to update the data automatically. More information on how to configure the update behaviour and caching locations for `pydeflate` are available in their [documentation](https://github.com/jm-rivera/pydeflate).

## Handling different heating values

Each `Parameter` can have a `heating_value` attribute, which can be either `LHV` (or allowed aliases like `lower_heating_value`, 'NCV', 'net_calorific_value') or `HHV` (or allowed aliases like `higher_heating_value`, 'GCV', 'gross_calorific_value').
This attribute indicates the basis on which the energy content of the parameter is defined.
In operations between `Parameter` objects, the heating value is checked.
Only parameters with the same heating value can be used in arithmetic operations.

The heating value can be changed using the `change_heating_value` method, which uses the `carrier` attribute of the `Parameter` to determine the conversion factor between LHV and HHV based on their energy densities.

- **Supported Carriers:** The method currently supports conversion for common carriers such as hydrogen and methane. For any other carrier that is not implemented, a ratio of 1 is assumed.
- **Adding Carriers:** New carriers can be added programmatically by extending the `EnergyDensityLHV` and `EnergyDensityHHV` dictionaries in `technologydata.constants`. The LHV/HHV ratio is calculated based on these two dictionaries, so any new carrier must have both LHV and HHV energy densities defined. In addition, the carrier name must be a valid dimensionality defined in `technologydata.utils.units.creg`.

### Example: Converting Between LHV and HHV

```python
from technologydata import Parameter

# Create a parameter on LHV basis
param_lhv = Parameter(magnitude=33.33, units="kWh/kg", carrier="hydrogen", heating_value="LHV")
>>> print(param_lhv.magnitude, param_lhv.units, param_lhv.heating_value)
33.33 kWh/kg lower_heating_value

# Convert to HHV basis
param_hhv = param_lhv.change_heating_value("HHV")
>>> print(param_hhv.magnitude, param_hhv.units, param_hhv.heating_value)
39.51 kWh/kg higher_heating_value

# Convert back to LHV
param_lhv2 = param_hhv.change_heating_value("LHV")
>>> print(param_lhv2.magnitude, param_lhv2.units, param_lhv2.heating_value)
33.33 kWh/kg lower_heating_value

# On mixed carriers
param_mixed = Parameter(magnitude=1/9, units="kWh/kg", carrier="hydrogen / water", heating_value="LHV")
param_mixed_hhv = param_mixed.change_heating_value("HHV")
>>> print(param_mixed_hhv.magnitude, param_mixed_hhv.units, param_mixed_hhv.heating_value)
0.13 kWh/kg higher_heating_value
```

## API Reference

Please refer to the [API documentation](../api/parameter.md) for detailed information on the `Parameter` class methods and attributes.

## Notes

- **Provenance/Note/Sources in Arithmetic**: When performing arithmetic operations, the handling and merging of `provenance`, `note`, and `sources` is not yet implemented (see `TODO` comments in the code).
- **Unit Conversion**: The `.to()` method does not support currency conversion; use `.to_currency()` for that.
- **Partial Unit Compatibility**: Only certain combinations of units, carriers, and heating values are supported for arithmetic operations.
- **No Uncertainty Handling**: There is currently no support for uncertainty or error propagation.
- **No Serialization/Deserialization**: Direct methods for exporting/importing to/from JSON or DataFrame are not implemented in this class.
- **Series Index Alignment**: When performing operations between two series parameters with different indices, the result uses the index from the longer series. More sophisticated index alignment is not currently implemented.
- **Mixed Series Types**: Operations between pandas Series and plain Python lists convert the list to a Series, which may not preserve intended semantics in all cases.
