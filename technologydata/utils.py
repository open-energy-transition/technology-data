"""Classes for utils methods."""

from __future__ import annotations

import logging
import pathlib
import re
from collections.abc import Callable
from enum import Enum
from typing import Any

import pandas as pd
import pydeflate as pyd
from dateutil import parser

logger = logging.getLogger(__name__)


deflation_function_registry = {}


def register_deflator(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Register a deflation function with a given name.

    This decorator function allows you to register a deflation function
    under a specified name in the deflation function registry.

    Parameters
    ----------
    name : str
        The name under which the deflation function will be registered.

    Returns
    -------
    Callable[[Callable], Callable]
        A decorator that registers the provided function as a deflation
        function in the registry.

    Examples
    --------
    >>> @register_deflator('example_deflator')
    ... def example_function(data):
    ...     return data * 0.5

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        deflation_function_registry[name] = func
        return func

    return decorator


@register_deflator("imf_gdp_deflate")
def imf_gdp_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.imf_gdp_deflate.

    Uses GDP deflators and exchange rates from the IMF World Economic Outlook.

    This function acts as a registered deflator under the name "imf_gdp_deflate" and delegates
    all arguments to the underlying `imf_gdp_deflate` function from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.imf_gdp_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.imf_gdp_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.imf_gdp_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `imf_gdp_deflate` function.

    """
    return pyd.imf_gdp_deflate(*args, **kwargs)


@register_deflator("imf_cpi_deflate")
def imf_cpi_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.imf_cpi_deflate.

    Uses Consumer Price Index and exchange rates data from the IMF World Economic Outlook.

    This function acts as a registered deflator under the name "imf_cpi_deflate"
    and delegates all arguments to the underlying `imf_cpi_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.imf_cpi_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.imf_cpi_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.imf_cpi_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `imf_cpi_deflate` function.

    """
    return pyd.imf_cpi_deflate(*args, **kwargs)


@register_deflator("imf_cpi_e_deflate")
def imf_cpi_e_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.imf_cpi_e_deflate.

    Uses end-of-period Consumer Price Index and exchange rates data from the IMF World Economic Outlook.

    This function acts as a registered deflator under the name "imf_cpi_e_deflate"
    and delegates all arguments to the underlying `imf_cpi_e_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.imf_cpi_e_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.imf_cpi_e_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.imf_cpi_e_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `imf_cpi_e_deflate` function.

    """
    return pyd.imf_cpi_e_deflate(*args, **kwargs)


@register_deflator("wb_gdp_deflate")
def wb_gdp_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.wb_gdp_deflate.

    Uses GDP deflators and exchange rates from the World Bank.

    This function acts as a registered deflator under the name "wb_gdp_deflate"
    and delegates all arguments to the underlying `wb_gdp_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.wb_gdp_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.wb_gdp_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.wb_gdp_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `wb_gdp_deflate` function.

    """
    return pyd.wb_gdp_deflate(*args, **kwargs)


@register_deflator("wb_gdp_linked_deflate")
def wb_gdp_linked_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.wb_gdp_linked_deflate.

    Uses the World Bank’s linked GDP deflator and exchange rates data.

    This function acts as a registered deflator under the name "wb_gdp_linked_deflate"
    and delegates all arguments to the underlying `wb_gdp_linked_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.wb_gdp_linked_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.wb_gdp_linked_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.wb_gdp_linked_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `wb_gdp_linked_deflate` function.

    """
    return pyd.wb_gdp_linked_deflate(*args, **kwargs)


@register_deflator("wb_cpi_deflate")
def wb_cpi_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.wb_cpi_deflate.

    Uses Consumer Price Index and exchange rate data from the World Bank.

    This function acts as a registered deflator under the name "wb_cpi_deflate"
    and delegates all arguments to the underlying `wb_cpi_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.wb_cpi_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.wb_cpi_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.wb_cpi_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `wb_cpi_deflate` function.

    """
    return pyd.wb_cpi_deflate(*args, **kwargs)


@register_deflator("oecd_dac_deflate")
def oecd_dac_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Introduce wrapper function for pydeflate.oecd_dac_deflate.

    Uses the OECD DAC deflator series (prices and exchange rates).

    This function acts as a registered deflator under the name "oecd_dac_deflate"
    and delegates all arguments to the underlying `oecd_dac_deflate` function
    from the pydeflate package.

    Parameters
    ----------
    *args : tuple
        Positional arguments to be passed to `pydeflate.oecd_dac_deflate`.
    **kwargs : dict
        Keyword arguments to be passed to `pydeflate.oecd_dac_deflate`.

    Returns
    -------
    pandas.DataFrame
        The DataFrame returned by `pydeflate.oecd_dac_deflate`, containing the
        deflated values according to the specified parameters.

    Notes
    -----
    This wrapper function is primarily used for registration purposes and does
    not modify the behavior or signature of the underlying `oecd_dac_deflate` function.

    """
    return pyd.oecd_dac_deflate(*args, **kwargs)


class DateFormatEnum(str, Enum):
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


class FileExtensionEnum(Enum):
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


class Utils:
    """
    A utility class for various helper functions.

    The class contains static methods that provide utility functions for
    common tasks, such as changing the format of datetime strings. The methods
    in this class are designed to be stateless and can be called without
    instantiating the class.

    Methods
    -------
    change_datetime_format(input_datetime_string: str, output_datetime_format: DateFormatEnum) -> str | None:
        Change the format of a given datetime string to a specified output format.

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
        >>> Utils.change_datetime_format("20250520144500", DateFormatEnum.SOURCES_CSV)
        >>> "2025-05-20 14:45:00"

        """
        try:
            # Automatically detect the format of the input datetime string
            dt = parser.parse(input_datetime_string)
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
    def ensure_currency_unit(
        input_string: str, expected_format: str = r"[A-Z]{3}-\d{4}"
    ) -> str | None:
        r"""
        Check if the input string contains a currency unit.

        The method searches for a substring that matches the expected format and extracts it if found.

        Parameters
        ----------
        input_string : str
            The string to check.
        expected_format : str
            The string with the expected format.

        Returns
        -------
        str
            The matched currency unit if found, None otherwise.

        Raises
        ------
        ValueError
            If the input_string or the expected_format are not a string.

        Examples
        --------
        >>> Utils.ensure_currency_unit("The price is USD-2025", r"[A-Z]{3}-\d{4}")
        'USD-2025'
        >>> Utils.ensure_currency_unit("No currency here", r"[A-Z]{3}-\d{4}")
        None

        """
        if not isinstance(input_string, str) or not isinstance(expected_format, str):
            raise ValueError("Input must be a string.")

        currency_unit_pattern = re.compile(expected_format)
        match = currency_unit_pattern.search(input_string)
        return match.group(0) if match else None

    @staticmethod
    def get_deflate_row_function(
        base_year: int,
        deflator_name: str,
        target_currency: str,
        year: str,
        iso_code: str,
        target_value_column: str,
    ):
        deflation_function = deflation_function_registry.get(deflator_name)
        if deflation_function is None:
            raise ValueError(
                f"Deflator function '{deflator_name}' not found in registry"
            )

        def deflate_row(row):
            row_df = pd.DataFrame([row])
            deflated_df = deflation_function(
                data=row_df,
                base_year=base_year,
                source_currency=row[iso_code],
                target_currency=target_currency,
                id_column=iso_code,
                year_column=year,
                value_column="value",
                target_value_column=target_value_column,
            )
            return deflated_df.iloc[0]

        return deflate_row

    @staticmethod
    def convert_and_adjust_currency(
        base_year_val: int,
        deflator_function_name: str,
        target_currency: str,
        pydeflate_path: pathlib.Path,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        # Specify the path where deflator and exchange data will be saved
        # if pydeflate_path is not None:
        #    pyd.set_pydeflate_path(pydeflate_path)
        # else:
        #    raise ValueError(
        #        "The path where the deflator and exchange data will be saved is None"
        #    )

        # Validate columns presence
        required_columns = {"unit", "value", "region"}
        if not required_columns.issubset(data.columns):
            missing = required_columns - set(data.columns)
            raise ValueError(f"Input DataFrame is missing required columns: {missing}")

        # Create a copy to avoid modifying original data
        results = data.copy()

        # Validate unit column, making sure it fulfills the format <3-letter currency code>-<currency year>
        invalid_rows = results[results["unit"].apply(Utils.ensure_currency_unit).isna()]

        if invalid_rows.empty:
            # For each row, extract currency year and currency from the unit column
            results[["currency", "currency_year"]] = (
                results["unit"]
                .apply(Utils.ensure_currency_unit)
                .str.split("-", expand=True)
            )

            # Cast 'currency_year' column to integer type
            results["currency_year"] = pd.to_numeric(
                results["currency_year"], errors="coerce"
            ).astype(int)
        else:
            details = [
                (idx, val) for idx, val in zip(invalid_rows.index, invalid_rows["unit"])
            ]
            raise ValueError(f"Invalid unit found in rows (index, value): {details}")

        deflate_row_func = Utils.get_deflate_row_function(
            base_year=base_year_val,
            deflator_name=deflator_function_name,
            target_currency=target_currency,
            year="currency_year",
            iso_code="region",
            target_value_column="adjusted_value",
        )

        final_results = results.apply(deflate_row_func, axis=1)

        final_results = final_results.drop(columns=["currency", "currency_year"])

        return final_results

        # TODO: modify the unit, adding the new currency. For example, if you convert from EUR to USD, you need to update the value column from EUR/Mwh_el to USD/Mwh_el
        # TODO: not all rows of the dataframe will contain units containing currencies. Hence you should modify those with the currencies and leave untouched the other rows.
