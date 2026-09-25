# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Provide a parser for the DEA data storage dataset."""

import logging
import pathlib

from technologydata.parsers.data_parser_base import ParserBase
from technologydata.parsers.dea_energy_storage.parser_v10 import (
    DeaEnergyStorageV10Parser,
)


class DeaEnergyStorageParser:
    """
    Main parser for the DEA Energy Storage dataset.

    Dispatches to version-specific parser implementations.
    """

    def __init__(self) -> None:
        """Initialize the parser and maps versions to parser classes."""
        self._parsers: dict[str, type[ParserBase]] = {
            "v10": DeaEnergyStorageV10Parser,
            # "v11": DeaEnergyStorageV11Parser, # Add new versions here
        }

    def get_supported_versions(self) -> list[str]:
        """Return a list of supported dataset versions."""
        return list(self._parsers.keys())

    def parse(
        self,
        version: str,
        input_path: pathlib.Path | list[pathlib.Path],
        num_digits: int,
        archive_source: bool,
        filter_params: bool,
        export_schema: bool,
    ) -> None:
        """
        Parse the specified version of the DEA Energy Storage dataset.

        This method selects the appropriate parser for the given version and
        delegates the parsing task to it.

        Parameters
        ----------
        version : str
            The version of the dataset to parse (e.g., 'v10').
        input_path : pathlib.Path | list[pathlib.Path]
            Path to the raw input data file.
        num_digits : int
            Number of decimals to round numerical values to.
        archive_source : bool
            If True, archives the source object on the Wayback Machine and
            rewrites sources.json.
        filter_params : bool
            If True, keeps only a predefined set of parameters.
        export_schema : bool
            If True, exports the Pydantic schema for the data models.

        Raises
        ------
        ValueError
            If the specified version is not supported.

        """
        if version not in self._parsers:
            raise ValueError(
                f"Unsupported version: {version}. "
                f"Supported versions are: {', '.join(self.get_supported_versions())}"
            )

        parser_class = self._parsers[version]
        parser_instance = parser_class()

        logging.info(
            f"Parsing DEA Energy Storage dataset version {version} using {parser_class.__name__}"
        )
        return parser_instance.parse(
            input_path=input_path,
            num_digits=num_digits,
            archive_source=archive_source,
            filter_params=filter_params,
            export_schema=export_schema,
        )


# Make the main parser class available for import from the module
__all__ = ["DeaEnergyStorageParser", "DeaEnergyStorageV10Parser"]
