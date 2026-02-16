# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Test the DataAccessor class."""

import pathlib

import pytest

from technologydata.parsers.data_accessor import DataAccessor, DataSourceName


class TestDataAccessor:
    """Test suite for the DataAccessor class in the technologydata module."""

    @pytest.mark.parametrize(
        ("versions", "expected"),
        [
            (["v1", "v2", "v3", "v4"], "v4"),
            (["v0.1.0", "v0.1.1"], "v0.1.1"),
            (["v1", "v10", "v2"], "v10"),
            (["v1.0.0", "v0.2.1", "v0.1.0"], "v1.0.0"),
        ],
    )  # type: ignore
    def test_get_latest_version_string(
        self, tmp_path: pathlib.Path, versions: list[pathlib.Path], expected: str
    ) -> None:
        """Test get_latest_version_string."""
        versions_dir = [pathlib.Path(tmp_path, version) for version in versions]
        for version in versions_dir:
            version.mkdir()

        assert DataAccessor.get_latest_version_string(versions_dir) == expected

    def test_get_latest_version_string_raises_error(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test if get_latest_version_string raises FileNotFoundError for no valid versions."""
        (tmp_path / "invalid1").mkdir()
        (tmp_path / "another_invalid").mkdir()

        path_list = [p for p in tmp_path.iterdir() if p.is_dir()]

        with pytest.raises(
            FileNotFoundError, match="No valid version directories found."
        ):
            DataAccessor.get_latest_version_string(path_list)

    @pytest.mark.parametrize(
        ("version", "expected_length"),
        [("v10", 136), (None, 136), ("v1", 136)],
    )  # type: ignore
    def test_access_data_dea_energy_storage(
        self, version: str | None, expected_length: int
    ) -> None:
        """Test access_data."""
        data_accessor = DataAccessor(
            data_source_name="dea_energy_storage", data_version=version
        )
        data_package = data_accessor.access_data()

        assert data_accessor.data_source_name == DataSourceName.DEA_ENERGY_STORAGE
        assert data_accessor.data_version == version
        assert data_package is not None
        assert data_package.technologies is not None
        assert data_package.sources is not None
        assert len(data_package.technologies) == expected_length

    def test_access_data_dea_energy_storage_validation(self) -> None:
        """Test access_data."""
        with pytest.raises(ValueError):
            DataAccessor(data_source_name="dea_energy", data_version="v10")

    def test_parse_and_access_data_dea_energy_storage(self) -> None:
        """Test access_data."""
        data_accessor = DataAccessor(
            data_source_name="dea_energy_storage", data_version="v10"
        )
        file_name = "Technology_datasheet_for_energy_storage.xlsx"
        data_accessor.run_parser(file_name, num_digits=3, filter_params=True)
        data_package = data_accessor.access_data()

        assert data_accessor.data_source_name == DataSourceName.DEA_ENERGY_STORAGE
        assert data_accessor.data_version == "v10"
        assert data_package is not None
        assert data_package.technologies is not None
        assert data_package.sources is not None
        assert len(data_package.technologies) == 136

    def test_parse_and_access_data_manual_input_usa(self) -> None:
        """Test access_data."""
        data_accessor = DataAccessor(
            data_source_name="manual_input_usa", data_version="v0.13.4"
        )
        file_name = "manual_input_usa.csv"
        data_accessor.run_parser(file_name, num_digits=3)
        data_package = data_accessor.access_data()

        assert data_accessor.data_source_name == DataSourceName.MANUAL_INPUT_USA
        assert data_accessor.data_version == "v0.13.4"
        assert data_package is not None
        assert data_package.technologies is not None
        assert data_package.sources is not None
        assert len(data_package.technologies) == 85
