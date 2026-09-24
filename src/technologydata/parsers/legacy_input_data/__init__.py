# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Provide a parser for the technology-data raw/legacy_input_data/other.csv and raw/legacy_input_data/usa.csv datasets."""

import logging
import pathlib

from technologydata.parsers.data_parser_base import ParserBase
from technologydata.parsers.legacy_input_data.parser_v0134 import (
    LegacyInputDataV0134Parser,
)


class LegacyInputDataParser:
    """
    Main parser for the technology_data raw/legacy_input_data/other.csv and raw/legacy_input_data/usa.csv dataset.

    Dispatches to version-specific parser implementations.
    """

    def __init__(self) -> None:
        """Initialize the parser and maps versions to parser classes."""
        self._parsers: dict[str, type[ParserBase]] = {
            "v0.13.4": LegacyInputDataV0134Parser,
            # "v0.13.5": LegacyInputDataV0135Parser, # Add new versions here
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
        Parse the specified version of the technology_data raw/legacy_input_data/other.csv and raw/legacy_input_data/usa.csv dataset.

        This method selects the appropriate parser for the given version and
        delegates the parsing task to it.

        Parameters
        ----------
        version : str
            The version of the dataset to parse (e.g., 'v0.13.4').
        input_path : list of pathlib.Path
            List of paths to the raw input data files (CSV).
        num_digits : int, optional
            Number of significant digits to round the values, by default 4.
        archive_source : bool, optional
            If True, archives the source object on the Wayback Machine, by default False.
        filter_params : bool, optional
            If True, filters the parameters stored in the output, by default False.
        export_schema : bool, optional
            If True, exports the Pydantic schema for the data models, by default False.

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
            f"Parsing the technology-data raw/legacy_input_data/usa.csv and raw/legacy_input_data/other.csv. dataset version {version} using {parser_class.__name__}"
        )
        return parser_instance.parse(
            input_path=input_path,
            num_digits=num_digits,
            archive_source=archive_source,
            filter_params=filter_params,
            export_schema=export_schema,
        )


# Make the main parser class available for import from the module
__all__ = ["LegacyInputDataParser", "LegacyInputDataV0134Parser"]
