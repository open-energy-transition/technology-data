<!--
SPDX-FileCopyrightText: The technology-data authors
SPDX-License-Identifier: MIT
-->
# Contributing

## Install the development dependencies

To contribute to this project, you will need to install the development dependencies.
These dependencies are listed in the `pyproject.toml` file and include everything needed for development, testing and building the documentation of the project.

To install the development dependencies, run the following command inside the project directory:

```bash
uv sync
```

This will create a virtual environment at `.venv`.

The development dependencies include `ipykernel` to support Jupyter notebooks and integration into e.g. VS Code.

To view the full list of development dependencies, you can check the `pyproject.toml` file under the `[dependency-groups]` section as `dev` and `docs`, which are both included in the `default-groups`.

The virtual environment can be "activated" to make its packages available:

=== "macOS and Linux"

    ```bash
    source .venv/bin/activate
    ```

=== "Windows"

    ```pwsh-session
    PS> .venv\Scripts\activate
    ```

To exit a virtual environment, use the `deactivate` command:

```bash
deactivate
```

## Add new development dependencies
To add new dependencies to a specific dependency group in the `pyproject.toml`:

```bash
uv add package_name --group group_name
```

To install the new dependency run `uv sync`.

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

## Documentation
The documentation is generated with [MkDocs](https://www.mkdocs.org/). The documentation source files are written in Markdown and are available under the `/docs` sub-folder. The documentation is configured with the `mkdocs.yaml` file. 

MkDocs offers the possibility to start a builtin development server to preview the documentation as you work on it.  To start the development server run:

```bash
mkdocs serve
```


