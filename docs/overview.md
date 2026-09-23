# Overview

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

This page introduces the building blocks of `technologydata` in a few short steps: parameters, technologies, collections of technologies, the datasets that ship with the package, and data packages for saving and sharing data.
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

Compatible units are converted automatically, incompatible ones raise an error instead of returning a wrong number:

``` py
>>> print(capacity + Parameter(magnitude=500, units="kWh"))
100.5 megawatt_hour
>>> capacity + Parameter(magnitude=20, units="MW")
Traceback (most recent call last):
...
pint.errors.DimensionalityError: Cannot convert from 'megawatt_hour' ([mass] * [length] ** 2 / [time] ** 2) to 'megawatt' ([mass] * [length] ** 2 / [time] ** 3)
```

The same applies to different energy carriers or currencies.

More: carriers, heating values and all operations in the [Parameter guide](user_guide/parameter.md).

## 2. Technologies

A `Technology` groups the parameters of one technology for a region, a year and a case, e.g. a scenario or an estimate.

``` py
>>> from technologydata import Technology
>>> battery = Technology(
...     name="battery",
...     detailed_technology="utility-scale lithium-ion battery",
...     region="EU",
...     year=2030,
...     case="example",
...     parameters={
...         "specific_investment": specific_investment,
...         "capacity": capacity,
...         "lifetime": Parameter(magnitude=20, units="year"),
...     },
... )
>>> print(battery.parameters["lifetime"])
20 year
```

Many parameters are linked by equations, e.g. total investment = specific investment × capacity.
`calculate_parameters()` derives missing parameters from the ones a technology has, using the equations built into the package:

``` py
>>> battery = battery.calculate_parameters("total_investment_cost")
>>> print(battery.parameters["total_investment_cost"])
25000000.0 EUR_2020
```

The equations identify parameters by name (`specific_investment`, `capacity`, `total_investment_cost`, …).

More: all built-in equations and how to add your own in the [equation system guide](user_guide/equations.md).

## 3. Technology collections

### 3.1 Grouping technologies

A `TechnologyCollection` holds several technologies, e.g. the same technology in different years, or different technologies.
`get()` selects technologies by `name`, `detailed_technology`, `region`, `year` and `case`, and returns a new collection:

``` py
>>> from technologydata import TechnologyCollection
>>> battery_2040 = Technology(
...     name="battery",
...     detailed_technology="utility-scale lithium-ion battery",
...     region="EU",
...     year=2040,
...     case="example",
...     parameters={"specific_investment": Parameter(magnitude=200_000, units="EUR_2020/MWh")},
... )
>>> batteries = TechnologyCollection(technologies=[battery, battery_2040])
>>> print(batteries.get(year=2040)[0])
Technology('battery', region='EU', year=2040, case='example', 1 parameters: ['specific_investment'])
```

More: filtering with regular expressions and exporting to pandas, CSV and JSON in the [TechnologyCollection guide](user_guide/technology_collection.md).

### 3.2 Values from a bundled dataset

The package ships with parsed [datasets](datasets/index.md), each loaded as a collection of technologies.
The `DataAccessor` loads one by its key and version; here the [energy storage catalogue](datasets/dea_energy_storage.md) of the Danish Energy Agency (DEA).
We select utility-scale lithium-ion battery storage, using the DEA central estimate (`case="control"`), and read its lifetime and specific investment in 2030:

``` py
>>> from technologydata import DataAccessor
>>> dea = DataAccessor(data_source="dea_energy_storage", version="v10").load()
>>> dea_batteries = dea.technologies.get(name="lithium ion battery", case="control")
>>> print([t.year for t in dea_batteries])
[2025, 2030, 2035, 2040, 2050]
>>> dea_battery = dea_batteries.get(year=2030)[0]
>>> print(dea_battery.detailed_technology)
lithium-ion battery (utility-scale)
>>> print(dea_battery.parameters["technical lifetime"])
20.0 year
>>> print(dea_battery.parameters["specific investment"])
279000.0 EUR_2020 / megawatt_hour
```

Parameter names follow the dataset; the [fact sheet](datasets/dea_energy_storage.md) of each dataset lists all technologies and parameters.

More: loading options in the [DataAccessor guide](user_guide/data_accessor.md).

### 3.3 Projections with growth models

The DEA gives no value for 2045.
`project()` fits a growth model to a parameter across the years in a collection and returns the projected years as a new collection.
Here we use a linear model (`LinearGrowth`) to interpolate between `2040` and `2050` values in the DEA dataset:

``` py
>>> from technologydata.technologies.growth_models import LinearGrowth
>>> projected = dea_batteries.project(
...     to_years=[2045],
...     parameters={"specific investment": LinearGrowth()},
... )
>>> print(round(projected[0].parameters["specific investment"].magnitude))
305770
```

More models and functionality are available: exponential, logistic and other growth models in the [models guide](user_guide/models.md) and [projecting collections](user_guide/technology_collection.md#projecting-parameters).

## 4. Harmonising currencies and inflation

Values in different currencies or price years cannot be combined directly:

``` py
>>> investment + Parameter(magnitude=1_500_000, units="EUR_2024")
Traceback (most recent call last):
...
ValueError: Operation not permitted on parameters with different currencies or currency years: 'EUR_2020' and 'EUR_2024'. Use `to_currency` to convert to the same currency before performing the operation.
```

`to_currency()` converts to another currency and price year, adjusting for inflation with the deflator of the given country (ISO 3166 alpha-3 code).
(Note: The region `EU` is not a country, so we use Germany `= DEU` for inflation indicators:)

``` py
>>> dea_investment = dea_battery.parameters["specific investment"].to_currency("EUR_2024", country="DEU")
>>> print(round(dea_investment.magnitude), dea_investment.units)
335418 EUR_2024 / megawatt_hour
```

The inflation and exchange rate data (World Bank by default) is downloaded on first use and then cached so this operation is only slow upon first use.
This functionality is also available on `TechnologyCollections`, allowing for quick harmonisation across multiple technologies into one harmonised dataset.

The total investment of a fictitious 400 MWh project in 2024 prices is then:

``` py
>>> project_investment = dea_investment * Parameter(magnitude=400, units="MWh")
>>> print(f"{project_investment.magnitude / 1e6:.1f} million {project_investment.units}")
134.2 million EUR_2024
```

The result keeps the DEA catalogue as its source, so the number stays traceable; see the [Source guide](user_guide/source.md).

More: data sources and options for the conversion in the [Parameter guide](user_guide/parameter.md#currency-and-inflation-adjustment).

## 5. Consistency checks

`check_consistency()` uses standard or your custom equations to check that the parameters of a technology agree with each other.
The battery from section 2 is consistent; after changing its capacity, its total investment no longer matches and this error is highlighted:

``` py
>>> battery.check_consistency(parameters=["total_investment_cost"])
{'eac_simple': "missing parameters: ['eac']", 'total_investment_from_specific': True}
>>> battery.parameters["capacity"] = Parameter(magnitude=120, units="MWh")
>>> battery.check_consistency(parameters=["total_investment_cost"])
{'eac_simple': "missing parameters: ['eac']", 'total_investment_from_specific': False}
```

Equations that lack a parameter are reported as such rather than checked.

More: checking and deriving parameters in the [Technology guide](user_guide/technology.md#calculating-parameters-and-checking-consistency).

## 6. Data packages: saving and loading

A `DataPackage` bundles a collection of technologies with their sources under a name and a version; `DataAccessor.load()` returns one.
It follows the data schema of `technologydata`, the same format the bundled datasets are stored in, so your own packages can be shared and loaded the same way.
Here we store the DEA battery series as our own package:

``` py
>>> import pathlib, tempfile
>>> from technologydata import DataPackage
>>> package = DataPackage(name="my-batteries", version="v1", technologies=dea_batteries)
>>> package.get_source_collection()
>>> print(len(package.sources))
1
>>> folder = pathlib.Path(tempfile.mkdtemp())
>>> package.to_json(folder)
>>> print(sorted(p.name for p in folder.iterdir()))
['sources.json', 'technologies.json']
>>> reloaded = DataPackage.from_json("my-batteries", "v1", folder)
>>> print(reloaded.technologies.get(year=2030)[0].parameters["specific investment"])
279000.0 EUR_2020 / megawatt_hour
```

`get_source_collection()` collects the sources of all parameters into `package.sources`.
`to_csv()` writes the same content as CSV files for spreadsheets, and `TechnologyCollection.to_json(..., output_schema=True)` also writes the JSON schema describing the file format.

More: file formats and the JSON round trip in the [DataPackage guide](user_guide/datapackage.md).

## Next steps

- The [tutorial](tutorial/index.md) goes further: comparing two datasets and working with the equations in more detail.
- The [User Guide](user_guide/technology.md) and the [API Reference](api/technology.md) describe every class in detail.
