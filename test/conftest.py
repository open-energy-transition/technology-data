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


def create_source_from_params(params: dict[str, str]) -> td.Source:
    """Helper to create a Source object from a parameter dictionary, with validation."""
    required_fields = ["source_title", "source_authors"]
    missing = [f for f in required_fields if f not in params]
    if missing:
        raise ValueError(f"Missing required fields for Source: {missing}")
    return td.Source(
        title=params["source_title"],
        authors=params["source_authors"],
        url=params.get("source_url"),
        url_archive=params.get("source_url_archive"),
        url_date=params.get("source_url_date"),
        url_date_archive=params.get("source_url_date_archive"),
    )


@pytest.fixture(scope="function")  # type: ignore
def example_source(request: pytest.FixtureRequest) -> td.Source:
    """Fixture to create an example source."""
    return create_source_from_params(request.param)


@pytest.fixture(scope="function")  # type: ignore
def example_source_collection(request: pytest.FixtureRequest) -> td.SourceCollection:
    """
    Fixture to create an example SourceCollection from a list of parameter dicts.

    Each dict in the list must contain the following keys:
        - source_title
        - source_authors

    This fixture is compatible with pytest parametrize.
    """
    sources_params: list[dict[str, str]] = request.param
    sources = [create_source_from_params(params) for params in sources_params]
    return td.SourceCollection(sources=sources)
