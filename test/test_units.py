import pytest
import pint
from unittest.mock import patch
from technologydata.utils.units import extract_currency_units


class TestExtractCurrencyUnits:
    """Test cases for extract_currency_units function."""

    def test_single_currency_unit(self):
        """Test extraction of a single currency unit."""
        result = extract_currency_units("USD_2020/kW")
        assert result == ["USD_2020"]

    def test_multiple_currency_units(self):
        """Test extraction of multiple currency units."""
        result = extract_currency_units("EUR_2015/USD_2020")
        assert set(result) == {"EUR_2015", "USD_2020"}

    def test_no_currency_units(self):
        """Test that no currency units are extracted from non-currency strings."""
        result = extract_currency_units("kW/hour")
        assert result == []

    def test_empty_string(self):
        """Test extraction from empty string."""
        result = extract_currency_units("")
        assert result == []

    def test_pint_unit_input(self):
        """Test that pint.Unit objects are properly converted to strings."""
        ureg = pint.UnitRegistry()
        unit = ureg.parse_expression("kW")
        result = extract_currency_units(unit)
        assert result == []

    def test_complex_unit_string(self):
        """Test extraction from complex unit strings with multiple components."""
        result = extract_currency_units("USD_2020/kW/year")
        assert result == ["USD_2020"]

    def test_invalid_year_format(self):
        """Test that invalid year formats are not matched."""
        result = extract_currency_units("USD_20/kW")
        assert result == []

        result = extract_currency_units("USD_20200/kW")
        assert result == []

    def test_non_three_letter_codes(self):
        """Test that non-three-letter codes are not matched."""
        result = extract_currency_units("US_2020/kW")
        assert result == []

        result = extract_currency_units("USDD_2020/kW")
        assert result == []

    def test_case_sensitivity(self):
        """Test that currency codes must be uppercase."""
        result = extract_currency_units("usd_2020/kW")
        assert result == []

    def test_valid_currency_codes(self):
        """Test that only valid currency codes are accepted."""
        result = extract_currency_units("USD_2020/kW")
        assert result == ["USD_2020"]

        result = extract_currency_units("EUR_2015/kW")
        assert result == ["EUR_2015"]

        with pytest.raises(ValueError):
            extract_currency_units("EUA_2015/kW")

    def test_invalid_currency_codes_raise(self):
        """Test that invalid currency codes raise ValueError."""
        with pytest.raises(ValueError):
            extract_currency_units("XYZ_2020/kW")

    def test_duplicate_currency_units(self):
        """Test that duplicate currency units are handled correctly."""
        result = extract_currency_units("USD_2020/USD_2020/EUR_2015")
        assert result == ["USD_2020", "USD_2020", "EUR_2015"]

    def test_different_years_same_currency(self):
        """Test extraction of same currency with different years."""
        result = extract_currency_units("USD_2020/USD_2015")
        assert result == ["USD_2020", "USD_2015"]

    def test_mixed_valid_invalid_currencies(self):
        """Test behavior with mix of valid and invalid currency codes."""
        with pytest.raises(ValueError):
            extract_currency_units("USD_2020/XYZ_2021")
