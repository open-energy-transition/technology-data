# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""
Data parser for manually specified, USA-specific data from the technology-data repository (`manual_input_usa.csv`).

How to run:
    From the repository root, execute:
        python src/technologydata/parsers/manual_input_usa/manual_input_usa.py

This will regenerate the files `src/technologydata/parsers/manual_input_usa/{sources.json|technologies.json}` with the specified options.
Use the default options to reproduce the file provided with the package.

Configuration options (command-line arguments):
    --num_digits <int>         Number of significant digits to round the values. Default: 4
    --store_source             Store the source object on the Wayback Machine. Default: False

Example:
    python src/technologydata/parsers/manual_input_usa/manual_input_usa.py --num_digits 3 --store_source

"""

import logging
import pathlib
import sys

from technologydata.parsers.commons import ArgumentConfig, CommonsParser
from technologydata.parsers.manual_input_usa import ManualInputUsaParser

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

    # Parse input arguments
    input_args = CommonsParser.parse_input_arguments(
        additional_arguments=additional_input_args,
        description="Parse the technology_data manual_input_usa.csv dataset",
    )
    logger.info("Command line arguments parsed.")

    # Read the raw data
    input_data_path = pathlib.Path(
        path_cwd,
        "src",
        "technologydata",
        "parsers",
        "raw",
        input_args.input_file_name,
    )

    logger.info(f"Input data path set to: {input_data_path}")

    # --- Initialize and run the parser ---
    manual_input_usa_parser = ManualInputUsaParser()

    if input_args.version not in manual_input_usa_parser.get_supported_versions():
        logging.error(
            f"Version '{input_args.version}' is not supported. "
            f"Supported versions: {manual_input_usa_parser.get_supported_versions()}"
        )
        sys.exit(1)

    try:
        manual_input_usa_parser.parse(
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
