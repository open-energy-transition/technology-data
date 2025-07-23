# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pint
import pydeflate
from hdx.location.country import Country
from platformdirs import user_cache_dir

logger = logging.getLogger(__name__)

CURRENCY_UNIT_PATTERN = re.compile(r"\b([A-Z]{3})_(\d{4})\b")

# Set up cache directory and file for currency codes
CACHE_DIR = Path(user_cache_dir("technologydata"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CURRENCY_CODES_CACHE = CACHE_DIR / "currency_codes.json"


def get_iso3_to_currency_codes(refresh=False, ignore_cache=False) -> dict[str, str]:
    """
    Get all 3-letter currency codes from official UN data.

    Uses a persistent local cache to avoid unnecessary network requests.

    Parameters
    ----------
    refresh : bool, optional
        If True, the cache will be updated from the internet, by default False.
    ignore_cache : bool, optional
        If True, the cache will not be used and the data will always be fetched from the live feed.

    Returns
    -------
    dict[str, str]
        A dictionary mapping ISO3 country codes to their corresponding 3-letter currency codes.
    """
    if refresh:
        logger.debug("Deleting existing currency codes cache to refresh it.")
        CURRENCY_CODES_CACHE.unlink(missing_ok=True)

    if ignore_cache:
        logger.debug("Ignoring cache and fetching live currency codes.")
        currencies = Country.countriesdata()["currencies"]
    elif not CURRENCY_CODES_CACHE.exists():
        logger.debug(
            "Cache does not exist. Fetching live currency codes and creating cache."
        )
        currencies = Country.countriesdata()["currencies"]
        with open(CURRENCY_CODES_CACHE, "w") as f:
            json.dump(currencies, f)
    else:
        logger.debug("Reading currency codes from cache.")
        with open(CURRENCY_CODES_CACHE, "r") as f:
            currencies = json.load(f)

    return currencies


def extract_currency_units(units: str | pint.Unit) -> list[str]:
    """
    Extract currency-like strings from a string or pint.Unit.

    Parameters
    ----------
    units : str or pint.Unit
        The units string or pint.Unit from which to extract currency-like strings.

    Returns
    -------
    list[str]
        A list of currency-like strings found in the input, formatted as "{3-letter currency code}_{year as YYYY}".
        If no matches are found, an empty list is returned.

    Examples
    --------
    >>> extract_currency_units("USD_2020/kW")
    ["USD_2020"]

    >>> extract_currency_units("EUR_2015/USD_2020")
    ["EUR_2015", "USD_2020"]
    """
    # Ensure that the input is a string
    units = str(units)

    # Get the 3-letter currency codes for all officially recognized currencies
    logger.debug("Retrieving all 3-letter currency codes from the `hdx-country`.")
    all_currency_codes = set(get_iso3_to_currency_codes().values())

    # Check if the units contain a currency-like string, defined as "{3-letter currency code}_{year as YYYY}"
    matches = CURRENCY_UNIT_PATTERN.findall(units)
    if len(matches) == 0:
        logger.debug("No currency-like string found in the units.")
        return []

    # Extract the currency codes from the matches using the regex groups
    logger.debug(f"Found currency-like strings in the units: {matches}")
    currency_codes = {code for code, year in matches}

    # Ensure that all currency codes are legitimate 3-letter currency codes
    invalid_codes = currency_codes - all_currency_codes
    if invalid_codes:
        invalid_currencies = [
            f"{code}_{year}" for code, year in matches if code in invalid_codes
        ]
        raise ValueError(
            f"The following unit(s) appear to be currency units, but have invalid 3-letter currency codes: {', '.join(invalid_currencies)}. "
        )

    # Reconstruct currency units from the matches
    matches = [f"{code}_{year}" for code, year in matches]

    return matches


@lru_cache()
def get_conversion_rate(
    from_currency: str,
    to_currency: str,
    country_iso3: str,
    from_year: int,
    to_year: int,
    source: str = "worldbank",
) -> float:
    """
    Get the conversion rate from one currency (year, ISO3) to another currency (year, ISO3) from pydeflate.

    Parameters
    ----------
    from_currency : str
        The ISO3 code of the country of the currency to convert from (e.g., 'USA' if the source currency is USD).
    to_currency : str
        The ISO3 code of the country of the currency to convert to (e.g., 'DEU' if the target currency is EUR).
    country_iso3 : str
        The ISO3 code of the country to adjust for inflation.
    from_year : int
        The julian year (YYYY) of the source currency.
    to_year : int
        The julian year (YYYY) of the target currency.
    source : str
        The source of the inflation data ('worldbank' or 'international_monetary_fund').
    """
    # Choose the deflation function based on the source
    deflation_function = {
        "worldbank": pydeflate.wb_gdp_deflate,
        "international_monetary_fund": pydeflate.imf_gdp_deflate,
    }[source]

    # pydeflate only operates on pandas.DataFrame
    data = pd.DataFrame(
        {
            "iso3": [country_iso3],
            "from_year": [from_year],
            "value": [1],
        }
    )

    # Deflate values include currency conversion
    conversion_rates = deflation_function(
        data,
        source_currency=from_currency,
        target_currency=to_currency,
        id_column="iso3",
        year_column="from_year",
        base_year=to_year,
        value_column="value",
        target_value_column="new_value",
    )

    return conversion_rates.loc[0, "new_value"]


class UnitRegistry(pint.UnitRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.define("USD_2020 = [currency]")

        self.define(
            "LHV = [lower_heating_value] = lower_heating_value = NCV = net_calorific_value"
        )
        self.define(
            "HHV = [higher_heating_value] = higher_heating_value = GCV = gross_calorific_value"
        )

        self.define("H2 = [hydrogen] = hydrogen")
        self.define("CH4 = [methane] = methane")
        self.define("CO2 = [carbon_dioxide] = carbon_dioxide")
        self.define("CO = [carbon_monoxide] = carbon_monoxide")
        self.define("O2 = [oxygen] = oxygen")
        self.define("N2 = [nitrogen] = nitrogen")
        self.define("H2O = [water] = water")  # TODO avoid warnings for redefinition
        self.define("C = [carbon] = carbon")  # TODO avoid warnings for redefinition

    def get_reference_currency(self) -> str:
        """Get the reference currency from the unit registry."""
        reference_currency = [
            self._units[u].name
            for u in self._units
            if "[currency]" in self._units[u].reference
        ]
        if not reference_currency or len(reference_currency) != 1:
            raise ValueError(
                "The unit registry does not have a unique base currency defined as '[currency]'. Please define a base currency unit to proceed."
            )

        return reference_currency[0]

    def ensure_currency_is_unit(self, units: str) -> None:
        """Ensure that if the units contain a currency-like string, that this currency is defined in the unit registry such that it can be used."""

        currency_units = extract_currency_units(units)

        if not currency_units:
            # Nothing to do
            return

        reference_currency = self.get_reference_currency()

        # Check if the currency unit is already defined in the unit registry
        # if not, define it relative to the base currency USD_2015
        for currency_unit in currency_units:
            if currency_unit in self._units:
                logger.debug(
                    f"Currency unit '{currency_unit}' is already defined in the unit registry. Not redefining it."
                )
                continue

            logger.debug(
                f"Currency unit '{currency_unit}' not found in the unit registry. "
                f"Defining it without a conversion factor relative to the base currency '{reference_currency}'."
            )
            self.define(f"{currency_unit} = nan {reference_currency}")
