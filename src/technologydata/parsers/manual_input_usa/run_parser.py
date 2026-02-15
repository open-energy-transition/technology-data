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