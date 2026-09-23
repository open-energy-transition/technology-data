# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Classes for Commons methods for the data parsers."""

import argparse
import re
from enum import StrEnum
from typing import Annotated, Any

import pydantic
from pydantic import BaseModel, ConfigDict


class UnitPatternRegex(StrEnum):
    """
    Enum defining regex patterns for extracting units, carriers, and heating values.

    Each pattern matches a specific format of unit strings commonly found in
    energy technology data. The patterns handle various combinations of:
    - Currency units (USD, EUR) with optional year
    - Energy units (kWh, MWh, GWh, etc.)
    - Mass units (t)
    - Carriers (H2, CH4, CO2, FT, etc.)
    - Time dimensions (/h)
    - Distance dimensions (/km)
    """

    # Pattern 1: Currency with optional year and power/energy carrier
    # Examples: USD_2022/MW_FT, EUR/kWh_H2, EUR_2020/kW_CH4
    CURRENCY_POWER_CARRIER = r"^(USD|EUR)(?:_(\d{4}))?/([kMGT]?Wh?)_([A-Za-z0-9]+)$"

    # Pattern 2: Currency with optional year, mass carrier and time (without parentheses)
    # Examples: USD_2023/t_CO2/h, EUR/t_cement/h
    CURRENCY_MASS_TIME = r"^(USD|EUR)(?:_(\d{4}))?/t_([A-Za-z0-9]+)/h$"

    # Pattern 3: Currency with optional year, mass carrier and time (with parentheses)
    # Examples: EUR/(t_HVC/h), USD_2022/(t_CO2/h)
    CURRENCY_MASS_TIME_PAREN = r"^(USD|EUR)(?:_(\d{4}))?/\(t_([A-Za-z0-9]+)/h\)$"

    # Pattern 4: Energy ratio with carriers
    # Examples: MWh_H2/MWh_FT, MWh_el/MWh_CH4, kWh_NG/kWh_H2
    ENERGY_ENERGY_RATIO = r"^([kMGT]?Wh)_([A-Za-z0-9]+)/([kMGT]?Wh)_([A-Za-z0-9]+)$"

    # Pattern 5: Mass/energy ratio with carriers (order agnostic)
    # Examples: t_CO2/MWh_FT, MWh_el/t_CO2, MWh_H2/t_HLOHC
    # Excludes el/th/thermal carriers which are handled by Pattern 6
    MASS_ENERGY_RATIO = r"^(t|[kMGT]?Wh)_(?!(?:el|th|thermal)/)([A-Za-z0-9]+)/([kMGT]?Wh|t)_([A-Za-z0-9]+)$"

    # Pattern 6: Energy unit with el/th/thermal carrier to mass with carrier
    # Examples: MWh_el/t_CO2, MWh_th/t_cement, kWh_thermal/t_clinker
    ENERGY_THERMAL_MASS = r"^([kMGT]?Wh)_(el|th|thermal)/t_([A-Za-z0-9]+)$"

    # Pattern 7: Currency with generic unit and carrier per time (in parentheses)
    # Examples: EUR/(t_HVC/h), USD/(MW_H2/h)
    CURRENCY_GENERIC_TIME_PAREN = (
        r"^(USD|EUR)(?:_(\d{4}))?/\(([A-Za-z0-9]+)_([A-Za-z0-9]+)/h\)$"
    )

    # Pattern 8: Currency per mass/time with distance dimension
    # Examples: EUR/(t_CO2/h)/km, USD_2023/(t_cement/h)/km
    CURRENCY_MASS_TIME_DISTANCE = r"^(USD|EUR)(?:_(\d{4}))?/\(t_([A-Za-z0-9]+)/h\)/km$"

    # Pattern 9: Currency with optional year and mass carrier (without time)
    # Examples: EUR/t_clinker, USD_2023/t_cement, EUR/t_HVC
    CURRENCY_MASS_CARRIER = r"^(USD|EUR)(?:_(\d{4}))?/t_([A-Za-z0-9]+)$"

    # Pattern 10: Power per distance per power with carriers
    # Examples: MW_e/km/MW_CH4, MW_e/km/MW_H2
    POWER_DISTANCE_POWER = r"^([kMGT]?W)_([A-Za-z0-9]+)/km/([kMGT]?W)_([A-Za-z0-9]+)$"


class UnitCarrierHeatingValueExtractor:
    """Process matched unit patterns into standardized unit, carrier, and heating value tuples."""

    @staticmethod
    def process_currency_power_carrier(match: re.Match[str]) -> tuple[str, str, str]:
        """Process currency with power/energy carrier pattern."""
        currency, year, unit, carrier = match.groups()
        standardized_unit = (
            f"{currency}_{year}/{unit}" if year else f"{currency}/{unit}"
        )
        carrier_str = f"1/{carrier}"
        # Distinguish between power (W) and energy (Wh) units
        heating_value = "LHV" if unit.endswith("h") else "1/LHV"
        return standardized_unit, carrier_str, heating_value

    @staticmethod
    def process_currency_mass_time(match: re.Match[str]) -> tuple[str, str, None]:
        """Process currency with mass carrier and time pattern."""
        currency, year, carrier = match.groups()
        standardized_unit = f"{currency}_{year}/t/h" if year else f"{currency}/t/h"
        carrier_str = f"1/{carrier}"
        return standardized_unit, carrier_str, None

    @staticmethod
    def process_currency_mass_carrier(match: re.Match[str]) -> tuple[str, str, None]:
        """Process currency with mass carrier (without time) pattern."""
        currency, year, carrier = match.groups()
        standardized_unit = f"{currency}_{year}/t" if year else f"{currency}/t"
        carrier_str = carrier
        return standardized_unit, carrier_str, None

    @staticmethod
    def process_energy_ratio(match: re.Match[str]) -> tuple[str, str, str]:
        """Process energy ratio with carriers pattern."""
        unit1, carrier1, unit2, carrier2 = match.groups()
        standardized_unit = f"{unit1}/{unit2}"
        # Normalize "th" to "thermal"
        normalized_carrier1 = "thermal" if carrier1 == "th" else carrier1
        normalized_carrier2 = "thermal" if carrier2 == "th" else carrier2
        carrier_str = f"{normalized_carrier1}/{normalized_carrier2}"
        return standardized_unit, carrier_str, "LHV"

    @staticmethod
    def process_mass_energy_ratio(match: re.Match[str]) -> tuple[str, str, str | None]:
        """Process mass/energy ratio with carriers pattern."""
        unit1, carrier1, unit2, carrier2 = match.groups()
        standardized_unit = f"{unit1}/{unit2}"
        carrier_str = f"{carrier1}/{carrier2}"
        # Determine heating value based on unit types
        heating_value = "LHV" if ("Wh" in unit1 or "Wh" in unit2) else None
        return standardized_unit, carrier_str, heating_value

    @staticmethod
    def process_energy_thermal_mass(match: re.Match[str]) -> tuple[str, str, str]:
        """Process energy unit with el/th/thermal carrier to mass pattern."""
        unit, carrier1, carrier2 = match.groups()
        standardized_unit = f"{unit}/t"
        # Normalize "th" to "thermal"
        normalized_carrier1 = "thermal" if carrier1 == "th" else carrier1
        carrier_str = f"{normalized_carrier1}/{carrier2}"
        return standardized_unit, carrier_str, "LHV"

    @staticmethod
    def process_currency_generic_time(match: re.Match[str]) -> tuple[str, str, None]:
        """Process currency with generic unit and carrier per time pattern."""
        currency, year, unit_type, carrier = match.groups()
        standardized_unit = (
            f"{currency}_{year}/{unit_type}/h" if year else f"{currency}/{unit_type}/h"
        )
        return standardized_unit, f"1/{carrier}", None

    @staticmethod
    def process_currency_mass_time_distance(
        match: re.Match[str],
    ) -> tuple[str, str, None]:
        """Process currency per mass/time with distance dimension pattern."""
        currency, year, carrier = match.groups()
        standardized_unit = (
            f"{currency}_{year}/t/h/km" if year else f"{currency}/t/h/km"
        )
        return standardized_unit, f"1/{carrier}", None

    @staticmethod
    def process_power_distance_power(match: re.Match[str]) -> tuple[str, str, str]:
        """Process power per distance per power with carriers pattern."""
        unit1, carrier1, unit2, carrier2 = match.groups()
        standardized_unit = f"{unit1}/km/{unit2}"
        carrier_str = f"{carrier1}/{carrier2}"
        # Distinguish between power (W) and energy (Wh) units
        heating_value = "1/LHV"
        return standardized_unit, carrier_str, heating_value


class ArgumentConfig(BaseModel):
    """
    Pydantic model for defining argument configurations.

    Allows flexible configuration of command-line arguments with type checking
    and validation.
    """

    name: Annotated[str, pydantic.Field(description="Name of the argument config")]
    arg_type: Annotated[
        type | None,
        pydantic.Field(
            description="The type to which the command-line argument should be converted."
        ),
    ] = None
    default: Annotated[
        Any | None, pydantic.Field(description="Default value of the argument config")
    ] = None
    help: Annotated[
        str | None,
        pydantic.Field(description="A brief description of what the argument does."),
    ] = None
    action: Annotated[
        str | None,
        pydantic.Field(
            description="Specification of how the command-line arguments should be handled"
        ),
    ] = None
    required: Annotated[
        bool, pydantic.Field(description="Flag to check whether field is mondatory")
    ] = False

    # Allow extra fields for maximum flexibility
    model_config = ConfigDict(extra="allow")


class CommonsParser:
    """Commons methods for the data parsers."""

    @staticmethod
    @pydantic.validate_call
    def parse_input_arguments(
        additional_arguments: list[ArgumentConfig] | None = None,
        description: str = "Flexible command line argument parser",
    ) -> argparse.Namespace:
        """
        Parse command line arguments with robust configuration.

        Parameters
        ----------
        additional_arguments : Optional[List[ArgumentConfig]]
            A list of ArgumentConfig objects defining extra arguments.
        description : str
            Description for the argument parser. Defaults to a generic message.

        Returns
        -------
        argparse.Namespace
            Parsed command line arguments

        Examples
        --------
        >>> extra_args = [
        ...     ArgumentConfig(
        ...         name="--input_file",
        ...         arg_type=str,
        ...         required=True,
        ...         help="Path to input CSV file"
        ...     ),
        ...     ArgumentConfig(
        ...         name="--verbose",
        ...         action="store_true",
        ...         help="Enable verbose output"
        ...     )
        ... ]
        >>> args = CommonsParser.parse_input_arguments(additional_arguments=extra_args)

        """
        # Create parser with provided or default description
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        # Default arguments
        default_args = [
            ArgumentConfig(
                name="--num_digits",
                arg_type=int,
                default=4,
                help="Number of significant digits to round the values.",
            ),
            ArgumentConfig(
                name="--archive_source",
                action="store_true",
                help="Archive_source, store the source object on the wayback machine. Default: false",
            ),
            ArgumentConfig(
                name="--version",
                arg_type=str,
                help="Version of the dataset to parse.",
            ),
            ArgumentConfig(
                name="--input_file_name",
                arg_type=str,
                help="Name of the dataset file to parse. Default: None",
                required=True,
            ),
        ]

        # Combine default and additional arguments
        all_arguments = default_args + (additional_arguments or [])

        # Add arguments to parser (Option 1)
        for arg_config in all_arguments:
            # Convert Pydantic model to argparse-compatible dictionary
            arg_dict = {
                k: v
                for k, v in arg_config.model_dump().items()
                if v is not None and k != "name"
            }

            if arg_dict.get("arg_type") is not None:
                arg_dict["type"] = arg_dict.pop("arg_type")

            print("arg_dict", arg_dict)

            # Add argument to parser
            parser.add_argument(arg_config.name, **arg_dict)

        # Parse arguments
        args = parser.parse_args()

        return args
