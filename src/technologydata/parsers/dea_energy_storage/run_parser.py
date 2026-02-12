# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""
Data parser for the DEA energy storage data set.

How to run:
    From the repository root, execute:
        python src/technologydata/parsers/dea_energy_storage/dea_energy_storage.py

Configuration options (command-line arguments):
    --version <str>            Version of the dataset to parse. Default: "v10"
    --num_digits <int>         Number of significant digits to round the values. Default: 4
    --store_source             Store the source object on the Wayback Machine. Default: False
    --filter_params            Filter the parameters stored to technologies.json. Default: False
    --export_schema            Export the Source/TechnologyCollection schemas. Default: False

Example:
    python src/technologydata/parsers/dea_energy_storage/dea_energy_storage.py --version v10 --num_digits 3 --store_source --filter_params

"""

import logging
import pathlib
import sys

from technologydata.parsers.commons import ArgumentConfig, CommonsParser
from technologydata.parsers.dea_energy_storage import DeaEnergyStorageParser

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse input arguments

    additional_input_args = [
        ArgumentConfig(
            name="--filter_params",
            action="store_true",
            help="filter_params. Filter the parameters stored to technologies.json. Default: false",
        ),
        ArgumentConfig(
            name="--export_schema",
            action="store_true",
            help="export_schema. Export the Source/TechnologyCollection schemas. Default: false",
        ),
    ]

    input_args = CommonsParser.parse_input_arguments(
        additional_arguments=additional_input_args,
        description="Parse the DEA technology storage dataset",
    )
    logger.info("Command line arguments parsed.")

    # Read the raw data
    input_data_path = pathlib.Path(
        path_cwd,
        "src",
        "technologydata",
        "parsers",
        "raw",
        "Technology_datasheet_for_energy_storage.xlsx",
    )

    # --- Initialize and run the parser ---
    dea_parser = DeaEnergyStorageParser()

    if input_args.version not in dea_parser.get_supported_versions():
        logging.error(
            f"Version '{input_args.version}' is not supported. "
            f"Supported versions: {dea_parser.get_supported_versions()}"
        )
        sys.exit(1)

    try:
        dea_parser.parse(
            version=input_args.version,
            input_path=input_data_path,
            num_digits=input_args.num_digits,
            store_source=input_args.store_source,
            filter_params=input_args.filter_params,
            export_schema=input_args.export_schema,
        )

        logging.info(f"Successfully generated files for version {input_args.version} ")

    except (ValueError, FileNotFoundError, KeyError) as e:
        logging.error(f"An error occurred during parsing: {e}")
        sys.exit(1)
