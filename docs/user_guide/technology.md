# `Technology` Class Documentation

## Overview

The `Technology` class in `technologydata` represents a single technology, including its region, year, scenario, and a flexible set of parameters. It provides methods for accessing, modifying, and transforming technology parameters, as well as for currency adjustment and scaling.

## Features

- **Flexible Parameter Storage**: Stores technology parameters as a dictionary mapping names to `Parameter` objects.
- **Region, Year, and Scenario**: Tracks metadata for each technology, including `region`, `year`, `case`, and `detailed technology` name.
- **Parameter Access**: Supports dictionary-like access and assignment for parameters.
- **Consistency Checking**: Checks for completeness and consistency of required parameters.
- **Parameter Calculation**: Placeholder for calculating missing or derived parameters.
- **Currency Adjustment**: Harmonizes all technology parameters to a target currency, including inflation and exchange rates.
- **Region and Scale Adjustment**: Placeholder methods for adjusting technology parameters to a different region or scaling values.

## Usage Examples

### Creating a Technology

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "lifetime": Parameter(magnitude=25, units="year"),
    }
)
```

### Accessing and Setting Parameters

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "lifetime": Parameter(magnitude=25, units="year"),
    }
)

# Access a parameter
investment = tech["specific_investment"]

# Set a parameter
tech["efficiency"] = Parameter(magnitude=0.18, units=None)
```

### Checking Consistency

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "lifetime": Parameter(magnitude=25, units="year"),
    }
)

is_consistent = tech.check_consistency()
print(is_consistent)  # True if all required parameters are present
```

### Adjusting Currency

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "lifetime": Parameter(magnitude=25, units="year"),
    }
)

converted_tech = tech.to_currency("USD_2025", source="worldbank")
```

### Scaling Parameters

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "lifetime": Parameter(magnitude=25, units="year"),
    }
)

scaled_tech = tech.adjust_scale(1.1)
```

## API Reference

Please refer to the [API documentation](../api/technology.md) for detailed information on the `Technology` class methods and attributes.

### Calculating Derived Parameters

Use the formula registry to automatically derive missing parameters. See
[Formula System](formulas.md) for the full reference.

```python
from technologydata.technology import Technology
from technologydata.parameter import Parameter

tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1000, units="EUR_2020/kW"),
        "wacc":                Parameter(magnitude=0.06, units="dimensionless"),
        "lifetime":            Parameter(magnitude=25,   units="year"),
    }
)

# Derive EAC automatically
tech_derived = tech.calculate_parameters("eac")

# Derive all derivable parameters at once
tech_full = tech.calculate_parameters()
```
