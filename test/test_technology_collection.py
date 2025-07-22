# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the initialization and methods of the TechnologyCollection class."""

import pathlib

import pandas
import pytest

import technologydata

path_cwd = pathlib.Path.cwd()


def test_to_csv() -> None:
    """Check if the example technology collection is exported to CSV."""
    input_file = pathlib.Path(
        path_cwd,
        "test",
        "test_data",
        "solar_photovoltaics_example_03",
        "technologies.json",
    )
    technology_collection = technologydata.TechnologyCollection.from_json(input_file)
    output_file = pathlib.Path(path_cwd, "export.csv")
    technology_collection.to_csv(path_or_buf=output_file)
    assert output_file.is_file()
    # output_file.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "example_source_collection",
    [
        [
            {
                "source_title": "atb_nrel",
                "source_authors": "NREL/ATB",
                "source_url": "https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/parquet/2024/v3.0.0/ATBe.parquet",
                "source_url_archive": "https://web.archive.org/web/20250522150802/https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/parquet/2024/v3.0.0/ATBe.parquet",
                "source_url_date": "2025-05-22 15:08:02",
                "source_url_date_archive": "2025-05-22 15:08:02",
            },
            {
                "source_title": "tech_data_generation",
                "source_authors": "Danish Energy Agency",
                "source_url": "https://ens.dk/media/3273/download",
                "source_url_archive": "http://web.archive.org/web/20250506160204/https://ens.dk/media/3273/download",
                "source_url_date": "2025-05-06 16:02:04",
                "source_url_date_archive": "2025-05-06 16:02:04",
            },
        ],
    ],
    indirect=True,
)  # type: ignore
def test_to_json(example_source_collection: technologydata.SourceCollection) -> None:
    """Check if the example source collection is exported to JSON."""
    output_file = pathlib.Path(path_cwd, "sources.json")
    schema_file = pathlib.Path(path_cwd, "source_collection_schema.json")
    example_source_collection.to_json(pathlib.Path(output_file))
    assert output_file.is_file()
    assert schema_file.is_file()
    output_file.unlink(missing_ok=True)
    schema_file.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "example_source_collection",
    [
        [
            {
                "source_title": "atb_nrel",
                "source_authors": "NREL/ATB",
                "source_url": "https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/parquet/2024/v3.0.0/ATBe.parquet",
                "source_url_archive": "https://web.archive.org/web/20250522150802/https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/parquet/2024/v3.0.0/ATBe.parquet",
                "source_url_date": "2025-05-22 15:08:02",
                "source_url_date_archive": "2025-05-22 15:08:02",
            },
            {
                "source_title": "tech_data_generation",
                "source_authors": "Danish Energy Agency",
                "source_url": "https://ens.dk/media/3273/download",
                "source_url_archive": "http://web.archive.org/web/20250506160204/https://ens.dk/media/3273/download",
                "source_url_date": "2025-05-06 16:02:04",
                "source_url_date_archive": "2025-05-06 16:02:04",
            },
        ],
    ],
    indirect=True,
)  # type: ignore
def test_to_dataframe(
    example_source_collection: technologydata.SourceCollection,
) -> None:
    """Check if the example source collection is exported to pandas dataframe."""
    assert isinstance(example_source_collection.to_dataframe(), pandas.DataFrame)


def test_from_json() -> None:
    """Check if the example source collection is exported to JSON."""
    input_file = pathlib.Path(
        path_cwd, "test", "test_data", "solar_photovoltaics_example_03", "sources.json"
    )
    source_collection = technologydata.SourceCollection.from_json(input_file)
    assert isinstance(source_collection, technologydata.SourceCollection)
    assert len(source_collection) == 2


@pytest.mark.parametrize(
    "title_pattern, authors_pattern",
    [["ATB", "nrel"], ["TECH_DATA", "danish"]],
)  # type: ignore
def test_get(title_pattern: str, authors_pattern: str) -> None:
    """Check if the example source collection is filtered as requested."""
    input_file = pathlib.Path(
        path_cwd, "test", "test_data", "solar_photovoltaics_example_03", "sources.json"
    )

    source_collection = technologydata.SourceCollection.from_json(input_file)
    result = source_collection.get(title=title_pattern, authors=authors_pattern)
    assert len(result.sources) == 1
