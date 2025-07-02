"""
DataPackage class for managing collections of Technology objects and batch operations.

Examples
--------
>>> dp = DataPackage.from_json("path/to/data_package.json")
>>> dp.technologies[0].check_consistency()

"""

import json
from typing import Any

from pydantic import BaseModel, Field

from technologydata.technology import Technology


class DataPackage(BaseModel):
    """
    Container for a collection of Technology objects, with batch operations and loading utilities.

    Parameters
    ----------
    technologies : List[Technology]
        List of Technology objects.

    Attributes
    ----------
    technologies : List[Technology]
        List of Technology objects.

    """

    technologies: list[Technology] = Field(
        default_factory=list, description="List of Technology objects."
    )

    @classmethod
    def from_json(cls, path: str) -> "DataPackage":
        """
        Load a DataPackage from a JSON file.

        Parameters
        ----------
        path : str
            Path to the JSON file.

        Returns
        -------
        DataPackage
            The loaded DataPackage instance.

        """
        with open(path) as f:
            data = json.load(f)
        techs = [Technology(**t) for t in data.get("technologies", [])]
        return cls(technologies=techs)

    def check_consistency(self) -> dict[int, bool]:
        """
        Check consistency for all Technology objects in the package.

        Returns
        -------
        Dict[int, bool]
            Dictionary mapping index to consistency result.

        """
        return {i: tech.check_consistency() for i, tech in enumerate(self.technologies)}

    def calculate_parameters(self, parameters: Any | None = None) -> "DataPackage":
        """
        Calculate parameters for all Technology objects in the package.

        Parameters
        ----------
        parameters : Optional[Any]
            List of parameter names to calculate, or "<missing>" for all missing.

        Returns
        -------
        DataPackage
            A new DataPackage with calculated parameters.

        """
        techs = [
            tech.calculate_parameters(parameters=parameters)
            for tech in self.technologies
        ]
        return DataPackage(technologies=techs)
