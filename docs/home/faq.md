# Frequently Asked Questions (FAQ)

## How should I cite this package?

See the dedicated page on [Citing](citing.md).

## How do I add a new data source?

To add a new data source to the `technologydata` package:

1. **Create a Parser Class**: Implement a parser class that inherits from `DataParserBase` in `src/technologydata/parsers/`
2. **Register the Data Source**: Add your data source to the `DataSourceName` enumeration in `src/technologydata/parsers/data_accessor.py`
3. **Implement Version Support**: Create version-specific subdirectories under your parser directory (e.g., `v1.0/`, `v2.0/`)
4. **Place Raw Data**: Store your raw data files in `src/technologydata/parsers/raw/`
5. **Update DataAccessor**: Add your parser to the `parse()` method logic in `DataAccessor`
6. **Document Your Parser**: Create documentation in `docs/examples/` following the pattern of existing parser documentation

For detailed contribution guidelines, see the [contributing instructions](../contributing/instructions.md).

## How can I access data from a remote source?

You can use the `download()` method of the `DataAccessor` class to load technology data directly from remote URLs:

```python
from technologydata.parsers.data_accessor import DataAccessor

accessor = DataAccessor(
    data_source="dea_energy_storage",
    version="v10"
)

# Download from a remote URL
base_url = "https://example.com/data/dea_energy_storage/v10/"
dp = accessor.download(base_url)
```

The method will download both `technologies.json` and `sources.json` (if available) from the specified URL.

## If I use the package today, will the data change when I update the package later?

The data versioning system ensures reproducibility:

- Each data source has explicit version identifiers (e.g., `v10`, `v0.13.4`)
- When you specify a version in `DataAccessor`, you lock to that specific dataset
- Updating the package may add new versions but will not modify existing versioned data

Example for reproducible usage:

```python
# Pin specific versions
accessor = DataAccessor(
    data_source="dea_energy_storage",
    version="v10"  # Explicitly specify version
)
dp = accessor.load()
```

## How can I support your work?

TODO

## I would like to get involved, what can I do?

TODO

## How is this project different to GENESTE or other projects?

TODO
and ref. to GENESTE: <https://www.sciencedirect.com/science/article/pii/S235234092400636X>
