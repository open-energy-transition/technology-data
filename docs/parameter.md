# `Parameter` Class Documentation

## Overview

The `Parameter` class in `technologydata` encapsulates a value, its unit, provenance, notes, sources, and additional attributes required to describe technology parameters, such as carrier and heating value. It is designed for use in energy system modeling workflows, supporting unit handling, currency/inflation adjustments, and provenance tracking.

## Features

- **Value and Units**: Stores a numerical value (`magnitude`) and its associated units (`units`). Units are handled using `pint` and support custom currency units (e.g., `USD_2020/kW`).
- **Currency Unit Convention**: Currency units must follow the pattern `XYZ_YYYY`, where `XYZ` is the 3-letter [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) currency code (e.g., `USD`, `EUR`, `CNY`) and `YYYY` is the 4-digit year (e.g., `USD_2020`). This allows for both currency and inflation adjustment.
- **Carrier and Heating Value**: Optionally specify an energy carrier (e.g., `H2`) and a heating value type (`LHV` or `HHV`).
- **Provenance and Notes**: Track the origin of the data and any additional notes.
- **Sources**: Attach a `SourceCollection` of references for traceability.
- **Unit Conversion**: Convert between compatible units (excluding currency conversion) using `.to()`.
- **Currency/Inflation Adjustment**: Convert between currencies and adjust for inflation using `.change_currency()`.
- **Arithmetic Operations**: Supports addition, subtraction, multiplication, and division with other `Parameter` objects, with compatibility checks for carrier and heating value. **Note:** Some operations will fail if heating values or carriers are incompatible, raising a `ValueError`.

## Usage Examples

### Creating a Parameter

```python
from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.source_collection import SourceCollection

param = Parameter(
    magnitude=1000,
    units="USD_2020/kW",
    carrier="H2",
    heating_value="LHV",
    provenance="Directly extracted from literature",
    note="Estimated",
    sources=SourceCollection(sources=[
        Source(name="Example Source", authors="some authors", title="Example Title")
    ]),
)

>>> param
Parameter(magnitude=1000.0, units='USD_2020/kW', carrier='H2', heating_value='LHV', provenance='literature', note='Estimated', sources=SourceCollection(sources=[Source(name='Example Source', authors='some authors', title='Example Title')]))
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
euro_param = param.change_currency("EUR_2023", "DEU", source="worldbank")
>>> print(euro_param.magnitude, euro_param.units)
950.0 EUR_2023 / kilowatt
```

### Arithmetic Operations

```python
param2 = Parameter(magnitude=500, units="USD_2020/kW", carrier="H2", heating_value="LHV")
sum_param = param + param2
>>> print(sum_param.magnitude, sum_param.units)
1500.0 USD_2020 / kilowatt
```

**Note:** If you try to add or subtract parameters with different carriers or heating values, a `ValueError` will be raised:

```python
param_hhv = Parameter(magnitude=1, units="USD_2020/kW", carrier="H2", heating_value="HHV")
param + param_hhv
>>> # ValueError: Cannot add parameters with different heating values
```

## Notes on Currency Conversion and pydeflate

- **pydeflate Integration**: Currency and inflation adjustments are performed using the `pydeflate` package. This package uses data from either the World Bank or the International Monetary Fund. In order to use `pydeflate` with currency codes, we make some opinioated assumptions about the mapping from currency codes to countries which should in most cases be correct, but may not always be accurate for all currencies or years.
- **Country Mapping**: To see which country was used for a given currency code during conversion, inspect the mapping in `pydeflate` or use the helper functions in `technologydata.utils.units` (e.g., `get_iso3_from_currency_code`). The country code you provide to `.change_currency()` determines the inflation adjustment, but the mapping from currency code to country is handled internally by pydeflate and may be checked in its documentation or by printing the mapping used in your environment.
- **Data availability**: Since we use World Bank or IMF data, the availability of currency conversion data may vary by year and currency, depending on the most recent publication. World Bank data is based on the [World Bank DataBank](https://databank.worldbank.org/home.aspx) and IMF data is based on the [World Economic Outlook](https://www.imf.org/en/Publications/WEO). If IMF data is used, this means that also short-term projections can be accessed, usually e.g. GDP deflators for up to 2 years into the future.
- **Updating Data**: If `pydeflate` notices that data is older than 50 days, it will display a warning. It will also periodically try to update the data automatically. More information on how to configure the update behaviour and caching locations for `pydeflate` are available in their [documentation](https://github.com/jm-rivera/pydeflate).

## Limitations & Missing Features

- **Provenance/Note/Sources in Arithmetic**: When performing arithmetic operations, the handling and merging of `provenance`, `note`, and `sources` is not yet implemented (see `TODO` comments in the code).
- **Unit Conversion**: The `.to()` method does not support currency conversion; use `.change_currency()` for that.
- **Partial Unit Compatibility**: Only certain combinations of units, carriers, and heating values are supported for arithmetic operations.
- **No Uncertainty Handling**: There is currently no support for uncertainty or error propagation.
- **No Serialization/Deserialization**: Direct methods for exporting/importing to/from JSON or DataFrame are not implemented in this class.