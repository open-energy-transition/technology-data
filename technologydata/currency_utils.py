"""Classes for utils methods."""

from __future__ import annotations

import logging
import pathlib
import re
from collections.abc import Callable
from typing import Any

import pandas as pd
import pydeflate as pyd
from hdx.location.country import Country

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


class CurrencyUtils:
    """
    A utility class for handling currency-related operations.

    This class provides static methods for ensuring currency units, deflating values based on a deflator function, and
    converting and adjusting currency values in a DataFrame.

    Methods
    -------
    ensure_currency_unit(input_string: str, expected_format: str = regex) -> str | None:
        Check if the input string contains a currency unit and extract it if found.

    get_deflate_row_function(base_year: int, deflator_name: str, target_currency: str, year: str, iso_code: str, target_value_column: str):
        Get a function to deflate a row of data based on the specified parameters.

    convert_and_adjust_currency(base_year_val: int, deflator_function_name: str, target_currency: str, pydeflate_path: pathlib.Path, data: pd.DataFrame) -> pd.DataFrame:
        Convert and adjust currency values in a DataFrame using a specified deflator function.

    Examples
    --------
    >>> CurrencyUtils.ensure_currency_unit("The price is USD-2025", "regex")
    'USD-2025'

    >>> CurrencyUtils.ensure_currency_unit("No currency here", "regex")
    None

    >>> CurrencyUtils.convert_and_adjust_currency(
    ...     base_year_val=2020,
    ...     deflator_function_name="example_deflator",
    ...     target_currency="USD",
    ...     pydeflate_path=pathlib.Path("/path/to/deflator"),
    ...     data=pd.DataFrame({"unit": ["USD-2020", "EUR-2020"], "value": [100, 200], "region": ["US", "EU"]})
    ... )
    ...
    # Returns a DataFrame with adjusted currency values.

    """

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
        >>> CurrencyUtils.ensure_currency_unit("The price is USD-2025", r"[A-Z]{3}-\d{4}")
        'USD-2025'
        >>> CurrencyUtils.ensure_currency_unit("No currency here", r"[A-Z]{3}-\d{4}")
        None

        """
        if not isinstance(input_string, str) or not isinstance(expected_format, str):
            raise ValueError("Input must be a string.")

        currency_unit_pattern = re.compile(expected_format)
        match = currency_unit_pattern.search(input_string)
        return match.group(0) if match else None

    @staticmethod
    def replace_currency_code(
        input_string: str,
        new_currency_code: str,
        expected_format: str = r"[A-Z]{3}-\d{4}",
    ) -> str | None:
        """
        Replace the currency code in the input string with a new currency code.

        Parameters
        ----------
        input_string : str
            The string containing the currency unit to be replaced.
        new_currency_code : str
            The new currency code to replace the existing one.
        expected_format: str
            The string expected format.

        Returns
        -------
        str
            The modified string with the currency code replaced, None otherwise.

        Raises
        ------
        ValueError
            If the input_string or the expected_format or the new_currency_code are not a string.

        Examples
        --------
        >>> CurrencyUtils.replace_currency_code("The price is EUR-2025", "USD")
        'The price is USD-2025'
        >>> CurrencyUtils.replace_currency_code("No currency here", "USD")
        None

        """
        if (
            not isinstance(input_string, str)
            or not isinstance(expected_format, str)
            or not isinstance(new_currency_code, str)
        ):
            raise ValueError("Input must be a string.")

        currency_unit = CurrencyUtils.ensure_currency_unit(
            input_string, expected_format
        )
        if currency_unit:
            # Extract the numeric part of the currency unit
            numeric_part = currency_unit.split("-")[1]
            # Construct the new currency unit
            new_currency_unit = f"{new_currency_code}-{numeric_part}"
            # Replace the old currency unit with the new one
            return input_string.replace(currency_unit, new_currency_unit)
        else:
            return None

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
        target_currency_country_code: str,
        pydeflate_path: pathlib.Path,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        # Specify the path where deflator and exchange data will be saved
        if pydeflate_path is not None:
            pyd.set_pydeflate_path(pydeflate_path)
        else:
            raise ValueError(
                "The path where the deflator and exchange data will be saved is None"
            )

        # Validate columns presence
        required_columns = {"unit", "value", "region"}
        if not required_columns.issubset(data.columns):
            missing = required_columns - set(data.columns)
            raise ValueError(f"Input DataFrame is missing required columns: {missing}")

        # Create a copy of the original data to avoid modifying input directly
        results = data.copy()

        # Select rows that correspond to a unit column that fulfills the format <3-letter currency code>-<currency year>
        has_currency_mask = (
            results["unit"].apply(CurrencyUtils.ensure_currency_unit).notna()
        )
        currency_rows = results.loc[has_currency_mask].copy()

        if currency_rows.empty:
            raise ValueError("No rows contain a valid currency unit.")
        else:
            # For each row, extract currency year and currency from the unit column
            currency_rows[["currency", "currency_year"]] = (
                currency_rows["unit"]
                .apply(CurrencyUtils.ensure_currency_unit)
                .str.split("-", expand=True)
            )

            # Cast 'currency_year' column to integer type
            currency_rows["currency_year"] = pd.to_numeric(
                currency_rows["currency_year"], errors="coerce"
            ).astype(int)

        deflate_row_func = CurrencyUtils.get_deflate_row_function(
            base_year=base_year_val,
            deflator_name=deflator_function_name,
            target_currency=target_currency_country_code,
            year="currency_year",
            iso_code="region",
            target_value_column="value",
        )

        target_currency_code = Country.get_currency_from_iso3(
            target_currency_country_code
        )

        adjusted_rows = currency_rows.apply(deflate_row_func, axis=1)

        adjusted_rows = adjusted_rows.drop(columns=["currency", "currency_year"])

        # Replace updated rows back into results DataFrame
        results.loc[has_currency_mask, adjusted_rows.columns] = adjusted_rows

        return results
