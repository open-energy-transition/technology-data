# Contributing

## Development dependencies

To contribute to this project, you will need to install the development dependencies.
These dependencies are not required for the basic functionality of the project but are essential for development, testing, and documentation.
To install the development dependencies, run the following command inside the project directory:

```bash
uv sync --extra dev
```

The development dependencies include `ipykernel` to support Jupyter notebooks and integration into e.g. VS Code.

## Testing

To run all tests in parallel, you can use the following command:

```bash
pytest -n auto
```

Some tests may not be thread-safe and therefore fail unexpectedly when run in parallel.
If you encounter such issues, you can run the tests sequentially by omitting the `-n auto` option:

```bash
pytest
```
