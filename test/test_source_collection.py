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
def test_example_source_collection(
    example_source_collection: td.SourceCollection,
) -> None:
    """Check if the example source collection is instantiated correctly."""
    # Check that the returned object is a SourceCollection
    assert isinstance(example_source_collection, td.SourceCollection)

    # Check the number of sources
    assert len(example_source_collection.sources) == 2

    # Check the titles of the sources
    assert example_source_collection.sources[0].title == "Source 1"
    assert example_source_collection.sources[1].title == "Source 2"
    assert example_source_collection.sources[0].authors == "Author 1"
    assert example_source_collection.sources[1].authors == "Author 2"


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
def test_retrieve_all_archives(example_source_collection: td.SourceCollection) -> None:
    """Check if the example source collection is downloaded from the Internet Archive Wayback Machine."""
    storage_paths = example_source_collection.retrieve_all_archives(path_cwd)

    # Check if storage_paths is not None and is a list
    assert storage_paths is not None, "Expected storage_paths to be not None."
    assert isinstance(storage_paths, list), "Expected storage_paths to be a list."

    # Filter out None values and check the remaining paths
    valid_paths = [path for path in storage_paths if path is not None]

    assert all(isinstance(path, pathlib.Path) for path in valid_paths), (
        f"Expected all elements in {valid_paths} to be instances of pathlib.Path."
    )
    assert all(path.is_file() for path in valid_paths), (
        f"Expected all elements in {valid_paths} to be a file, but it does not exist."
    )

    # Delete the downloaded files
    for path in valid_paths:
        path.unlink(missing_ok=True)


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
def test_export_to_csv(example_source_collection: td.SourceCollection) -> None:
    """Check if the example source collection is exported to CSV."""
    output_file = pathlib.Path(path_cwd, "export.csv")
    example_source_collection.export_to_csv(pathlib.Path(output_file))
    assert output_file.is_file()
    output_file.unlink(missing_ok=True)


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
def test_export_to_json(example_source_collection: td.SourceCollection) -> None:
    """Check if the example source collection is exported to JSON."""
    output_file = pathlib.Path(path_cwd, "export.json")
    schema_file = pathlib.Path(path_cwd, "source_collection_schema.json")
    example_source_collection.export_to_json(pathlib.Path(output_file))
    assert output_file.is_file()
    assert schema_file.is_file()
    output_file.unlink(missing_ok=True)
    schema_file.unlink(missing_ok=True)
