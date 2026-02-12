# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Provide a parser for the DEA data storage dataset."""

import logging
import pathlib
from typing import Type

from technologydata import TechnologyCollection
from technologydata.parsers.dea_energy_storage.base import DeaEnergyStorageParserBase
from technologydata.parsers.dea_energy_storage.parser_v10 import DeaEnergyStorageV10Parser


class DeaEnergyStorageParser:
    """
    Main parser for the DEA Energy Storage dataset.
    Dispatches to version-specific parser implementations.
    """

    def __init__(self) -> None:
        """Initializes the parser and maps versions to parser classes."""
        self._parsers: dict[str, Type[DeaEnergyStorageParserBase]] = {
            "v10": DeaEnergyStorageV10Parser,
            # "v11": DeaEnergyStorageV11Parser, # Add new versions here
        }

    def get_supported_versions(self) -> list[str]:
        """Returns a list of supported dataset versions."""
        return list(self._parsers.keys())

    def parse(
        self,
        version: str,
        input_path: pathlib.Path,
        num_digits: int = 4,
        store_source: bool = False,
        filter_params: bool = False,
        export_schema: bool = False,
    ) -> TechnologyCollection:
        """
        Parses the specified version of the DEA Energy Storage dataset.
        """
        if version not in self._parsers:
            raise ValueError(
                f"Unsupported version: {version}. "
                f"Supported versions are: {', '.join(self.get_supported_versions())}"
            )

        parser_class = self._parsers[version]
        parser_instance = parser_class()

        logging.info(f"Parsing DEA Energy Storage dataset version {version}...")
        return parser_instance.parse(
            input_path=input_path,
            num_digits=num_digits,
            store_source=store_source,
            filter_params=filter_params,
            export_schema=export_schema,
        )


# Make the main parser class available for import from the module
__all__ = ["DeaEnergyStorageParser"]
