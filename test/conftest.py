# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
The module is used to define sharable pytest fixtures.

Fixtures are a way to provide a fixed baseline upon which tests can
rely. They allow for setup code to be reused and can help manage
resources needed for tests, such as database connections, test data,
or configuration settings.
By placing fixtures in this file, they become accessible to all test
modules in the same directory and subdirectories, promoting code
reusability and organization.
"""


import pathlib
import sys

import pytest

import technologydata as td

sys.path.append("./technology-data")
path_cwd = pathlib.Path.cwd()


@pytest.fixture(scope="function")  # type: ignore
def example_source(request: pytest.FixtureRequest) -> td.Source:
    """Fixture to create an example source."""
    # Fetch the necessary values from the request object
    source_title = request.param.get("source_title", "example_source_01")
    source_authors = request.param.get("source_authors", "example_author")
    source_url = request.param.get("source_url", "https://example.com")
    source_url_archive = request.param.get("source_url_archive", "https://web.archive.org/web/20250522150802/https://example.com")
    source_url_date = request.param.get("source_url_date", "2025-05-22 15:08:02")
    source_url_date_archive = request.param.get("source_url_date_archive", "2025-05-22 15:08:02")

    def load_example_source() -> td.Source:
        """Inner function to create the source object."""
        return td.Source(
            title=source_title,
            authors=source_authors,
            url=source_url,
            url_archive=source_url_archive,
            url_date=source_url_date,
            url_date_archive=source_url_date_archive,
        )

    # Call the inner function and return the result
    return load_example_source()
