"""Classes for Currencies methods."""

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


def _register_deflator(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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
    >>> @_register_deflator('example_deflator')
    ... def example_function(data):
    ...     return data * 0.5

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        deflation_function_registry[name] = func
        return func

    return decorator


@_register_deflator("imf_gdp_deflate")
def _imf_gdp_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
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


@_register_deflator("wb_gdp_deflate")
def _wb_gdp_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
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


@_register_deflator("wb_gdp_linked_deflate")
def _wb_gdp_linked_deflate_wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
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


class Currencies:
    """
    A utility class for handling currency-related operations.

    This class provides static methods for ensuring currency units, deflating values based on a deflator function, and
    converting and adjusting currency values in a DataFrame.

    Methods
    -------
    extract_currency_unit(input_string: str, expected_format: str = regex) -> str | None:
        Check if the input string contains a currency unit and extract it if found.

    get_deflate_row_function(base_year: int, deflator_name: str, target_currency: str, year: str, iso_code: str, target_value_column: str):
        Get a function to deflate a row of data based on the specified parameters.

    adjust_currency(base_year_val: int, deflator_function_name: str, target_currency: str, pydeflate_path: pathlib.Path, data: pd.DataFrame) -> pd.DataFrame:
        Convert and adjust currency values in a DataFrame using a specified deflator function.

    Examples
    --------
    >>> Currencies.extract_currency_unit("The price is USD-2025", "regex")
    'USD-2025'

    >>> Currencies.extract_currency_unit("No currency here", "regex")
    None

    >>> Currencies.adjust_currency(
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
    def extract_currency_unit(
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
        >>> Currencies.extract_currency_unit("The price is USD-2025", r"[A-Z]{3}-\d{4}")
        'USD-2025'
        >>> Currencies.extract_currency_unit("No currency here", r"[A-Z]{3}-\d{4}")
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
        >>> Currencies.replace_currency_code("The price is EUR-2025", "USD")
        'The price is USD-2025'
        >>> Currencies.replace_currency_code("No currency here", "USD")
        None

        """
        if (
            not isinstance(input_string, str)
            or not isinstance(expected_format, str)
            or not isinstance(new_currency_code, str)
        ):
            raise ValueError("Input must be a string.")

        currency_unit = Currencies.extract_currency_unit(input_string, expected_format)
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
        year: str,
        iso_code: str,
        target_value_column: str,
        use_case_flag: str,
        target_currency: str | None = None,
    ) -> Callable[[pd.Series], pd.Series]:
        """
        Retrieve a function to deflate a row of data based on specified parameters.

        This method retrieves a deflation function from the registry using the provided deflator name
        and returns a closure that can be used to deflate a single row of data. The returned function
        takes a row as input and applies the deflation logic to it, returning the deflated row.

        Parameters
        ----------
        base_year : int
            The base year to which the values should be deflated.
        deflator_name : str
            The name of the deflation function to retrieve from the registry.
        year : str
            The name of the column that contains the year information for deflation.
        iso_code : str
            The name of the column that contains the ISO code for the currency.
        target_value_column : str
            The name of the column that contains the target value to be adjusted.
        use_case_flag : str
            A flag indicating the use case: "currency_conversion" or "inflation_adjustment".
        target_currency : str, optional
            The ISO3 country code representing the target currency to convert to. Required if use_case_flag is "currency_conversion".
            Ignored if use_case_flag is "inflation_adjustment".

        Returns
        -------
        Callable[[pd.Series], pd.Series]
            A function that takes a row (as a pandas Series) and returns the deflated row (as a pandas Series).

        Raises
        ------
        ValueError
            If the specified deflator function name is not found in the deflation function registry.
            Or if use_case_flag is not one of the allowed values.
            Or if use_case_flag is "currency_conversion" and target_currency is not provided.

        Examples
        --------
        >>> deflator_func = Currencies.get_deflate_row_function(
        ...     base_year=2022,
        ...     deflator_name='cpi_deflator',
        ...     year='currency_year',
        ...     iso_code='region',
        ...     target_value_column='value',
        ...     use_case_flag='currency_conversion'
        ...     target_currency='USD',
        ... )
        >>> deflated_row = deflator_func(row)  # where row is a pandas Series
        >>> deflator_func_inflation = Currencies.get_deflate_row_function(
        ...     base_year=2022,
        ...     deflator_name='cpi_deflator',
        ...     year='currency_year',
        ...     iso_code='region',
        ...     target_value_column='value',
        ...     use_case_flag='inflation_adjustment'
        ... )

        """
        # Validate use_case_flag
        if use_case_flag.casefold() not in (
            "currency_conversion",
            "inflation_adjustment",
        ):
            raise ValueError(
                "use_case_flag must be either 'currency_conversion' or 'inflation_adjustment'"
            )

        if (
            use_case_flag.casefold() == "currency_conversion"
            and target_currency is None
        ):
            raise ValueError(
                "target_currency must be provided when use_case_flag is 'currency_conversion'"
            )

        deflation_function = deflation_function_registry.get(deflator_name)
        if deflation_function is None:
            raise ValueError(
                f"Deflator function '{deflator_name}' not found in registry"
            )

        def deflate_row(row: pd.Series) -> pd.Series:
            row_df = pd.DataFrame([row])

            # Adjust target_currency based on use_case_flag
            if use_case_flag.casefold() == "inflation_adjustment":
                currency_to_use = row[iso_code]
            else:
                currency_to_use = target_currency

            deflated_df = deflation_function(
                data=row_df,
                base_year=base_year,
                source_currency=row[iso_code],
                target_currency=currency_to_use,
                id_column=iso_code,
                year_column=year,
                value_column="value",
                target_value_column=target_value_column,
            )
            return deflated_df.iloc[0]

        return deflate_row

    @staticmethod
    def adjust_currency(
        base_year_val: int,
        pydeflate_path: pathlib.Path,
        data: pd.DataFrame,
        use_case_flag: str,
        target_currency: str | None = None,
        deflator_function_name: str = "wb_gdp_deflate",
    ) -> pd.DataFrame:
        """
        Convert and/or adjust currency values in a DataFrame to a target currency and base year using deflation.

        This function adjusts the currency values in the input DataFrame by deflating and/or converting
        them to a specified target currency and base year. It identifies rows with currency units
        matching the format `<CURRENCY_CODE>-<YEAR>`, applies a deflator function to adjust the values,
        and updates the currency codes in the 'unit' column accordingly.

        Parameters
        ----------
        base_year_val : int
            The base year to which the currency values should be adjusted.
        pydeflate_path : pathlib.Path
            The file system path where deflator and exchange rate data will be saved or loaded from.
        data : pandas.DataFrame
            The input DataFrame containing at least the columns 'unit', 'value', and 'region'.
            The 'unit' column must have currency codes in the format `<3-letter currency code>-<year>`.
        use_case_flag : str
            A flag indicating the use case: "currency_conversion" or "inflation_adjustment".
        target_currency : Optional[str], optional
            The ISO3 country code representing the target currency to convert to. This argument is required
            if `use_case_flag` is "currency_conversion". It is ignored if `use_case_flag` is
            "inflation_adjustment". Default is None.
        deflator_function_name : str
            The name of the deflation function to use from the deflation function registry. Default is "wb_gdp_deflate".

        Returns
        -------
        pandas.DataFrame
            A DataFrame with currency values deflated to the specified base year and converted to the
            target currency. The 'unit' column will have updated currency codes reflecting the target currency.

        Raises
        ------
        ValueError
            If `pydeflate_path` is None.
            If any of the required columns ('unit', 'value', 'region') are missing from the input DataFrame.
            If no rows in the DataFrame contain a valid currency unit matching the expected pattern.
            If the specified deflator function name is not found in the deflation function registry.
            If `use_case_flag` is not one of the allowed values.
            If `target_currency` is required but not provided when `use_case_flag` is "currency_conversion".

        Examples
        --------
        >>> data = pd.DataFrame({
        ...     'unit': ['USD-2020', 'EUR-2021', 'JPY-2019'],
        ...     'value': [100, 200, 300],
        ...     'region': ['USA', 'FRA', 'JPN']
        ... })
        >>> adjusted_data = Currencies.adjust_currency(
        ...     base_year_val=2022,
        ...     target_currency='USD',
        ...     pydeflate_path=pathlib.Path('/path/to/data'),
        ...     data=data,
        ...     deflator_function_name='some_name',
        ... )
        >>> adjusted_data['unit']
        0    USD-2022
        1    USD-2022
        2    USD-2022
        Name: unit, dtype: object

        """
        if use_case_flag.casefold() not in (
            "currency_conversion",
            "inflation_adjustment",
        ):
            raise ValueError(
                "use_case_flag must be either 'currency_conversion' or 'inflation_adjustment'"
            )

        if (
            use_case_flag.casefold() == "currency_conversion"
            and target_currency is None
        ):
            raise ValueError(
                "target_currency must be provided when use_case_flag is 'currency_conversion'"
            )

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
            raise ValueError(f"Input dataFrame is missing required columns: {missing}")

        # Create a copy of the original data to avoid modifying input directly
        results = data.copy()

        # Select rows that correspond to a unit column that fulfills the format <3-letter currency code>-<currency year>
        has_currency_mask = (
            results["unit"].apply(Currencies.extract_currency_unit).notna()
        )
        currency_rows = results.loc[has_currency_mask].copy()

        if currency_rows.empty:
            logger.warning("No rows contain a valid currency unit.")
        else:
            # For each row, extract currency year and currency from the unit column
            currency_rows[["currency", "currency_year"]] = (
                currency_rows["unit"]
                .apply(Currencies.extract_currency_unit)
                .str.split("-", expand=True)
            )

            # Cast 'currency_year' column to integer type
            currency_rows["currency_year"] = pd.to_numeric(
                currency_rows["currency_year"], errors="coerce"
            ).astype(int)

        # Use match statement to determine the deflation function
        match use_case_flag.casefold():
            case "currency_conversion":
                deflate_row_func = Currencies.get_deflate_row_function(
                    base_year=base_year_val,
                    deflator_name=deflator_function_name,
                    year="currency_year",
                    iso_code="region",
                    target_value_column="value",
                    use_case_flag=use_case_flag,
                    target_currency=target_currency,
                )
            case "inflation_adjustment":
                deflate_row_func = Currencies.get_deflate_row_function(
                    base_year=base_year_val,
                    deflator_name=deflator_function_name,
                    year="currency_year",
                    iso_code="region",
                    target_value_column="value",
                    use_case_flag=use_case_flag,
                )
            case _:
                raise ValueError("Invalid use_case_flag provided.")

        adjusted_rows = currency_rows.apply(deflate_row_func, axis=1)

        adjusted_rows = adjusted_rows.drop(columns=["currency", "currency_year"])

        # Replace updated rows back into results DataFrame
        results.loc[has_currency_mask, adjusted_rows.columns] = adjusted_rows

        if use_case_flag.casefold() == "currency_conversion":
            target_currency_code = Country.get_currency_from_iso3(target_currency)

            # Update the 'unit' column with the new currency code
            results.loc[has_currency_mask, "unit"] = currency_rows["unit"].apply(
                lambda unit: Currencies.replace_currency_code(
                    unit, target_currency_code
                )
            )

        return results
