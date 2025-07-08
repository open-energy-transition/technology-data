# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
DataPackage class for managing collections of Technology objects and batch operations.

Examples
--------
>>> dp = DataPackage.from_json("path/to/data_package.json")

"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from technologydata.source_collection import SourceCollection
from technologydata.technology import Technology
from technologydata.technology_collection import TechnologyCollection


class DataPackage(BaseModel):
    """
    Container for a collection of Technology objects and/or Source objects, with batch operations and loading utilities.

    Parameters
    ----------
    name : str
        The short-name code of the source
    technologies : List[Technology]
        List of Technology objects.

    Attributes
    ----------
    technologies : List[Technology]
        List of Technology objects.

    """

    name: str
    path: Path
    technologies: TechnologyCollection
    sources: SourceCollection

    @classmethod
    def from_json(cls, path: Path) -> DataPackage:
        """
        Load a DataPackage from a JSON file.

        Parameters
        ----------
        path : Path
            Path to the JSON file.

        Returns
        -------
        DataPackage
            The loaded DataPackage instance.

        """
        with open(path) as f:
            data = json.load(f)
        techs = TechnologyCollection(
            [Technology(**t) for t in data.get("technologies", [])]
        )
        # TODO: redo this part once an example JSON is available
        techs = TechnologyCollection(
            [Technology(**t) for t in data.get("technologies", [])]
        )
        # You should also handle 'name', 'sources', etc. as needed
        return cls(
            name=data.get("name", ""),
            path=path,
            technologies=techs,
            sources=SourceCollection(data.get("sources", [])),
        )

    @classmethod
    def to_json(cls, path: Path) -> None:
        pass

    @classmethod
    def to_datapackage(cls, path: Path) -> DataPackage:
        pass
