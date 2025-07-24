# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the initialization and methods of the Datapackage class."""

import pathlib

import technologydata

path_cwd = pathlib.Path.cwd()


def test_get_source_collection() -> None:
    """Test how the sources attributes is extracted from a TechnologyCollection instance."""
    input_file = pathlib.Path(
        path_cwd,
        "test",
        "test_data",
        "solar_photovoltaics_example_03",
        "technologies.json",
    )
    technologies_collection = technologydata.TechnologyCollection.from_json(input_file)
    data_package = technologydata.DataPackage(
        name="test_package",
        path=pathlib.Path(path_cwd, "test_package"),
        technologies=technologies_collection,
    )
    assert isinstance(
        data_package.get_source_collection(), technologydata.SourceCollection
    )
