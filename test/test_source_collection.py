# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the initialization and methods of the SourceCollection class."""

import pathlib

import pytest

import technologydata as td

path_cwd = pathlib.Path.cwd()


@pytest.mark.parametrize(
    "example_source_collection",
    [
        [
            {
                "source_title": "Source 1",
                "source_authors": "Author 1",
            },
            {
                "source_title": "Source 2",
                "source_authors": "Author 2",
            },
        ]
    ],
    indirect=True,
)  # type: ignore
def test_example_source_collection(example_source_collection):
    # Check that the returned object is a SourceCollection
    assert isinstance(example_source_collection, td.SourceCollection)

    # Check the number of sources
    assert len(example_source_collection.sources) == 2

    # Check the titles of the sources
    assert example_source_collection.sources[0].title == "Source 1"
    assert example_source_collection.sources[1].title == "Source 2"
    assert example_source_collection.sources[0].authors == "Author 1"
    assert example_source_collection.sources[1].authors == "Author 2"
