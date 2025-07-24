# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
DataPackage class for managing collections of Technology objects and batch operations.

Examples
--------
>>> dp = DataPackage.from_json("path/to/data_package.json")

"""

import pathlib

import pydantic

from technologydata.source_collection import SourceCollection
from technologydata.technology_collection import TechnologyCollection


# TODO complete class
class DataPackage(pydantic.BaseModel):  # type: ignore
    """
    Container for a collection of Technology objects and/or Source objects, with batch operations and loading utilities.

    Parameters
    ----------
    name : str
        The short-name code of the data package.
    path : pathlib.Path
        The path to the data package.
    technologies : TechnologyCollection
        List of Technology objects.
    sources : SourceCollection
        List of Source objects.

    Attributes
    ----------
    name : str
        The short-name code of the data package.
    path : pathlib.Path
        The path to the data package.
    technologies : TechnologyCollection
        List of Technology objects.
    sources : SourceCollection
        List of Source objects.

    """

    name: str = pydantic.Field(
        ..., description="The short-name code of the data package."
    )
    path: pathlib.Path = pydantic.Field(
        ..., description="The path to the data package."
    )
    technologies: TechnologyCollection = pydantic.Field(
        ..., description="List of Technology objects."
    )
    sources: SourceCollection | None = pydantic.Field(
        None, description="List of Source objects."
    )

    def get_source_collection(self) -> None:
        """
        Get the SourceCollection associated with this DataPackage from the TechnologyCollection.

        Returns
        -------
        SourceCollection
            The SourceCollection instance.

        """
        sources_set = set()
        if self.sources is None:
            for technology in self.technologies:
                for parameter in technology.parameters.values():
                    sources_set.update(parameter.sources)
        self.sources = sources_set

    # @classmethod
    # def from_json(cls, path: pathlib.Path) -> technologydata.DataPackage:
    #     """
    #     Load a DataPackage from a JSON file.
    #
    #     Parameters
    #     ----------
    #     path : Path
    #         Path to the JSON file.
    #
    #     Returns
    #     -------
    #     DataPackage
    #         The loaded DataPackage instance.
    #
    #     """
    #     with open(path) as f:
    #         data = json.load(f)
    #     techs = technologydata.TechnologyCollection(
    #         [technologydata.Technology(**t) for t in data.get("technologies", [])]
    #     )
    #     # TODO: redo this part once an example JSON is available
    #     techs = technologydata.TechnologyCollection(
    #         [technologydata.Technology(**t) for t in data.get("technologies", [])]
    #     )
    #     # You should also handle 'name', 'sources', etc. as needed
    #     return cls(
    #         name=data.get("name", ""),
    #         path=path,
    #         technologies=techs,
    #         sources=technologydata.SourceCollection(data.get("sources", [])),
    #     )
    #
    # @classmethod
    # def to_json(cls, path: pathlib.Path) -> None:
    #     pass
    #
    # @classmethod
    # def to_datapackage(cls, path: pathlib.Path) -> None:
    #     pass
