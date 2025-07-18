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
    """
    Create a Source object from a parameter dictionary with validation.

    This function takes a dictionary of parameters and validates that the required fields are present.
    If any required fields are missing, a ValueError is raised. If all required fields are present,
    a new Source object is created and returned.

    Parameters
    ----------
    params : dict[str, str]
        A dictionary containing the parameters for creating a Source object.
        Must include the keys "source_title" and "source_authors".
        Other keys are optional.

    Returns
    -------
    td.Source
        A Source object initialized with the provided parameters.

    Raises
    ------
    ValueError
        If any of the required fields ("source_title", "source_authors") are missing from the params.

    Examples
    --------
    >>> params_dict = {
    ...     "source_title": "Example Title",
    ...     "source_authors": "John Doe",
    ...     "source_url": "http://example.com",
    ...     "source_url_archive": "http://web.archive.org/web/20231001120000/http://example.com",
    ...     "source_url_date": "2023-10-01",
    ...     "source_url_date_archive": "2023-10-01T12:00:00Z"
    ... }
    >>> source = create_source_from_params(params_dict)

    """
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
