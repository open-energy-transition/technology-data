# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT
from enum import Enum
from typing import Annotated

import pydantic


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
