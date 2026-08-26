# `Technology` Class Documentation

## Overview

The `Technology` class in `technologydata` represents a single technology, including its region, year, scenario, and a flexible set of parameters. It provides methods for accessing, modifying, and transforming technology parameters, as well as for currency adjustment and scaling.

## Features

- **Flexible Parameter Storage**: Stores technology parameters as a dictionary mapping names to `Parameter` objects.
- **Region, Year, and Scenario**: Tracks metadata for each technology, including `region`, `year`, `case`, and `detailed technology` name.
- **Parameter Access**: Supports dictionary-like access and assignment for parameters.
- **Consistency Checking**: Checks selected parameters against registered
    equations and returns a per-equation status dictionary.
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

### Calculating Parameters and checking consistency

Parameters of a `Technology` can be related to each other and derived through known equations.
A good example are total capacity, total investment costs and specific investment costs, where the specific costs are just the total costs divided by the total capacity.

Instead of manually writing out the equation each time and calculating the parameters manually, you can add equations that related parameters to each other and then have `technologydata` calculate missing parameters automatically.

`technologydata` can also use the equations to check whether existing parameters are consistent with each other, i.e. whether they fulfill the relationship described by the equations.

Let's take a look at an example:

```python
from technologydata import Technology, Parameter, equation_registry

print(equation_registry.list_equations())
```

The `equation_registry` contains the equations that you can work with.
Some equations are provided by default and you can modify the registry to suit your needs, remove or add equations, or load your own registry from a `yaml` file all together.

Starting with our known technology:

```python
tech = Technology(
    name="Solar PV",
    detailed_technology="Crystalline Silicon",
    case="Base",
    region="DEU",
    year=2020,
    parameters={
        "specific_investment": Parameter(magnitude=1, units="EUR_2020/kW"),
        "total_investment": Parameter(magnitude=1_000, units="EUR_2020"),
    }
)
```

Let's calculate the `capacity` for this installation:

```python
tech = tech.calculate("capacity")
tech.parameters["capacity"]
# 1000 kW
```

The calculate parameter is automatically added to the technology object.

We can check whether the parameters of the Technology object are consistent with the equations.
In this case we have derived one parameter using the other two, so they should be consistent:

```python
status = tech.check_consistency()
print(status)
# {
#   "total_investment_from_specific": True,
#   ...
# }
```

The consistency check will flag equations that are consistent with the parameters of the technology with `True` and those that aren't with `False`.
It will check against all the equations in the registry.
If there are equations for which only some but not all parameters are present, it will notify about these equations as `"missing parameters"` and equations for which no parameter is present will be labelled as `"inapplicable"`.
If we change the value of one of the parameters to be inconsistent with the others, e.g.

```python
tech.parameters["capacity"].magnitude = 5

# Check for consistency again
status = tech.check_consistency()
print(status)
# {
#   "total_investment_from_specific": False,
#   ...
# }
```

The inconsistency will be reported and flagged.
Since it is not possible to determine which parameters are right or wrong, it will not highlight a specific parameter as "inconsistent".

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
