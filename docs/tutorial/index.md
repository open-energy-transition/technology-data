# Tutorial

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

This tutorial builds up a `DataPackage` from nothing, then replaces the hand-written parts with published data. Each section adds one idea and every snippet runs on its own, so you can paste them into a session in order.

## When to use this package

Techno-economic catalogues are published in different currencies, price years, units, heating-value conventions and naming schemes. Comparing two of them means tracking all of that by hand, and the bookkeeping is where the mistakes happen.

Reach for `technologydata` when you need to:

- combine assumptions from more than one source, or from a source and your own numbers;
- convert between currencies, price years and units without losing track of what was converted;
- keep a record of where each number came from.

It is **not** the right tool when you only need a handful of constants for one model, in one currency, from one source. A dictionary is simpler and honest about its scope.

## 1. A parameter that knows its units

The smallest useful object is a `Parameter`: a magnitude, a unit, and the source it came from.

```python
from technologydata import Parameter, Source, SourceCollection

sources = SourceCollection(sources=[Source(
    title="Technology Data for Energy storage (May 2025)",
    authors="Danish Energy Agency",
    url="https://ens.dk/media/6589/download",
)])

investment = Parameter(magnitude=288000.0, units="EUR_2020/MWh", sources=sources)
print(investment.magnitude, investment.units)
```

```text
288000.0 EUR_2020 / megawatt_hour
```

The unit string is parsed rather than stored verbatim, which is why `EUR_2020/MWh` comes back as `EUR_2020 / megawatt_hour`. A currency is written as a three-letter code, an underscore and the price year — `EUR_2020`, `USD_2022`. Prefixed forms such as `MEUR_2020` are **not** units the registry knows; scale the magnitude instead.

Because the unit is real, the parameter can be converted:

```python
per_kwh = investment.to("EUR_2020/kWh")
print(per_kwh.magnitude, per_kwh.units)
```

```text
288.0 EUR_2020 / kilowatt_hour
```

## 2. From parameter to data package

A `Technology` groups parameters that describe the same thing in the same year and case. A `TechnologyCollection` holds many of those, and a `DataPackage` pairs a collection with its sources.

```python
from technologydata import DataPackage, Technology, TechnologyCollection

battery = Technology(
    name="lithium ion battery",
    detailed_technology="lithium-ion battery (utility-scale)",
    region="EU",
    year=2025,
    case="control",
    parameters={"specific investment": investment},
)

package = DataPackage(
    name="my-assumptions",
    version="v1",
    technologies=TechnologyCollection(technologies=[battery]),
    sources=sources,
)
print(package.name, package.version, len(package.technologies.technologies))
```

```text
my-assumptions v1 1
```

`DataPackage` requires a `name` and a `version` as well as the data — they are what `from_json()` uses to identify the package later.

## 3. Load a published catalogue

Writing technologies by hand does not scale. The package ships two parsed catalogues, which load the same way and give you the same `TechnologyCollection` type you just built.

```python
import pathlib

import technologydata
from technologydata.parsers.data_accessor import DataAccessor

# The bundled catalogues ship inside the installed package.
data = pathlib.Path(technologydata.__file__).parent / "parsers"

dea = DataAccessor(data_source="dea_energy_storage", version="v10", data_path=data).load()
usa = DataAccessor(data_source="manual_input_usa", version="v0.13.4", data_path=data).load()

print(len(dea.technologies.technologies), len(usa.technologies.technologies))
```

```text
136 85
```

## 4. Select one technology

`TechnologyCollection.get()` filters on five attributes and returns a new collection.

!!! warning "`get()` matches regular expressions, not literal text"
    Every argument is compiled as a regex, so `(` and `)` are read as a group rather than as brackets. A name containing them silently matches nothing. Pass it through `re.escape()`.

```python
import re

selected = dea.technologies.get(
    name="lithium ion battery",
    region="EU",
    year=2030,
    case="control",
    detailed_technology=re.escape("lithium-ion battery (utility-scale)"),
)
print(len(selected.technologies))
```

```text
1
```

Without `re.escape()` the same call returns an empty collection rather than raising, so a silent zero is the symptom to watch for.

## 5. Compare two catalogues

This is what the bookkeeping was for. The Danish figure is in `EUR_2020` per MWh; the USA figure is in `USD_2022` per kWh. Converting both to `USD_2023` per kWh makes them comparable.

```python
dea_investment = selected.technologies[0].parameters["specific investment"]
dea_2023 = dea_investment.to_currency("USD_2023", country="DEU").to("USD_2023/kWh")

usa_battery = next(
    t
    for t in usa.technologies.technologies
    if t.detailed_technology == "battery storage"
    and t.year == 2030
    and t.case == "Moderate - Market"
)
usa_2023 = usa_battery.parameters["investment"].to_currency("USD_2023", country="USA")

print(round(dea_2023.magnitude, 1), dea_2023.units)
print(round(usa_2023.magnitude, 1), usa_2023.units)
```

```text
351.7 USD_2023 / kilowatt_hour
264.2 USD_2023 / kilowatt_hour
```

`to_currency()` takes the target currency and the **ISO3 country code** whose deflator to use — `DEU`, `USA` — not a currency code. Both numbers are now on the same basis, and the remaining difference is a difference in the sources rather than in their units.

To work with both catalogues at once, concatenate them into one collection:

```python
combined = TechnologyCollection(
    technologies=dea.technologies.technologies + usa.technologies.technologies
)
print(len(combined.technologies))
```

```text
221
```

## 6. Save it and load it back

`to_json()` writes a package to a directory; `from_json()` reads it back given the same name and version.

```python
import tempfile

folder = pathlib.Path(tempfile.mkdtemp())
package.to_json(folder)
print(sorted(p.name for p in folder.iterdir()))

reloaded = DataPackage.from_json("my-assumptions", "v1", folder)
print(len(reloaded.technologies.technologies))
```

```text
['sources.json', 'technologies.json']
1
```

The two files are the same shape as the ones the bundled catalogues ship, so a package you assemble here can be loaded by anything that reads them.

## Where to go next

- [`Parameter`](../user_guide/parameter.md), [`TechnologyCollection`](../user_guide/technology_collection.md) and [`DataPackage`](../user_guide/datapackage.md) — reference for the classes built above.
- [`DataAccessor`](../user_guide/data_accessor.md) — every option for locating and loading a catalogue.
- [Danish Energy Agency parser](../examples/dea_storage_v10.md) and [Manual Input USA parser](../examples/manual_input_usa_v0134.md) — how each bundled catalogue is produced from its raw file.
- [Use cases](../user_guide/design.md) — the scenarios the package was designed around.
