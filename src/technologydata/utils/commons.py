# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Classes for Commons methods."""

import argparse
import enum
import logging
import re
from typing import Annotated, Any

import dateutil
import pandas as pd
import pydantic
from pydantic import BaseModel, ConfigDict

from technologydata.utils.units import CURRENCY_UNIT_PATTERN, get_iso3_to_currency_codes

logger = logging.getLogger(__name__)

all_currency_codes = set(get_iso3_to_currency_codes().values())


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


class DateFormatEnum(str, enum.Enum):
    """
    Enum for date formats used in different sources.

    Attributes
    ----------
    SOURCES_CSV : str
        Date format for CSV sources, e.g., "2023-10-01 12:00:00".
    WAYBACK : str
        Date format for Wayback Machine, e.g., "20231001120000".
    NONE : str
        Represents an empty date format.

    """

    SOURCES_CSV = "%Y-%m-%d %H:%M:%S"
    WAYBACK = "%Y%m%d%H%M%S"
    NONE = ""


class FileExtensionEnum(enum.Enum):
    """
    An enumeration that maps various file extensions to their corresponding MIME types.

    This Enum provides a structured way to associate common file extensions with their respective
    MIME types, facilitating easy retrieval of file extensions based on content types. Each member
    of the enumeration is a tuple containing the file extension and its associated MIME type.

    Members
    --------
    TEXT_PLAIN : tuple
        Represents the MIME type "text/plain" with the file extension ".txt".
    TEXT_HTML : tuple
        Represents the MIME type "text/html" with the file extension ".html".
    TEXT_CSV : tuple
        Represents the MIME type "text/csv" with the file extension ".csv".
    TEXT_XML : tuple
        Represents the MIME type "text/xml" with the file extension ".xml".
    APPLICATION_MS_EXCEL : tuple
        Represents the MIME type "application/vnd.ms-excel" with the file extension ".xls".
    APPLICATION_ODS : tuple
        Represents the MIME type "application/vnd.oasis.opendocument.spreadsheet" with the file extension ".ods".
    APPLICATION_OPENXML_EXCEL : tuple
        Represents the MIME type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        with the file extension ".xlsx".
    APPLICATION_JSON : tuple
        Represents the MIME type "application/json" with the file extension ".json".
    APPLICATION_XML : tuple
        Represents the MIME type "application/xml" with the file extension ".xml".
    APPLICATION_PDF : tuple
        Represents the MIME type "application/pdf" with the file extension ".pdf".
    APPLICATION_PARQUET : tuple
        Represents the MIME type "application/parquet" with the file extension ".parquet".
    APPLICATION_VDN_PARQUET : tuple
        Represents the MIME type "application/vdn.apache.parquet" with the file extension ".parquet".
    APPLICATION_RAR_WINDOWS : tuple
        Represents the MIME type "application/x-rar-compressed" with the file extension ".rar".
    APPLICATION_RAR : tuple
        Represents the MIME type "application/vnd.rar" with the file extension ".rar".
    APPLICATION_ZIP : tuple
        Represents the MIME type "application/zip" with the file extension ".zip".
    APPLICATION_ZIP_WINDOWS : tuple
        Represents the MIME type "application/x-zip-compressed" with the file extension ".zip".
    """

    TEXT_PLAIN = (".txt", "text/plain")
    TEXT_HTML = (".html", "text/html")
    TEXT_CSV = (".csv", "text/csv")
    TEXT_XML = (".xml", "text/xml")
    APPLICATION_MS_EXCEL = (".xls", "application/vnd.ms-excel")
    APPLICATION_ODS = (".ods", "application/vnd.oasis.opendocument.spreadsheet")
    APPLICATION_OPENXML_EXCEL = (
        ".xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    APPLICATION_JSON = (".json", "application/json")
    APPLICATION_XML = (".xml", "application/xml")
    APPLICATION_PDF = (".pdf", "application/pdf")
    APPLICATION_PARQUET = (".parquet", "application/parquet")
    APPLICATION_VDN_PARQUET = (".parquet", "application/vdn.apache.parquet")
    APPLICATION_RAR_WINDOWS = (".rar", "application/x-rar-compressed")
    APPLICATION_RAR = (".rar", "application/vnd.rar")
    APPLICATION_ZIP = (".zip", "application/zip")
    APPLICATION_ZIP_WINDOWS = (".zip", "application/x-zip-compressed")

    @classmethod
    def get_extension(cls, content_type: str) -> str | None:
        """
        Retrieve the file extension associated with a given MIME type.

        Parameters
        ----------
        content_type : str
            The MIME type for which the corresponding file extension is to be retrieved.

        Returns
        -------
        str | None
            The file extension associated with the given MIME type, or None if the
            MIME type is not supported.

        Examples
        --------
        >>> FileExtensionEnum.get_extension("application/pdf")
        >>> '.pdf'

        >>> FileExtensionEnum.get_extension("application/unknown")
        >>> None

        """
        for member in cls:
            if member.value[1] == content_type:
                return member.value[0]
        return None

    @classmethod
    def search_file_extension_in_url(cls, url: str) -> str | None:
        """
        Search for the file extension in a given URL.

        Parameters
        ----------
        url : str
            The URL to search for the file extension.

        Returns
        -------
        str | None
            The file extension, or None if no match is found.

        Examples
        --------
        >>> FileExtensionEnum.search_file_extension_in_url("https://example.com/file.pdf")
        '.pdf'

        >>> FileExtensionEnum.search_file_extension_in_url("https://example.com/file.unknown")
        None

        """
        for member in cls:
            if re.search(r"\b" + re.escape(member.value[0]) + r"\b", url):
                return member.value[0]
        return None


class Commons:
    """
    A utility class for various helper functions.

    This class provides static methods for common tasks, such as changing the format of datetime strings and replacing
    special characters in strings. The methods are stateless and can be called without instantiating the class.

    Methods
    -------
    change_datetime_format(input_datetime_string: str, output_datetime_format: DateFormatEnum) -> str | None:
        Change the format of a given datetime string to a specified output format.
    replace_special_characters(input_string: str) -> str:
        Replace special characters and spaces in a string with underscores.

    Examples
    --------
    >>> Commons.change_datetime_format("20250520144500", DateFormatEnum.SOURCES_CSV)
    '2025-05-20 14:45:00'
    >>> Commons.replace_special_characters("Hello, World! Welcome to Python @ 2023.")
    'hello_world_welcome_to_python_2023'

    """

    @staticmethod
    def change_datetime_format(
        input_datetime_string: str,
        output_datetime_format: DateFormatEnum,
    ) -> str | Any:
        """
        Change the format of a given datetime string to a specified output format.

        The method takes a datetime string and automatically detects its format, then converts it to the specified output format.
        If the input string cannot be parsed, it logs an error and returns None.

        Parameters
        ----------
        input_datetime_string : str
            datetime string that needs to be reformatted

        output_datetime_format : DateFormatEnum
            desired format for the output datetime string, following the strftime format codes.

        Returns
        -------
           str | None
               reformatted datetime string if successful, otherwise None

        Raises
        ------
        ValueError
            If the input datetime string cannot be parsed.

        Examples
        --------
        >>> Commons.change_datetime_format("20250520144500", DateFormatEnum.SOURCES_CSV)
        >>> "2025-05-20 14:45:00"

        """
        try:
            # Automatically detect the format of the input datetime string
            dt = dateutil.parser.parse(input_datetime_string)
            logger.debug(f"The datetime string has been parsed successfully: {dt}")
            output_datetime_string = dt.strftime(output_datetime_format.value)
            logger.debug(f"The format is now changed to {output_datetime_format.value}")
            return output_datetime_string
        except ValueError as e:
            raise ValueError(f"Error during datetime formatting: {e}")

    @staticmethod
    def replace_special_characters(input_string: str) -> str:
        """
        Replace special characters and spaces in a string.

        The method replaces special characters and spaces in a string with underscores,
        collapsing multiple consecutive underscores into a single underscore. Finally, it lowercases all characters of the string and removes leading or
        trailing underscores.

        Parameters
        ----------
        input_string : str
            The input string from which special characters and spaces will be replaced.

        Returns
        -------
        str
            A new string with all special characters and spaces replaced by a single underscore
            where consecutive underscores occur.

        Examples
        --------
        >>> replace_special_characters("Hello, World! Welcome to Python @ 2023.")
        'hello_world_welcome_to_python_2023'

        >>> replace_special_characters("Special#Characters$Are%Fun!")
        'special_characters_are_fun'

        """
        # Replace any character that is not a word character or whitespace with underscore
        replaced = re.sub(r"[^\w\s]", "_", input_string)
        # Replace whitespace with underscore
        replaced = replaced.replace(" ", "_")
        # Collapse multiple consecutive underscores into a single underscore
        replaced = re.sub(r"_+", "_", replaced)
        # Remove leading and trailing underscores
        replaced = replaced.strip("_")
        # Lower case the string
        replaced = replaced.casefold()
        return replaced

    @staticmethod
    def update_unit_with_currency_year(unit: str, currency_year: str) -> str:
        """
        Update unit string to include currency year for currency-based units.

        Parameters
        ----------
        unit : str
            A unit string
        currency_year: str
            A currency year string

        Returns
        -------
        str
            Updated unit

        """
        # Check if the units contain a currency-like string, defined as "{3-letter currency code}_{year as YYYY}"
        matches = CURRENCY_UNIT_PATTERN.findall(unit)

        # Check if unit is a string, contains the currency, and currency_year is not null
        if isinstance(unit, str) and pd.notna(currency_year):
            for currency_code in all_currency_codes:
                if (
                    pd.notna(currency_code)
                    and currency_code in unit
                    and len(matches) == 0
                ):
                    # Replace currency with currency_currency_year
                    unit = unit.replace(
                        currency_code, f"{currency_code}_{currency_year}"
                    )

        return unit

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
        >>> args = Commons.parse_input_arguments(additional_arguments=extra_args)

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
                name="--store_source",
                action="store_true",
                help="Store_source, store the source object on the wayback machine. Default: false",
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
