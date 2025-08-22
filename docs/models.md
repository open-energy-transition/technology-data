<!--
SPDX-FileCopyrightText: 2025 The technology-data authors

SPDX-License-Identifier: MIT
-->

# Models

Different models can be used to modify assumptions to fit specific scenarios.
The following types of models are currently supported:

* Growth models: Models that allow to create projections forward in time.

## Growth Models

These models are used to project technology parameters forward in time.
All models take the following arguments:

* `affected_parameters`: List of parameters to be affected by the growth model.
* `to_years`: List of years to which the growth model should be applied.

In addition, each model has its own specific parameters that affect the models behavior.

The models can either be instantiated independently and reused, or be directly used through a method that accepts a dictionary of model parameters.
This allows for easy integration with e.g. `yaml` files, or reuse of model definitions across multiple technologies or inside a package.

The models always take a single `Technology` object that is used as input,
and return a `TechnologyCollection` object that contains the original technology as well as the projected technologies to the specified `to_years` to project to.

### Example Usage

```python
# Create an example technology
from technologydata.technology import Technology
from technologydata.parameter import Parameter
tech = Technology(
    name="Zero Emission Vehicle",
    detailed_technology="Battery Electric Vehicle",
    region="EU",
    case="default",
    year=2020,
    parameters={
        "total units": Parameter(magnitude=1000),
        "lifetime": Parameter(magnitude=10, unit="years"),
        "battery capacity": Parameter(magnitude=50, unit="kWh"),
    }
)

# There are three ways to create projections with growth models for this technology:

# 1. Through a method call, where you specify the model name and its parameters
from technologydata.technologies.growth_models import project_with_model
project_with_model(
    tech,
    model="LinearGrowth", # acceptable alias: "linear"
    annual_growth_rate=0.05,
    affected_parameters=["total units", "battery capacity"],
    to_years=[2025, 2030],
)

# 2. Instantiate a model and use its project method
# Setup the growth model
# we use a simple linear growth model here, that
# affects the parameters:
# * total units
# * battery capacity
#
# with an annual growth rate of 5% and creates projections for 2025 and 2030.
from technologydata.technologies.growth_models import LinearGrowth
linear_growth = LinearGrowth(
    annual_growth_rate=0.05,
    affected_parameters=["total units", "battery capacity"],
    to_years=[2025, "2030"],
)

# Now apply the model to the technology
projected_techs = linear_growth.project(tech)

# 3. With an instantiated model, you can also use the same method as in (1)
# or for convinience, the same method also accepts a model instance:
project_with_model(
    tech, model=linear_growth
)
```

### Linear Growth

A linear growth model that increases the affected parameters by a fixed annual growth rate.
For a parameter $P$ at the base year $Y_0$, the projected year $Y$ is calculated with the annual growth rate $r$ as:
$$P(Y) = P(Y_0) \cdot \left[1 + r \cdot (Y - Y_0)\right]$$

