# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Test the schema version of serialised collections."""

import json
import pathlib

import pytest

import technologydata
from technologydata import SCHEMA_VERSION, SourceCollection, TechnologyCollection

path_cwd = pathlib.Path.cwd()
example_folder = pathlib.Path(
    path_cwd, "test", "test_data", "solar_photovoltaics_example"
)

COLLECTIONS = [
    pytest.param(TechnologyCollection, "technologies.json", id="technologies"),
    pytest.param(SourceCollection, "sources.json", id="sources"),
]
COLLECTION_CLASSES: list[type[TechnologyCollection | SourceCollection]] = [
    TechnologyCollection,
    SourceCollection,
]


def _write_with_version(
    tmp_path: pathlib.Path, file_name: str, version: object
) -> pathlib.Path:
    """Copy an example file, replacing its schema version."""
    data = json.loads(pathlib.Path(example_folder, file_name).read_text())
    data["schema_version"] = version
    output_file = pathlib.Path(tmp_path, file_name)
    output_file.write_text(json.dumps(data))
    return output_file


def test_schema_version_is_integer() -> None:
    """Check that the schema version is a positive integer."""
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION >= 1


@pytest.mark.parametrize("collection_cls, file_name", COLLECTIONS)  # type: ignore
def test_to_json_writes_schema_version_first(
    collection_cls: type[TechnologyCollection | SourceCollection],
    file_name: str,
    tmp_path: pathlib.Path,
) -> None:
    """Check that to_json writes the schema version as the first key."""
    collection = collection_cls.from_json(pathlib.Path(example_folder, file_name))
    output_file = pathlib.Path(tmp_path, file_name)
    collection.to_json(output_file)

    data = json.loads(output_file.read_text())
    assert next(iter(data)) == "schema_version"
    assert data["schema_version"] == SCHEMA_VERSION


def test_nested_sources_have_no_schema_version(tmp_path: pathlib.Path) -> None:
    """Check that only the top level of technologies.json carries the version."""
    collection = TechnologyCollection.from_json(
        pathlib.Path(example_folder, "technologies.json")
    )
    output_file = pathlib.Path(tmp_path, "technologies.json")
    collection.to_json(output_file)

    assert output_file.read_text().count('"schema_version"') == 1


def test_new_collection_has_current_schema_version() -> None:
    """Check that collections created in memory get the current version."""
    assert TechnologyCollection(technologies=[]).schema_version == SCHEMA_VERSION
    assert SourceCollection(sources=[]).schema_version == SCHEMA_VERSION


@pytest.mark.parametrize(
    "version, message",
    [
        (SCHEMA_VERSION + 1, "Upgrade technologydata"),
        (SCHEMA_VERSION - 1, "no longer supported"),
        ("1", "must be an integer"),
    ],
)  # type: ignore
@pytest.mark.parametrize("collection_cls, file_name", COLLECTIONS)  # type: ignore
def test_from_json_rejects_other_schema_version(
    collection_cls: type[TechnologyCollection | SourceCollection],
    file_name: str,
    version: object,
    message: str,
    tmp_path: pathlib.Path,
) -> None:
    """Check that files with a different or invalid schema version are rejected."""
    input_file = _write_with_version(tmp_path, file_name, version)
    with pytest.raises(ValueError, match=message):
        collection_cls.from_json(input_file)


def test_model_validate_rejects_other_schema_version() -> None:
    """Check that the version is also checked when validating a dict."""
    with pytest.raises(ValueError, match="Upgrade technologydata"):
        SourceCollection.model_validate(
            {"schema_version": SCHEMA_VERSION + 1, "sources": []}
        )


@pytest.mark.parametrize("collection_cls", COLLECTION_CLASSES)  # type: ignore
def test_json_schema_contains_schema_version(
    collection_cls: type[TechnologyCollection | SourceCollection],
) -> None:
    """Check that the generated JSON schema documents the schema version."""
    schema = collection_cls.model_json_schema()
    assert schema["properties"]["schema_version"]["default"] == SCHEMA_VERSION
    assert schema["properties"]["schema_version"]["type"] == "integer"


def test_schema_version_exported() -> None:
    """Check that SCHEMA_VERSION is part of the public API."""
    assert "SCHEMA_VERSION" in technologydata.__all__
