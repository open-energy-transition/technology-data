# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT
import pathlib
from enum import Enum
from typing import Annotated, Self

import pydantic

from technologydata import DataPackage


class DataSourceName(str, Enum):
    """An enumeration of available data sources."""

    DEA_ENERGY_STORAGE = "dea_energy_storage"
    MANUAL_INPUT_USA = "manual_input_usa"


class DataAccessor(pydantic.BaseModel):
    """A class to access data from a data source."""

    data_source_name: Annotated[
        DataSourceName, pydantic.Field(description="The name of the data source.")
    ]
    data_version: Annotated[
        str | None, pydantic.Field(description="The version of the data source.")
    ] = None

    @staticmethod
    def from_package_data() -> Self:
        """
        Load the default 'technologies.json' from the package data.

        Returns
        -------
        TechnologyCollection
            An instance of TechnologyCollection initialized with the default data.

        """
        # This assumes 'technologies.json' is in a 'data' directory
        # at the same level as the 'src' directory.
        # Adjust the path as needed for your project structure.
        data_path = pathlib.Path(__file__).parent.parent.parent / "data" / "technologies.json"
        return DataPackage.from_json(data_path)
