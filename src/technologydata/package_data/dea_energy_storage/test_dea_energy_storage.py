# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""Test the functions of the DEA energy storage parser."""

import pytest

from technologydata.package_data.dea_energy_storage.dea_energy_storage import clean_parameter_string


class TestDEAEnergyStorage:
    """Test suite for the functions of the DEA energy storage parser."""

    @pytest.mark.parametrize(
        "input_string, expected_string",
        [
            ("- Discharge efficiency [%]", "Discharge efficiency"),
            ("Construction time [years]", "Construction time"),
            ("- Another example [with brackets]", "Another example"),
            ("No brackets or hyphen here", "No brackets or hyphen here"),
        ],
    )  # type: ignore
    def test_clean_parameter_string(
        self, input_string: str, expected_string: str
    ) -> None:
        """Check if the clean_parameter_string works as expected."""
        print(clean_parameter_string(input_string))
        assert clean_parameter_string(input_string) == expected_string
