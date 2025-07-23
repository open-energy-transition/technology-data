"""Test that the cache for retrieving up-to-date currency codes and their relationship to ISO3 codes is working correctly."""

import os
import json
import pytest
from technologydata.utils.units import (
    get_iso3_to_currency_codes,
    CURRENCY_CODES_CACHE,
)
from pathlib import Path


def test_currency_cache_creates_and_reads():
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
