# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

import abc
import pathlib

from technologydata import TechnologyCollection


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
    ) -> TechnologyCollection:
        """
        Parses a specific version of the DEA Energy Storage dataset.
        """
        raise NotImplementedError
