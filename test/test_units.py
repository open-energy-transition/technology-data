# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT
"""Test the creation of custom units and handling of currencies using Pint."""

import json

import pint
import pytest

from technologydata.utils.units import (
    CURRENCY_CODES_CACHE,
    UnitRegistry,
    extract_currency_units,
    get_conversion_rate,
    get_iso3_to_currency_codes,
)


class TestExtractCurrencyUnits:
    """Test cases for extract_currency_units function."""

    def test_single_currency_unit(self) -> None:
        """Test extraction of a single currency unit."""
        result = extract_currency_units("USD_2020/kW")
        assert result == ["USD_2020"]

    def test_multiple_currency_units(self) -> None:
        """Test extraction of multiple currency units."""
        result = extract_currency_units("EUR_2015/USD_2020")
        assert set(result) == {"EUR_2015", "USD_2020"}

    def test_no_currency_units(self) -> None:
        """Test that no currency units are extracted from non-currency strings."""
        result = extract_currency_units("kW/hour")
        assert result == []

    def test_empty_string(self) -> None:
        """Test extraction from empty string."""
        result = extract_currency_units("")
        assert result == []

    def test_pint_unit(self) -> None:
        """Test extraction from pint.Unit object."""
        ureg = pint.UnitRegistry()
        ureg.define("USD_2020 = [currency]")
        unit = pint.Unit("USD_2020")
        result = extract_currency_units(unit)
        assert result == ["USD_2020"]

        ureg.define("USD_2020 = [currency]")
        unit = pint.Unit("USD_2020/kW")
        result = extract_currency_units(unit)
        assert result == ["USD_2020"]

    def test_pint_unit_input(self) -> None:
        """Test that pint.Unit objects are properly converted to strings."""
        ureg = pint.UnitRegistry()
        unit = ureg.parse_expression("kW")
        result = extract_currency_units(unit)
        assert result == []

    def test_complex_unit_string(self) -> None:
        """Test extraction from complex unit strings with multiple components."""
        result = extract_currency_units("USD_2020/kW/year")
        assert result == ["USD_2020"]

    def test_invalid_year_format(self) -> None:
        """Test that invalid year formats are not matched."""
        result = extract_currency_units("USD_20/kW")
        assert result == []

        result = extract_currency_units("USD_20200/kW")
        assert result == []

    def test_non_three_letter_codes(self) -> None:
        """Test that non-three-letter codes are not matched."""
        result = extract_currency_units("US_2020/kW")
        assert result == []

        result = extract_currency_units("USDD_2020/kW")
        assert result == []

    def test_case_sensitivity(self) -> None:
        """Test that currency codes must be uppercase."""
        result = extract_currency_units("usd_2020/kW")
        assert result == []

    def test_valid_currency_codes(self) -> None:
        """Test that only valid currency codes are accepted."""
        result = extract_currency_units("USD_2020/kW")
        assert result == ["USD_2020"]

        result = extract_currency_units("EUR_2015/kW")
        assert result == ["EUR_2015"]

        with pytest.raises(ValueError):
            extract_currency_units("EUA_2015/kW")

    def test_invalid_currency_codes_raise(self) -> None:
        """Test that invalid currency codes raise ValueError."""
        with pytest.raises(ValueError):
            extract_currency_units("XYZ_2020/kW")

    def test_duplicate_currency_units(self) -> None:
        """Test that duplicate currency units are handled correctly."""
        result = extract_currency_units("USD_2020/USD_2020/EUR_2015")
        assert result == ["USD_2020", "USD_2020", "EUR_2015"]

    def test_different_years_same_currency(self) -> None:
        """Test extraction of same currency with different years."""
        result = extract_currency_units("USD_2020/USD_2015")
        assert result == ["USD_2020", "USD_2015"]

    def test_mixed_valid_invalid_currencies(self) -> None:
        """Test behavior with mix of valid and invalid currency codes."""
        with pytest.raises(ValueError):
            extract_currency_units("USD_2020/XYZ_2021")


class TestGetIso3ToCurrencyCodes:
    """Test cases for get_iso3_to_currency_codes function and whether the cache works correctly."""

    def test_correct_currency_codes(self) -> None:
        """Test that the function returns correct currency codes."""
        codes = get_iso3_to_currency_codes()

        # dtype check
        assert isinstance(codes, dict)

        # check some known currency codes
        assert "USD" in codes.values()
        assert "EUR" in codes.values()

        # check wrong currency codes
        assert "EUA" not in codes.values()  # EUA is not a valid currency code
        assert "usd" not in codes.values()  # codes must be uppercase

        assert all(len(iso3) == 3 for iso3 in codes.keys()), (
            "All ISO3 codes should be 3 letters long"
        )
        assert all(iso3.isupper() for iso3 in codes.keys()), (
            "All ISO3 codes should be uppercase"
        )
        assert all([len(code) == 3 for code in codes.values() if code]), (
            "All currency codes should be 3 letters long"
        )
        assert all([code.isupper() for code in codes.values() if code]), (
            "All currency codes should be uppercase"
        )

    def test_currency_cache_creates_and_reads(self) -> None:
        """Test that the cache is properly created/read/ignored."""
        # Ensure the cache does not exist before the test
        CURRENCY_CODES_CACHE.unlink(missing_ok=True)

        # First call should create cache
        codes = get_iso3_to_currency_codes()
        assert CURRENCY_CODES_CACHE.exists()

        # Second call should read from cache (simulate by modifying file)
        dummy_data = {"FOO": "BAR"}
        with open(CURRENCY_CODES_CACHE, "w") as f:
            json.dump(dummy_data, f)
        codes = get_iso3_to_currency_codes()
        assert codes == dummy_data

        # Bypass cache to ensure it reads from the live feed (FOO should not be there)
        codes = get_iso3_to_currency_codes(ignore_cache=True)
        assert codes != dummy_data

        # Force refresh should overwrite cache
        codes = get_iso3_to_currency_codes(refresh=True)
        assert codes != dummy_data


class TestGetConversionRate:
    """Test cases for get_conversion_rate function."""

    def test_same_currency_same_year(self) -> None:
        """Test conversion rate when currency and year are the same."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="USA",
            country_iso3="USA",
            from_year=2020,
            to_year=2020,
        )
        assert rate == pytest.approx(1.0, rel=1e-6)

    def test_different_years_same_currency(self) -> None:
        """Test conversion rate with different years but same currency."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="USA",
            country_iso3="USA",
            from_year=2015,
            to_year=2020,
        )
        # Rate should not be 1.0 due to inflation adjustment
        assert rate != 1.0
        assert isinstance(rate, float)
        assert rate > 0

    def test_different_currencies_same_year(self) -> None:
        """Test conversion rate with different currencies but same year."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="DEU",
            country_iso3="USA",
            from_year=2020,
            to_year=2020,
        )
        # Rate should not be 1.0 due to currency conversion
        assert rate != 1.0
        assert isinstance(rate, float)
        assert rate > 0

    def test_different_currencies_different_years(self) -> None:
        """Test conversion rate with different currencies and years."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="DEU",
            country_iso3="USA",
            from_year=2015,
            to_year=2020,
        )
        assert isinstance(rate, float)
        assert rate > 0

    def test_worldbank_source(self) -> None:
        """Test conversion rate using World Bank data source."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="USA",
            country_iso3="USA",
            from_year=2015,
            to_year=2020,
            source="worldbank",
        )
        assert isinstance(rate, float)
        assert rate > 0

    def test_imf_source(self) -> None:
        """Test conversion rate using IMF data source."""
        rate = get_conversion_rate(
            from_currency="USA",
            to_currency="USA",
            country_iso3="USA",
            from_year=2015,
            to_year=2020,
            source="international_monetary_fund",
        )
        assert isinstance(rate, float)
        assert rate > 0

    def test_invalid_source_raises_keyerror(self) -> None:
        """Test that invalid source raises KeyError."""
        with pytest.raises(KeyError):
            get_conversion_rate(
                from_currency="USA",
                to_currency="USA",
                country_iso3="USA",
                from_year=2020,
                to_year=2020,
                source="invalid_source",
            )

    def test_caching_behavior(self) -> None:
        """Test that function results are cached."""
        # Call function twice with same parameters
        rate1 = get_conversion_rate(
            from_currency="USA",
            to_currency="DEU",
            country_iso3="USA",
            from_year=2018,
            to_year=2019,
        )
        rate2 = get_conversion_rate(
            from_currency="USA",
            to_currency="DEU",
            country_iso3="USA",
            from_year=2018,
            to_year=2019,
        )

        # Results should be identical (cached)
        assert rate1 == rate2


class TestUnitRegistryGetReferenceCurrency:
    """Test cases for UnitRegistry.get_reference_currency method."""

    def test_single_reference_currency(self) -> None:
        """Test that get_reference_currency returns the correct currency when one is defined."""
        ureg = UnitRegistry()
        # UnitRegistry already defines USD_2020 as [currency] in __init__
        reference = ureg.get_reference_currency()
        assert reference == "USD_2020"

    def test_no_reference_currency_raises_error(self) -> None:
        """Test that ValueError is raised when no reference currency is defined."""
        # Use base pint registry without currency definitions
        ureg = UnitRegistry()

        ureg.define(
            "USD_2020 = [not_a_currency]"
        )  # Overwrite the default currency definition to not be a currency

        with pytest.raises(ValueError, match="does not have a unique base currency"):
            ureg.get_reference_currency()

    def test_multiple_reference_currencies_raises_error(self) -> None:
        """Test that ValueError is raised when multiple currencies are defined."""
        ureg = UnitRegistry()
        ureg.define("EUR_2015 = [currency]")

        with pytest.raises(ValueError, match="does not have a unique base currency"):
            ureg.get_reference_currency()


class TestUnitRegistryEnsureCurrencyIsUnit:
    """Test cases for UnitRegistry.ensure_currency_is_unit method."""

    def test_no_currency_units_does_nothing(self) -> None:
        """Test that method does nothing when no currency units are present."""
        ureg = UnitRegistry()
        initial_units = set(ureg._units.keys())

        ureg.ensure_currency_is_unit("kW/hour")

        # No new units should be added
        assert set(ureg._units.keys()) == initial_units

    def test_empty_string_does_nothing(self) -> None:
        """Test that method does nothing with empty string."""
        ureg = UnitRegistry()
        initial_units = set(ureg._units.keys())

        ureg.ensure_currency_is_unit("")

        # No new units should be added
        assert set(ureg._units.keys()) == initial_units

    def test_already_defined_currency_not_redefined(self) -> None:
        """Test that already defined currency units are not redefined."""
        ureg = UnitRegistry()
        # USD_2020 is already defined in UnitRegistry.__init__

        # Should not raise an error or redefine
        ureg.ensure_currency_is_unit("USD_2020/kW")

        # Verify USD_2020 is still defined
        assert "USD_2020" in ureg._units

    def test_new_currency_unit_gets_defined(self) -> None:
        """Test that new currency units get defined relative to reference currency."""
        ureg = UnitRegistry()

        # EUR_2015 should not be defined initially
        assert "EUR_2015" not in ureg._units

        ureg.ensure_currency_is_unit("EUR_2015/kW")

        # EUR_2015 should now be defined
        assert "EUR_2015" in ureg._units

        # Verify it's defined relative to the reference currency (USD_2020)
        eur_unit = ureg._units["EUR_2015"]
        assert "USD_2020" in str(eur_unit)

    def test_multiple_currency_units_get_defined(self) -> None:
        """Test that multiple new currency units get defined."""
        ureg = UnitRegistry()

        # Neither should be defined initially
        assert "EUR_2015" not in ureg._units
        assert "GBP_2018" not in ureg._units

        ureg.ensure_currency_is_unit("EUR_2015/GBP_2018/kW")

        # Both should now be defined
        assert "EUR_2015" in ureg._units
        assert "GBP_2018" in ureg._units

    def test_mix_of_existing_and_new_currencies(self) -> None:
        """Test handling mix of existing and new currency units."""
        ureg = UnitRegistry()

        # USD_2020 already exists, CAD_2019 doesn't
        assert "USD_2020" in ureg._units
        assert "CAD_2019" not in ureg._units

        ureg.ensure_currency_is_unit("USD_2020/CAD_2019")

        # Both should be defined
        assert "USD_2020" in ureg._units
        assert "CAD_2019" in ureg._units

    def test_currency_defined_with_nan_conversion(self) -> None:
        """Test that new currencies are defined with nan conversion factor."""
        ureg = UnitRegistry()

        ureg.ensure_currency_is_unit("JPY_2021/kW")

        # Verify JPY_2021 is defined with nan relative to reference currency
        jpy_unit = ureg._units["JPY_2021"]
        assert "nan" in str(jpy_unit) or "NaN" in str(jpy_unit).lower()

    def test_complex_unit_string_with_currency(self) -> None:
        """Test handling of complex unit strings containing currencies."""
        ureg = UnitRegistry()

        assert "CHF_2022" not in ureg._units

        ureg.ensure_currency_is_unit("CHF_2022/kW/year")

        assert "CHF_2022" in ureg._units

    def test_same_currency_different_years(self) -> None:
        """Test that same currency with different years creates separate units."""
        ureg = UnitRegistry()

        ureg.ensure_currency_is_unit("EUR_2015/EUR_2020")

        # Both year variants should be defined
        assert "EUR_2015" in ureg._units
        assert "EUR_2020" in ureg._units

    def test_invalid_currency_code_raises_error(self) -> None:
        """Test that invalid currency codes raise ValueError."""
        ureg = UnitRegistry()

        with pytest.raises(ValueError, match="invalid 3-letter currency codes"):
            ureg.ensure_currency_is_unit("XYZ_2020/kW")
