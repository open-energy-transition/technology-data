# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Data parser for the manual_input_usa.csv data set."""
import argparse
import logging
import pathlib
import pandas

from technologydata import Source, TechnologyCollection, SourceCollection, Parameter, Technology

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


def build_technology_collection(
    dataframe: pandas.DataFrame,
    sources_path: pathlib.Path,
    store_source: bool = False,
) -> TechnologyCollection:
    """
    Compute a collection of technologies from a grouped DataFrame.

    Processes input DataFrame by grouping technologies and extracting their parameters,
    creating Technology instances for each unique group.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Input DataFrame containing technology parameters.
        Expected columns include:
        - 'scenario': Estimation or case identifier
        - 'year': Year of the technology
        - 'technology': Detailed technology name
        - 'parameter': Parameter name
        - 'value': Parameter value
        - 'unit': Parameter units
        - 'further_description': Extra information about the technology
        - 'financial_case': Technology financial case
    sources_path: pathlib.Path
        Output path for storing the SourceCollection object
    store_source: Optional[bool]
        Flag to decide whether to store the source object on the Wayback Machine. Default False.

    Returns
    -------
    TechnologyCollection
        A collection of Technology instances, each representing a unique
        technology group with its associated parameters.

    Notes
    -----
    - The function groups the DataFrame by 'est', 'year', 'ws', and 'Technology'
    - For each group, it creates a dictionary of Parameters
    - Each Technology is instantiated with group-specific attributes

    """
    parameters = {}
    list_techs = []

    if store_source:
        source = Source(
            title="Energy system technology data for the US",
            authors="Contributors to technology-data. Data source: manual_input_usa.csv",
            url="https://github.com/PyPSA/technology-data/blob/master/inputs/US/manual_input_usa.csv",
        )
        #source.ensure_in_wayback()
        sources = SourceCollection(sources=[source])
        sources.to_json(sources_path)
    else:
        sources = SourceCollection.from_json(sources_path)

    for (scenario, year, technology), group in dataframe.groupby(
        ["scenario", "year", "technology"]
    ):
        for _, row in group.iterrows():
            parameters[row["parameter"]] = Parameter(
                magnitude=row["value"], units=row["unit"], note=row["further_description"], provenance=row["financial_case"], sources=sources
            )
        list_techs.append(
            Technology(
                name=technology,
                region="US",
                year=year,
                parameters=parameters,
                case=scenario,
                detailed_technology=technology,
            )
        )
    return TechnologyCollection(technologies=list_techs)


def parse_input_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command line arguments containing:
        - Number of significant digits
        - Store source flag

    """
    # Create the parser
    parser = argparse.ArgumentParser(
        description="Parse the DEA technology storage dataset",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Define arguments
    parser.add_argument(
        "--num_digits",
        type=int,
        default=4,
        help="Name of significant digits to round the values. ",
    )

    parser.add_argument(
        "--store_source",
        action="store_true",
        help="Store_source, store the source object on the wayback machine. Default: false",
    )

    # Parse arguments
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # Parse input arguments
    input_args = parse_input_arguments()
    logger.info("Command line arguments parsed.")
