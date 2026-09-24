# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Schema version of the JSON files written and read by technologydata."""

from typing import Any

# Version of the data schema. Increment on any change.
# It is independent of the package version and of dataset versions.
SCHEMA_VERSION = 1


def check_schema_version(data: dict[str, Any], model_name: str) -> None:
    """
    Check that serialised data was written with the current schema version.

    Parameters
    ----------
    data : dict[str, Any]
        The deserialised JSON content, containing a ``schema_version`` key.
    model_name : str
        Name of the model being loaded, used in error messages.

    Raises
    ------
    ValueError
        If ``schema_version`` is not an integer or differs from `SCHEMA_VERSION`.

    """
    version = data["schema_version"]
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValueError(
            f"{model_name} 'schema_version' must be an integer, got {version!r}."
        )
    if version > SCHEMA_VERSION:
        raise ValueError(
            f"{model_name} data has schema version {version}, but this version of "
            f"technologydata supports up to schema version {SCHEMA_VERSION}. "
            f"Upgrade technologydata to load this file."
        )
    if version < SCHEMA_VERSION:
        # No migrations exist yet; add them here when the schema changes.
        raise ValueError(
            f"{model_name} data has schema version {version}, which is no longer "
            f"supported (current schema version: {SCHEMA_VERSION}). Migrate or regenerate "
            f"the file with the current version of technologydata."
        )
