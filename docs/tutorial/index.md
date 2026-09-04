# Tutorial

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

This tutorial walks through the features of `technologydata` and how to use them.
It shows how to use `Parameter` and `Technology` objects, use the functionalities of the package, and combine them into a packaged data follow our data schema (a `DataPackage`).
All manual steps are shown, as well as how to utilise some pre-parsed and packaged data from the Danish Energy Agency.

## Who this package is for

Techno-economic data is central to energy system models.
They usually utilise data catalogues that are published in different currencies, price years, units, heating-value conventions and naming schemes.
Comparing, combining and harmonising them means making these changes and tracking them all by hand - a highly repetitive and error-prone process.

This is where `technologydata` is meant to support you.
It helps to:

- combine assumptions from more than one source, or from a source and your own numbers;
- convert between currencies, price years and units without losing track of what was converted;
- keep a record of where each number came from and how it was calculated
- supports through an equation system derived parameters and consistency checks
- provides common models for scenario interpolation and projection

## 1. A parameter that knows its units

The smallest useful object is a `Parameter`: a magnitude, a unit, and the source it came from.

``` py
>>> from technologydata import Parameter, Source, SourceCollection
>>> sources = SourceCollection(sources=[Source(
...     title="Technology Data for Energy storage (May 2025)",
...     authors="Danish Energy Agency",
...     url="https://ens.dk/media/6589/download",
... )])
>>> investment = Parameter(magnitude=288000.0, units="EUR_2020/MWh", sources=sources)
>>> print(investment.magnitude, investment.units)
288000.0 EUR_2020 / megawatt_hour
```

The unit string is parsed rather than stored verbatim, which is why `EUR_2020/MWh` comes back as `EUR_2020 / megawatt_hour`. A currency is written as a three-letter code, an underscore and the price year — `EUR_2020`, `USD_2022`. Prefixed forms such as `MEUR_2020` are **not** units the registry knows; scale the magnitude instead.

Because the unit is real, the parameter can be converted:

``` py
>>> per_kwh = investment.to("EUR_2020/kWh")
>>> print(per_kwh.magnitude, per_kwh.units)
288.0 EUR_2020 / kilowatt_hour
```

## 2. From parameter to data package

A `Technology` groups parameters that describe the same thing in the same year and case. A `TechnologyCollection` holds many of those, and a `DataPackage` pairs a collection with its sources.

``` py
>>> from technologydata import DataPackage, Technology, TechnologyCollection
>>> battery = Technology(
...     name="lithium ion battery",
...     detailed_technology="lithium-ion battery (utility-scale)",
...     region="EU",
...     year=2025,
...     case="control",
...     parameters={"specific investment": investment},
... )
>>> package = DataPackage(
...     name="my-assumptions",
...     version="v1",
...     technologies=TechnologyCollection(technologies=[battery]),
...     sources=sources,
... )
>>> print(package.name, package.version, len(package.technologies.technologies))
my-assumptions v1 1
```

`DataPackage` requires a `name` and a `version` as well as the data — they are what `from_json()` uses to identify the package later.

## 3. Load a published catalogue

Writing technologies by hand does not scale. The package ships two parsed catalogues, which load the same way and give you the same `TechnologyCollection` type you just built.

``` py
>>> import pathlib
>>> from technologydata import DataAccessor
>>> dea = DataAccessor(data_source="dea_energy_storage", version="v10").load()
>>> usa = DataAccessor(data_source="manual_input_usa", version="v0.13.4").load()
>>> print(len(dea.technologies.technologies), len(usa.technologies.technologies))
136 85
```

## 4. Select one technology

`TechnologyCollection.get()` filters on five attributes and returns a new collection.

!!! warning "`get()` matches regular expressions, not literal text"
    Every argument is compiled as a regex, so `(` and `)` are read as a group rather than as brackets. A name containing them silently matches nothing. Pass it through `re.escape()`.

``` py
>>> import re
>>> selected = dea.technologies.get(
...     name="lithium ion battery",
...     region="EU",
...     year=2030,
...     case="control",
...     detailed_technology=re.escape("lithium-ion battery (utility-scale)"),
... )
>>> print(len(selected.technologies))
1
```

Without `re.escape()` the same call returns an empty collection rather than raising, so a silent zero is the symptom to watch for.

## 5. Compare two catalogues

This is what the bookkeeping was for. The Danish figure is in `EUR_2020` per MWh; the USA figure is in `USD_2022` per kWh. Converting both to `USD_2023` per kWh makes them comparable.

``` py
>>> dea_investment = selected.technologies[0].parameters["specific investment"]
>>> dea_2023 = dea_investment.to_currency("USD_2023", country="DEU").to("USD_2023/kWh")
>>> usa_battery = next(
...     t
...     for t in usa.technologies.technologies
...     if t.detailed_technology == "battery storage"
...     and t.year == 2030
...     and t.case == "Moderate - Market"
... )
>>> usa_2023 = usa_battery.parameters["investment"].to_currency("USD_2023", country="USA")
>>> print(round(dea_2023.magnitude, 1), dea_2023.units)
351.7 USD_2023 / kilowatt_hour
>>> print(round(usa_2023.magnitude, 1), usa_2023.units)
264.2 USD_2023 / kilowatt_hour
```

`to_currency()` takes the target currency and the **ISO3 country code** whose deflator to use — `DEU`, `USA` — not a currency code. Both numbers are now on the same basis, and the remaining difference is a difference in the sources rather than in their units.

To work with both catalogues at once, concatenate them into one collection:

``` py
>>> combined = TechnologyCollection(
...     technologies=dea.technologies.technologies + usa.technologies.technologies
... )
>>> print(len(combined.technologies))
221
```

## 6. Save it and load it back

`to_json()` writes a package to a directory; `from_json()` reads it back given the same name and version.

``` py
>>> import tempfile
>>> folder = pathlib.Path(tempfile.mkdtemp())
>>> package.to_json(folder)
>>> print(sorted(p.name for p in folder.iterdir()))
['sources.json', 'technologies.json']
>>> reloaded = DataPackage.from_json("my-assumptions", "v1", folder)
>>> print(len(reloaded.technologies.technologies))
1
```

The two files are the same shape as the ones the bundled catalogues ship, so a package you assemble here can be loaded by anything that reads them.

## 7. Derive parameters and check consistency

Some parameters are related by known formulas rather than independent. Specific investment cost, total investment cost and capacity are one such triple: specific investment is just total investment divided by capacity. `calculate_parameters()` uses a registry of these relationships to fill in whichever one is missing.

``` py
>>> tech = Technology(
...     name="Solar PV",
...     detailed_technology="Crystalline Silicon",
...     case="Base",
...     region="DEU",
...     year=2020,
...     parameters={
...         "specific_investment": Parameter(magnitude=1.0, units="EUR_2020/kW"),
...         "total_investment_cost": Parameter(magnitude=1_000.0, units="EUR_2020"),
...     },
... )
>>> tech = tech.calculate_parameters("capacity")
>>> capacity = tech.parameters["capacity"]
>>> print(capacity.magnitude, capacity.units)
1000.0 kilowatt
```

The same relationship works in reverse to check, rather than derive: `check_consistency()` confirms that the parameters a technology already has still agree with each other.

``` py
>>> print(tech.check_consistency(parameters=["capacity"]))
{'total_investment_from_specific': True}
```

If a parameter is edited by hand and no longer agrees with the others, the check flags it:

``` py
>>> tech.parameters["capacity"].magnitude = 5
>>> print(tech.check_consistency(parameters=["capacity"]))
{'total_investment_from_specific': False}
```

`parameters=` restricts the check to equations that involve the given names; omit it to check every equation touching any parameter the technology has.

## 8. Project a technology into the future

A published catalogue only covers the years its source measured. Growth-model curves — linear, exponential, logistic and others — fit to known data points and project a value to any year, past or future.

``` py
>>> from technologydata.technologies.growth_models import LinearGrowth
>>> model = LinearGrowth(x0=2020)
>>> model = model.add_data((2020, 1000.0)).add_data((2025, 1250.0)).add_data((2030, 1500.0))
>>> model = model.fit()
>>> model.project(2040)
2000.0
```

`add_data()` and `fit()` both return the model, so calls chain. `project()` extrapolates using the fitted curve — here a straight line through the three points, continued out to 2040. `TechnologyCollection.fit()` and `.project()` apply the same curves across every technology in a collection at once, fitting one named parameter per technology and returning a new collection with the projected years added.

## Where to go next

- [`Parameter`](../user_guide/parameter.md), [`TechnologyCollection`](../user_guide/technology_collection.md) and [`DataPackage`](../user_guide/datapackage.md) — reference for the classes built above.
- [`DataAccessor`](../user_guide/data_accessor.md) — every option for locating and loading a catalogue.
- [Danish Energy Agency parser](../examples/dea_storage_v10.md) and [Manual Input USA parser](../examples/manual_input_usa_v0134.md) — how each bundled catalogue is produced from its raw file.
- [Parameter formula system](../user_guide/equations.md) — every built-in formula, how to register your own, and the details of how a formula is solved.
- [`Technology`](../user_guide/technology.md) and [Models](../user_guide/models.md) — more on `calculate_parameters()`, `check_consistency()` and the growth-model curves.
- [Use cases](../user_guide/design.md) — the scenarios the package was designed around.
