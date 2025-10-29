# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the utility methods."""

import typing

import pandas
import pytest

import technologydata


class TestCommonsUtils:
    """Test suite for the Commons utility functions in the technologydata module."""

    @pytest.mark.parametrize(
        "input_datetime_string, date_format, expected_date",
        [
            (
                "2025-05-20 14:45:00",
                technologydata.DateFormatEnum.SOURCES_CSV,
                "2025-05-20 14:45:00",
            ),
            (
                "20250520144500",
                technologydata.DateFormatEnum.SOURCES_CSV,
                "2025-05-20 14:45:00",
            ),
            (
                "2025-05-20 14:45:00",
                technologydata.DateFormatEnum.WAYBACK,
                "20250520144500",
            ),
            ("20250520144500", technologydata.DateFormatEnum.WAYBACK, "20250520144500"),
            ("2025-05-20 14:45:00", technologydata.DateFormatEnum.NONE, ""),
            (
                "invalid-date-string",
                technologydata.DateFormatEnum.SOURCES_CSV,
                ValueError,
            ),
            ("2025/13/01", technologydata.DateFormatEnum.SOURCES_CSV, ValueError),
        ],
    )  # type: ignore
    def test_change_datetime_format(
        self,
        input_datetime_string: str,
        date_format: technologydata.DateFormatEnum,
        expected_date: str | typing.Any,
    ) -> None:
        """Check if the datetime is correctly transformed to a new format."""
        if expected_date is ValueError:
            with pytest.raises(ValueError, match="Error during datetime formatting"):
                technologydata.Commons.change_datetime_format(
                    input_datetime_string, date_format
                )
        else:
            result = technologydata.Commons.change_datetime_format(
                input_datetime_string, date_format
            )
            assert result == expected_date

    @pytest.mark.parametrize(
        "input_string, expected_string",
        [
            (
                "Hello, World! Welcome to Python @ 2023.",
                "hello_world_welcome_to_python_2023",
            ),
            (
                "  Special#Characters$Are%Fun!  ",
                "special_characters_are_fun",
            ),
            (
                "!!!LeadingAndTrailing!!!",
                "leadingandtrailing",
            ),
        ],
    )  # type: ignore
    def test_replace_special_characters(
        self,
        input_string: str,
        expected_string: str,
    ) -> None:
        """Check if the special characters are removed from a string and the string is lowercased."""
        assert (
            technologydata.Commons.replace_special_characters(input_string)
            == expected_string
        )

    @pytest.mark.parametrize(
        "input_string, expected_string",
        [
            ("text/plain", ".txt"),
            ("text/html", ".html"),
            ("text/csv", ".csv"),
            ("text/xml", ".xml"),
            ("application/vnd.ms-excel", ".xls"),
            ("application/vnd.oasis.opendocument.spreadsheet", ".ods"),
            (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
            ),
            ("application/json", ".json"),
            ("application/xml", ".xml"),
            ("application/pdf", ".pdf"),
            ("application/parquet", ".parquet"),
            ("application/vdn.apache.parquet", ".parquet"),
            ("application/x-rar-compressed", ".rar"),
            ("application/vnd.rar", ".rar"),
            ("application/zip", ".zip"),
            ("application/x-zip-compressed", ".zip"),
        ],
    )  # type: ignore
    def test_get_extension(
        self,
        input_string: str,
        expected_string: str,
    ) -> None:
        """Check if the correct file extension is associated to a given MIME type."""
        assert (
            technologydata.FileExtensionEnum.get_extension(input_string)
            == expected_string
        )

    @pytest.mark.parametrize(
        "input_string, expected_string",
        [
            ("https://example.com/file.txt", ".txt"),
            ("https://example.com/file.html", ".html"),
            ("https://example.com/file.csv", ".csv"),
            ("https://example.com/file.xml", ".xml"),
            ("https://example.com/file.xls", ".xls"),
            ("https://example.com/file.ods", ".ods"),
            ("https://example.com/file.xlsx", ".xlsx"),
            ("https://example.com/file.json", ".json"),
            ("https://example.com/file.pdf", ".pdf"),
            ("https://example.com/file.parquet", ".parquet"),
            ("https://example.com/file.rar", ".rar"),
            ("https://example.com/file.zip", ".zip"),
            ("https://example.com/file.unknown", None),
        ],
    )  # type: ignore
    def test_search_file_extension_in_url(
        self,
        input_string: str,
        expected_string: str,
    ) -> None:
        """Check if the correct file extension is found in a given url."""
        assert (
            technologydata.FileExtensionEnum.search_file_extension_in_url(input_string)
            == expected_string
        )

    def test_safe_divide_scalars(self) -> None:
        """Check if the safe_divide works as expected."""
        assert technologydata.Commons.safe_divide(10, 2) == 5.0

    def test_safe_divide_lists(self) -> None:
        """Check if the safe_divide works as expected."""
        result = technologydata.Commons.safe_divide([10, 20], [2, 4])
        print(result)
        assert result.equals(pandas.Series([5.0, 5.0]))

    def test_safe_divide_series(self) -> None:
        """Check if the safe_divide works as expected."""
        a = pandas.Series([10, 20])
        b = pandas.Series([2, 4])
        result = technologydata.Commons.safe_divide(a, b)
        assert result.equals(pandas.Series([5.0, 5.0]))

    def test_safe_divide_zero_division(self) -> None:
        """Check if the safe_divide works as expected."""
        with pytest.raises(ZeroDivisionError):
            technologydata.Commons.safe_divide(1, 0)

    def test_safe_multiply_scalars(self) -> None:
        """Check if the safe_multiply works as expected."""
        assert technologydata.Commons.safe_multiply(3, 4) == 12.0

    def test_safe_multiply_lists(self) -> None:
        """Check if the safe_multiply works as expected."""
        result = technologydata.Commons.safe_multiply([2, 3], [4, 5])
        assert result.equals(pandas.Series([8, 15]))

    def test_safe_multiply_series(self) -> None:
        """Check if the safe_multiply works as expected."""
        a = pandas.Series([2, 3])
        b = pandas.Series([4, 5])
        result = technologydata.Commons.safe_multiply(a, b)
        assert result.equals(pandas.Series([8, 15]))

    def test_safe_len_sized(self) -> None:
        """Check if the safe_len works as expected."""
        assert technologydata.Commons.safe_len([1, 2, 3]) == 3

    def test_safe_len_unsized(self) -> None:
        """Check if the safe_len works as expected."""
        assert technologydata.Commons.safe_len(42) == 1

    def test_safe_loc_series(self) -> None:
        """Check if the safe_loc works as expected."""
        s = pandas.Series({"a": 1, "b": 2})
        assert technologydata.Commons.safe_loc(s, "a") == 1

    def test_safe_loc_scalar(self) -> None:
        """Check if the safe_loc works as expected."""
        assert technologydata.Commons.safe_loc(5, "a") == 5

    def test_safe_iloc_series(self) -> None:
        """Check if the safe_iloc works as expected."""
        s = pandas.Series([10, 20, 30])
        assert technologydata.Commons.safe_iloc(s, 1) == 20

    def test_safe_iloc_scalar(self) -> None:
        """Check if the safe_iloc works as expected."""
        assert technologydata.Commons.safe_iloc(7, 0) == 7
