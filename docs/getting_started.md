# Getting started

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

This page introduces the building blocks of `technologydata` in a few short steps: parameters, technologies, collections of technologies, and the datasets that ship with the package.
It assumes `technologydata` is [installed](./index.md#installation).

## 1. Parameters with units

A `Parameter` is a value with a unit.
Currencies are written as the currency code and the price year, e.g. `EUR_2020`.

``` py
>>> from technologydata import Parameter
>>> specific_investment = Parameter(magnitude=250_000, units="EUR_2020/MWh")
>>> capacity = Parameter(magnitude=100, units="MWh")
```

Calculations and conversions keep track of the units:

``` py
>>> investment = specific_investment * capacity
>>> print(investment)
25000000 EUR_2020
>>> print(specific_investment.to("EUR_2020/kWh"))
250.0 EUR_2020 / kilowatt_hour
>>> grid_connection = Parameter(magnitude=1_500_000, units="EUR_2020")
>>> print(investment + grid_connection)
26500000 EUR_2020
```

Adding parameters with incompatible units, currencies or energy carriers raises an error instead of returning a wrong number.

More: carriers and heating values, currency and inflation adjustment, all operations in the [Parameter guide](user_guide/parameter.md).

## 2. Technologies

A `Technology` groups the parameters of one technology for a region, a year and a case, e.g. a scenario or an estimate.

``` py
>>> from technologydata import Technology
>>> battery_2030 = Technology(
...     name="battery",
...     detailed_technology="utility-scale lithium-ion battery",
...     region="EU",
...     year=2030,
...     case="example",
...     parameters={
...         "specific investment": specific_investment,
...         "lifetime": Parameter(magnitude=20, units="year"),
...     },
... )
>>> print(battery_2030.parameters["lifetime"])
20 year
```

More: deriving missing parameters and checking their consistency in the [Technology guide](user_guide/technology.md).

## 3. Technology collections

A `TechnologyCollection` holds several technologies, e.g. the same technology in different years.
`get()` selects technologies by `name`, `detailed_technology`, `region`, `year` and `case`, and returns a new collection.

``` py
>>> from technologydata import TechnologyCollection
>>> battery_2040 = Technology(
...     name="battery",
...     detailed_technology="utility-scale lithium-ion battery",
...     region="EU",
...     year=2040,
...     case="example",
...     parameters={"specific investment": Parameter(magnitude=200_000, units="EUR_2020/MWh")},
... )
>>> batteries = TechnologyCollection(technologies=[battery_2030, battery_2040])
>>> print(batteries.get(year=2040)[0])
Technology('battery', region='EU', year=2040, case='example', 1 parameters: ['specific investment'])
```

More: filtering with regular expressions, export to pandas, CSV and JSON, and projecting parameters to other years in the [TechnologyCollection guide](user_guide/technology_collection.md).

## 4. Loading a bundled dataset

The package ships with parsed datasets.
The `DataAccessor` loads one by its key and version; here the energy storage catalogue of the Danish Energy Agency (DEA).
We select utility-scale lithium-ion battery storage in 2030, using the DEA central estimate (`case="control"`):

``` py
>>> from technologydata import DataAccessor
>>> dea = DataAccessor(data_source="dea_energy_storage", version="v10").load()
>>> battery = dea.technologies.get(name="lithium ion battery", year=2030, case="control")[0]
>>> print(battery.detailed_technology)
lithium-ion battery (utility-scale)
>>> print(battery.parameters["technical lifetime"])
20.0 year
>>> print(battery.parameters["specific investment"])
279000.0 EUR_2020 / megawatt_hour
```

More: all technologies, parameters and parsing choices of this dataset in its [fact sheet](datasets/dea_energy_storage.md), other datasets under [Datasets](datasets/index.md), and loading options in the [DataAccessor guide](user_guide/data_accessor.md).

## 5. Calculating a project's investment

With the specific investment from the DEA, the total investment of a fictitious 400 MWh battery project is:

``` py
>>> project_capacity = Parameter(magnitude=400, units="MWh")
>>> project_investment = battery.parameters["specific investment"] * project_capacity
>>> print(project_investment)
111600000.0 EUR_2020
```

The result keeps the DEA catalogue as its source, so the number stays traceable.

More: converting the result to another currency or price year with `to_currency()` in the [Parameter guide](user_guide/parameter.md#currency-and-inflation-adjustment), and source tracking in the [Source guide](user_guide/source.md).

## Next steps

- The [tutorial](tutorial/index.md) goes further: comparing two datasets, saving your own data, deriving parameters and projecting them into the future.
- The [User Guide](user_guide/technology.md) and the [API Reference](api/technology.md) describe every class in detail.
