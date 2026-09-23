# Frequently asked questions

## How do I add a new data source to the package?

A data source is a package of a name, one or more versioned parsers, and a dispatcher:

1. Add a member to the `DataSourceName` enumeration in `parsers/data_accessor.py`.
2. Add `parsers/<source>/parser_v<version>.py` containing a class that subclasses `ParserBase` and implements its abstract `parse()` method.
3. Add `parsers/<source>/__init__.py` containing a dispatcher class that maps version strings to parser classes and exposes `get_supported_versions()`.
4. Register the dispatcher in `DataAccessor.parse()`.
5. Place the raw input file in `parsers/raw/`. The parser writes the parsed catalogue to `parsers/<source>/<version>/technologies.json`.

## If I use the package today, will the data change when I update the package later?

Datasets are shipped in version-pinned directories — `dea_energy_storage/v10`, `manual_input_usa/v0.13.4` — and are selected with the `version` argument of `DataAccessor`.
A new version of the package will not change the data of existing versions unless for fixing incorrectly extracted values.
If newer editions of a catalogue become available, they will not replace an existing version, but be available under the new version name.
If you use the package in a production-ready application we recommend you pin the version of the data that you are using - by default the data accessors provide the `latest` version of the data available.

## I would like to get involved, what can I do?

Contributions are welcome!
The [Contributing](../contributing/instructions.md) section of this documentation describes the development setup and conventions, and `CONTRIBUTING.md` in the repository summarises them.
Bug reports and feature proposals are handled through the [issue tracker](https://github.com/open-energy-transition/technology-data/issues).
