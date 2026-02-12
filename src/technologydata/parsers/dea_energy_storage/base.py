# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Abstract base class for a specific version of the DEA parser."""

import abc
import pathlib


class DeaEnergyStorageParserBase(abc.ABC):
    """Abstract base class for a specific version of the DEA parser."""

    @abc.abstractmethod
    def parse(
        self,
        input_path: pathlib.Path,
        num_digits: int,
        store_source: bool,
        filter_params: bool,
        export_schema: bool,
    ) -> None:
        """
        Parse a specific version of the DEA Energy Storage dataset.

        Parameters
        ----------
        input_path : pathlib.Path
            Path to the raw input data file.
        num_digits : int
            Number of significant digits to round the values.
        store_source : bool
            If True, store the source object on the Wayback Machine.
        filter_params : bool
            If True, filter the parameters stored in the output.
        export_schema : bool
            If True, export the Pydantic schema for the data models.

        """
        raise NotImplementedError
