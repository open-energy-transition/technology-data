# Introduction

## Currencies Class Documentation

### Overview

The `Currencies` class provides utility methods for handling currency-related operations, including deflating values based on specified deflator functions, converting currency values in a DataFrame, and ensuring currency units are correctly formatted. 
This class utilizes the `pydeflate` package for deflation calculations and the `hdx` package for relating country and currency ISO3 codes.

### Installation

To use the `Currencies` class, ensure you have the following packages installed:

`pip install pandas pydeflate hdx-python`

### Usage

#### Getting Country from Currency Code

To retrieve a list of country ISO3 codes associated with a given currency code, use the `get_country_from_currency` method.

#### Extracting Currency Unit

To check if a string contains a currency unit and extract it, use the `extract_currency_unit` method.

#### Updating Currency Unit

To replace the currency code and/or year in a string representing a currency unit, use the `update_currency_unit` method.

#### Adjusting Currency Values

To convert and adjust currency values in a DataFrame to a target currency and base year, use the `adjust_currency` method.

### Limitations

The limitations of the class are:
- the `get_country_from_currency` method assumes that the currency code provided is valid and exists in the HDX country data. If the currency code is not found, it may return an empty list or raise a `KeyError`. 
- the `extract_currency_unit` method relies on a specific format for currency units (i.e., `<ISO3 CURRENCY_CODE>_<YEAR>`). If the input string does not match this format, it will return `None`. I.e. currency values need to provided with the correctly formatted currency unit, e.g. `USD_2020`, `EUR_2023` or `CNY_2025`. The currency symbols follow [ISO 4217](https://de.wikipedia.org/wiki/ISO_4217)
- the `adjust_currency` method requires the input DataFrame to contain specific columns: `unit`, `value`, and `region`. If any of these columns are missing, a `ValueError` will be raised.

### Assumptions

The assumptions are:
- the class assumes that the currency codes provided are valid ISO3 currency codes.
- the `get_country_from_currency `method assumes that the HDX package's country data is up-to-date and accurately reflects the current currency usage by countries.
- the `adjust_currency` method assumes that the `pydeflate` package is correctly configured and that the necessary deflation functions are registered in the `deflation_function_registry`.

### Conclusion

The Currencies class is a powerful utility for managing currency operations in Python, leveraging the capabilities of the pydeflate and hdx packages. By following the usage examples and being aware of the limitations and assumptions, users can effectively integrate currency handling into their data processing workflows.