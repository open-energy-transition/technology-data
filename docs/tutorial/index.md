# Tutorial

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

This tutorial introduces the concepts of `technologydata` one at a time, and explains why each of them exists.
It builds one example from a single number up to a dataset you can save and share: the assumptions for a hydrogen electrolyser.
Basic Python (variables, function calls, dictionaries) is enough to follow along.
For a faster, code-first tour, see the [Overview](../overview.md).

The numbers used here are illustrative, not taken from a study.

## 1. Why `technologydata`?

Energy system models need many techno-economic assumptions: investment costs, efficiencies, lifetimes.
They come from studies and catalogues that each use their own units, currencies, price years and conventions.
In a spreadsheet these are plain numbers, and nothing stops you from:

- adding a capacity in MW to an energy in MWh;
- comparing a cost in 2020 euros with one in 2024 euros, as if there were no inflation;
- mixing hydrogen quantities on the lower and the higher heating value, which differ by about 18 %;
- losing track of which study a number came from.

Each of these mistakes silently produces a wrong result.
`technologydata` makes the context of a number (its unit, price year, energy carrier, heating value and source) part of the number itself.
Mistakes like the ones above then raise an error, and conversions between conventions are done for you.

## 2. Parameters: numbers with units

A single assumption is a `Parameter`: a value, called `magnitude`, and its `units`.
Our electrolyser costs 1,000 euros, in 2020 prices, per kilowatt of electric input:

``` py
>>> from technologydata import Parameter
>>> investment = Parameter(magnitude=1000, units="EUR_2020/kW")
>>> print(investment)
1000 EUR_2020 / kilowatt
```

The unit is understood, not just stored as text, so it can be converted:

``` py
>>> print(investment.to("EUR_2020/MW"))
1000000.0 EUR_2020 / megawatt
```

It also means that operations that make no physical sense are refused.
The capacity of the electrolyser is a power (MW); what it consumes over time is an energy (MWh).
The two are easily confused, and adding them is an error:

``` py
>>> capacity = Parameter(magnitude=10, units="MW")
>>> capacity + Parameter(magnitude=5, units="MWh")
Traceback (most recent call last):
...
pint.errors.DimensionalityError: Cannot convert from 'megawatt' ([mass] * [length] ** 2 / [time] ** 3) to 'megawatt_hour' ([mass] * [length] ** 2 / [time] ** 2)
```

An error at this point is much cheaper than a wrong number deep inside a model.
Units are handled by [pint](https://pint.readthedocs.io); the [Parameter guide](../user_guide/parameter.md) lists all operations.

## 3. Currencies and price years

A cost is only meaningful together with the year of its prices: because of inflation, 1,000 euros in 2020 bought more than 1,000 euros in 2024.
Studies report costs in different price years, so comparing them requires adjusting for inflation first.
In `technologydata` the price year is therefore part of the currency unit, e.g. `EUR_2020`, and costs in different price years cannot be combined by accident:

``` py
>>> investment + Parameter(magnitude=50, units="EUR_2024/kW")
Traceback (most recent call last):
...
ValueError: Operation not permitted on parameters with different currencies or currency years: 'EUR_2020 / kilowatt' and 'EUR_2024 / kilowatt'. Use `to_currency` to convert to the same currency before performing the operation.
```

`to_currency()` converts to another price year or currency.
It uses the inflation and exchange rates of a country, given as a three-letter ISO code, because inflation differs between countries:

``` py
>>> investment_2024 = investment.to_currency("EUR_2024", country="DEU")
>>> print(round(investment_2024.magnitude), investment_2024.units)
1202 EUR_2024 / kilowatt
```

With German inflation, the same electrolyser costs about 20 % more in 2024 euros; ignoring this would make it look cheaper than technologies costed in 2024 prices.
The rates come from the World Bank by default and are downloaded on first use.
More options are in the [Parameter guide](../user_guide/parameter.md#currency-and-inflation-adjustment).

## 4. Energy carriers and heating values

For energy, units alone are not enough: 1 MWh of electricity is not the same as 1 MWh of hydrogen.
Hydrogen can also be measured on two bases: the lower heating value (LHV) excludes the energy in the water vapour formed when it burns, the higher heating value (HHV) includes it.
Studies use both, so a `Parameter` can record its `carrier` and `heating_value`.

The efficiency of our electrolyser is 0.65 MWh of hydrogen (LHV) per MWh of electricity:

``` py
>>> efficiency = Parameter(magnitude=0.65, units="MWh/MWh", carrier="H2/el", heating_value="LHV")
>>> print(efficiency)
0.65 dimensionless, carrier=hydrogen / electricity, heating_value=lower_heating_value
```

The units cancel, but the carrier keeps what the ratio means.
Hydrogen quantities can be converted between heating values, and quantities on different bases cannot be added:

``` py
>>> hydrogen = Parameter(magnitude=650, units="MWh", carrier="H2", heating_value="LHV")
>>> hydrogen_hhv = hydrogen.change_heating_value("HHV")
>>> print(round(hydrogen_hhv.magnitude, 1), hydrogen_hhv.units)
767.5 megawatt_hour
>>> hydrogen + Parameter(magnitude=100, units="MWh", carrier="H2", heating_value="HHV")
Traceback (most recent call last):
...
ValueError: Operation not permitted on parameters with different heating values: 'lower_heating_value' and 'higher_heating_value'.
```

The same holds for different carriers, e.g. adding electricity to hydrogen.
See [handling different heating values](../user_guide/parameter.md#handling-different-heating-values) for the supported carriers.

## 5. Sources and provenance

A number without a source cannot be checked, cited or updated when a new study comes out.
A `Parameter` therefore carries `sources`, the references it comes from, and `provenance`, a record of how the value was obtained:

``` py
>>> from technologydata import Source, SourceCollection
>>> study = Source(title="Illustrative electrolyser assumptions", authors="technologydata tutorial")
>>> investment = Parameter(
...     magnitude=1000,
...     units="EUR_2020/kW",
...     sources=SourceCollection(sources=[study]),
...     provenance=["illustrative value for this tutorial"],
... )
>>> print(investment.to_currency("EUR_2024", country="DEU").sources)
SourceCollection with 1 sources: 'technologydata tutorial': 'Illustrative electrolyser assumptions'
```

The source stays attached through conversions and arithmetic, so a converted value can still be traced back to its study.
A `Source` can also hold a URL and be archived on the Wayback Machine, see the [Source guide](../user_guide/source.md).
Provenance information is tracked for some operations automatically - a feature that will be expanded in the future, such that all automatic transformations of `technoloydata` keep track of what has happened to a value.

## 6. Technologies

A model needs several parameters per technology, and needs to know exactly what they describe.
A `Technology` groups parameters with the fields that identify them:

- `name`: the short name used to find the technology;
- `detailed_technology`: the specific variant, e.g. PEM or alkaline electrolyser;
- `region`: where the values apply, since costs differ between countries;
- `year`: the year the values apply to, since costs of new technologies fall over time;
- `case`: the scenario or estimate, since catalogues often give a central estimate and a range.

``` py
>>> from technologydata import Technology
>>> electrolyser = Technology(
...     name="electrolyser",
...     detailed_technology="PEM electrolyser",
...     region="DEU",
...     year=2030,
...     case="illustrative",
...     parameters={
...         "specific_investment": investment,
...         "efficiency": efficiency,
...         "lifetime": Parameter(magnitude=25, units="year"),
...     },
... )
>>> print(electrolyser)
Technology('electrolyser', region='DEU', year=2030, case='illustrative', 3 parameters: ['specific_investment', 'efficiency', 'lifetime'])
>>> print(electrolyser.parameters["lifetime"])
25 year
```

More in the [Technology guide](../user_guide/technology.md).

## 7. Equations: deriving and checking parameters

Many parameters depend on each other: the total investment of a plant is its specific investment times its capacity.
Working these out by hand, in many places, is error-prone and leaves no record of how a value was obtained.
`technologydata` ships the common equations, and `calculate_parameters()` derives missing parameters from the ones a technology has.
The equations find parameters by name, which is why we used `specific_investment` above.
For a 10 MW electrolyser:

``` py
>>> electrolyser.parameters["capacity"] = Parameter(magnitude=10_000, units="kW")
>>> electrolyser = electrolyser.calculate_parameters("total_investment_cost")
>>> total = electrolyser.parameters["total_investment_cost"]
>>> print(total)
10000000.0 EUR_2020
>>> print(total.provenance[0])
Calculated from other parameters using formula 'total_investment_from_specific': total_investment_cost - specific_investment * capacity = 0
Input values:
  specific_investment = 1000 EUR_2020 / kilowatt
  capacity = 10000 kilowatt
```

The provenance records the formula and the input values, so the derived number can be reproduced.

The same equations can check values that are already there.
This helps with datasets that contain related values: if one of them was edited or copied wrongly, the check flags it.
After changing the capacity, the total investment no longer fits:

``` py
>>> electrolyser.check_consistency(parameters=["total_investment_cost"])
{'eac_simple': "missing parameters: ['eac']", 'total_investment_from_specific': True}
>>> electrolyser.parameters["capacity"] = Parameter(magnitude=20_000, units="kW")
>>> electrolyser.check_consistency(parameters=["total_investment_cost"])
{'eac_simple': "missing parameters: ['eac']", 'total_investment_from_specific': False}
```

Equations with a missing parameter are reported as such rather than checked.
The [equation system guide](../user_guide/equations.md) lists all equations and shows how to add your own.

## 8. Collections: several years

Assumptions change over time, and a model usually needs them for several years.
A `TechnologyCollection` holds several technologies, here the electrolyser in 2030, 2040 and 2050.
A small function saves us from repeating the identifying fields:

``` py
>>> from technologydata import TechnologyCollection
>>> def electrolyser_in(year, investment):
...     return Technology(
...         name="electrolyser",
...         detailed_technology="PEM electrolyser",
...         region="DEU",
...         year=year,
...         case="illustrative",
...         parameters={"specific_investment": Parameter(magnitude=investment, units="EUR_2020/kW")},
...     )
>>> electrolysers = TechnologyCollection(
...     technologies=[electrolyser, electrolyser_in(2040, 700), electrolyser_in(2050, 500)]
... )
>>> print(electrolysers.get(year=2040)[0].parameters["specific_investment"])
700 EUR_2020 / kilowatt
```

`get()` selects technologies by any of the identifying fields.
Most operations also work on a whole collection at once, e.g. `to_currency()` or `calculate_parameters()`.

A model may need a year the source does not cover.
`project()` fits a growth model to the years that are there and returns the requested years as a new collection:

``` py
>>> from technologydata.technologies.growth_models import LinearGrowth
>>> projected = electrolysers.project(
...     to_years=[2035],
...     parameters={"specific_investment": LinearGrowth(x0=2030)},
... )
>>> print(round(projected[0].parameters["specific_investment"].magnitude))
858
```

The straight line is fitted through all three years, so the 2035 value is not exactly halfway between 2030 and 2040.
Other growth models, e.g. exponential or logistic, are described in the [models guide](../user_guide/models.md).

## 9. Data packages: saving and sharing

Assumptions are reused across projects and exchanged between people and models, so they need a common file format.
A `DataPackage` bundles a collection with its sources under a name and a version, and writes it to files that follow the data schema of `technologydata`.
The version matters for reproducibility: it records which set of assumptions a model run used.

``` py
>>> import pathlib, tempfile
>>> from technologydata import DataPackage
>>> package = DataPackage(name="my-electrolyser-assumptions", version="v1", technologies=electrolysers)
>>> package.get_source_collection()
>>> folder = pathlib.Path(tempfile.mkdtemp())
>>> package.to_json(folder)
>>> print(sorted(p.name for p in folder.iterdir()))
['sources.json', 'technologies.json']
>>> reloaded = DataPackage.from_json("my-electrolyser-assumptions", "v1", folder)
>>> print(reloaded.technologies.get(year=2050)[0].parameters["specific_investment"])
500 EUR_2020 / kilowatt
```

`get_source_collection()` gathers the sources of all parameters into `package.sources`, e.g. for a bibliography.
`to_csv()` writes the same content as CSV for spreadsheets.
More in the [DataPackage guide](../user_guide/datapackage.md).

## 10. Batteries included - sharing encouraged

Building every assumption by hand does not scale.
`technologydata` therefore ships datasets parsed from published catalogues, and loading one gives the same kind of `DataPackage` you just built:

``` py
>>> from technologydata import DataAccessor
>>> dea = DataAccessor(data_source="dea_energy_storage", version="v10").load()
>>> print(dea.name, dea.version, len(dea.technologies))
dea_energy_storage v10 136
```

The [Datasets](../datasets/index.md) section describes each dataset, and the [Overview](../overview.md) shows how to work with one.
We welcome new datasets and additions - together we can build larger and better databases for technology data in energy system models!

## Where to go next

- [User Guide](../user_guide/parameter.md): every class in detail.
- [Datasets](../datasets/index.md): the bundled datasets, their contents and assumptions.
- [Equation system](../user_guide/equations.md): all built-in equations and how to add your own.
- [Use cases](../user_guide/design.md): the scenarios the package was designed around.
