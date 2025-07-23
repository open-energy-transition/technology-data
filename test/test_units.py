import json

import pint
import pytest

from technologydata.utils.units import (
    CURRENCY_CODES_CACHE,
    extract_currency_units,
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
