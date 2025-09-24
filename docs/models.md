# Title

<!--
SPDX-FileCopyrightText: 2025 The technology-data authors

SPDX-License-Identifier: MIT

-->

## Models

Different models can be used to modify assumptions to fit specific scenarios.

## Supported Model Types

- **Growth models**: For projecting technology parameters forward in time using mathematical models.

These are implemented as Python classes and can be used for fitting to data and making projections.

## Growth Models

Growth models are mathematical models for projecting technology parameters over time. They are implemented as Pydantic classes in `technologydata.technologies.growth_models` and can be used for both fitting to data and making projections. The following growth models are available:

### Available Growth Models

- `LinearGrowth`: Linear model, $f(x) = m \cdot (x - x_0) + c$
- `ExponentialGrowth`: Exponential model, $f(x) = A \cdot \exp(k \cdot (x - x_0))$
- `LogisticGrowth`: Logistic (sigmoid) model, $f(x) = \frac{L}{1 + \exp(-k \cdot (x - x_0))}$
- `GeneralLogisticGrowth`: Generalized logistic model, $f(x) = A + \frac{K - A}{(C + Q \cdot \exp(-B \cdot (x - x_0)))^{1/\nu}}$
- `GompertzGrowth`: Gompertz model, $f(x) = A \cdot \exp(-b \cdot \exp(-k \cdot (x - x_0)))$

Each model exposes:

- A `function(x, ...)` method for the mathematical form
- A `fit()` method to fit parameters to data points
- A `project(to_year)` method to project to a given year (once parameters are set)
- Data points can be added via `add_data((x, y))`

#### Example: Fitting and Projecting

```python
from technologydata.technologies.growth_models import LinearGrowth
model = LinearGrowth(m=None, c=None, data_points=[(2020, 100), (2025, 200)])
model.fit()
value_2030 = model.project(2030)
```

#### Model Parameters

Each model has its own parameters (e.g., `m`, `c` for linear; `A`, `k`, `x0` for exponential, etc.). These must be provided or fitted before projection.

#### Integration with Technology and TechnologyCollection

Currently, growth models are **not directly integrated** with the `Technology` or `TechnologyCollection` classes. You must use the models independently and apply projections manually to technology parameters. Future versions may provide tighter integration and batch projection utilities.

### Example: Fitting and Projecting

```python
from technologydata.technologies.growth_models import ExponentialGrowth
import numpy as np
x = np.array([2020, 2025, 2030])
y = 100 * np.exp(0.1 * (x - 2020))
model = ExponentialGrowth(A=None, k=None, x0=2020, data_points=list(zip(x, y)))
model.fit()
print(model.project(2040))
```

### Model API

- `add_data((x, y))`: Add a data point for fitting
- `fit()`: Fit model parameters to data
- `project(to_year)`: Project to a given year (parameters must be set)

See the Python docstrings for each model for parameter details.
