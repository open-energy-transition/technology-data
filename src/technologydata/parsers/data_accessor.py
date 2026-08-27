# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Provide a class to access data from a data source."""

import enum
import logging
import pathlib
import re
import sys
from typing import Annotated

import pydantic
import requests
from packaging.version import parse
from pydantic import Field, field_validator

from technologydata import DataPackage
from technologydata.parsers.dea_energy_storage import DeaEnergyStorageParser
from technologydata.parsers.manual_input_usa import ManualInputUsaParser

path_cwd = pathlib.Path.cwd()

logger = logging.getLogger(__name__)


class DataSourceName(enum.StrEnum):
    """An enumeration of available data sources."""

    DEA_ENERGY_STORAGE = "dea_energy_storage"
    MANUAL_INPUT_USA = "manual_input_usa"


class DataAccessor(pydantic.BaseModel):
    """
    Access data from a versioned data source.

    This class provides a standardized interface to locate and load technology
    datasets from predefined data sources. It can either load a specific version
    from the local storage, automatically determining and loading the latest available
    version, or download data from a remote URL.

    Attributes
    ----------
    data_source : str
        The name of the data source to access, as defined in the
        `DataSourceName` enumeration.
    version : str, optional
        The specific version string of the data to load (e.g., "v1.0.0").
        If not provided, the latest version will be automatically determined
        and used. Default is None.
    data_path : pathlib.Path, optional
        The path to the data source directory. If not provided, the default
        path will be used.

    """

    data_source: Annotated[str, Field(description="The name of the data source.")]
    version: Annotated[
        str | None, Field(description="The version of the data source.")
    ] = None
    data_path: Annotated[
        pathlib.Path,
        Field(
            description="The base directory path where data sources are located.",
        ),
    ] = pathlib.Path(path_cwd, "src", "technologydata", "parsers")

    @staticmethod
    def ensure_path_exists(input_data_path: pathlib.Path) -> None:
        """
        Ensure the provided data directory exists, creating it if necessary.

        Creates the data directory and any parent directories as needed. If the
        directory already exists, no action is taken.

        Parameters
        ----------
        input_data_path : pathlib.Path
             The base directory path where data sources are located.

        Returns
        -------
        None

        Notes
        -----
        This method uses `mkdir(parents=True, exist_ok=True)` to safely create
        the directory structure without raising an error if the directory
        already exists.

        """
        if not input_data_path.is_dir():
            input_data_path.mkdir(parents=True, exist_ok=True)

    @field_validator("data_source", mode="before")
    @classmethod
    def _validate_data_source_name(cls, v: str) -> DataSourceName:
        # Validate if the given string is a valid DataSourceName
        try:
            return DataSourceName(v)
        except ValueError:
            raise ValueError(
                f"{v} is not a valid DataSourceName. Available options: {[e for e in DataSourceName]}"
            )

    @staticmethod
    def get_latest_version_string(data_source_path_list: list[pathlib.Path]) -> str:
        """
        Find the latest version string for the data source.

        Returns
        -------
        str
            The string of the latest version (e.g., 'v10', 'v1.0.0').

        Raises
        ------
        FileNotFoundError
            If the data source directory or valid version directories are not found.

        """
        version_pattern = re.compile(r"^v(\d+(\.\d+)*)$")
        versions = []
        for item in data_source_path_list:
            if item.is_dir():
                match = version_pattern.match(item.name)
                if match:
                    versions.append(item.name)

        if not versions:
            raise FileNotFoundError("No valid version directories found.")

        latest_version_str = max(versions, key=lambda v: parse(v[1:]))
        return latest_version_str

    def load(self) -> DataPackage:
        """
        Load the default 'technologies.json' from the package data.

        Returns
        -------
        DataPackage
            An instance of DataPackage initialized with the requested data.

        Raises
        ------
        FileNotFoundError
            If the data source directory or the specified version directory is not found.
        ValueError
            If the specified version is not found. The user is notified of  the latest available version.

        """
        # Ensure the data path exists before attempting to load data
        DataAccessor.ensure_path_exists(self.data_path)

        source_path = pathlib.Path(self.data_path, self.data_source)

        source_path_list = [p.name for p in source_path.iterdir() if p.is_dir()]

        if self.version and self.version in source_path_list:
            version = self.version
            logger.info(
                f"Data source directory corresponding to version {self.version} found."
            )
        else:
            version = self.get_latest_version_string(list(source_path.iterdir()))
            raise ValueError(
                f"Data source version '{self.version}' not found. The latest available version is {version}."
            )

        data_path = pathlib.Path(source_path, version)
        dp = DataPackage.from_json(self.data_source, self.version, data_path)
        return dp

    def download(self, base_url: str) -> DataPackage:
        """
        Download and load technology data from a remote URL.

        This method downloads technologies.json and sources.json files from the
        specified base URL and loads them into a DataPackage instance. The sources.json
        file is optional; if not found, sources will be extracted from technologies.

        Parameters
        ----------
        base_url : str
            Base URL where the JSON files are hosted. The method will attempt to download
            technologies.json and sources.json from this location. The URL should point
            to the directory containing these files.
        version : str
            The version of the data to download. This will be used to create a subdirectory

        Returns
        -------
        DataPackage
            An instance of DataPackage initialized with the downloaded data.

        Raises
        ------
        requests.HTTPError
            If the HTTP request to download technologies.json fails.
        requests.ConnectionError
            If there is a network connectivity issue.

        Examples
        --------
        >>> accessor = DataAccessor(data_source="dea_energy_storage", version="v1.0")
        >>> dp = accessor.download("https://example.com/data")

        """
        # Ensure base_url ends with /
        if not base_url.endswith("/"):
            base_url += "/"

        # Download technologies.json
        technologies_url = f"{base_url}technologies.json"
        sources_url = f"{base_url}sources.json"
        if self.version:
            technologies_path = pathlib.Path(
                self.data_path, self.data_source, self.version, "technologies.json"
            )
            sources_path = pathlib.Path(
                self.data_path, self.data_source, self.version, "sources.json"
            )
        else:
            raise ValueError("Version must be specified for downloading data.")

        # Ensure parent directories exist
        self.ensure_path_exists(technologies_path.parent)
        self.ensure_path_exists(sources_path.parent)

        try:
            logger.info(f"Downloading technologies.json from {technologies_url}")
            response = requests.get(technologies_url, timeout=30)
            response.raise_for_status()

            with open(technologies_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        except requests.HTTPError as e:
            logger.error(f"Failed to download technologies.json: {e}")
            raise

        try:
            logger.info(f"Downloading sources.json from {sources_url}")
            response = requests.get(sources_url, timeout=30)
            response.raise_for_status()

            with open(sources_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        except requests.HTTPError as e:
            logger.error(f"Failed to download sources.json: {e}")
            raise

        # Load using DataPackage.from_json
        # Construct path to folder containing the downloaded files
        if self.version:
            path_to_folder = pathlib.Path(
                self.data_path, self.data_source, self.version
            )
        else:
            path_to_folder = pathlib.Path(self.data_path, self.data_source)

        data_package = DataPackage.from_json(
            name=self.data_source, version=self.version, path_to_folder=path_to_folder
        )

        return data_package

    def parse(
        self,
        input_file_name: str,
        num_digits: int = 4,
        archive_source: bool = False,
        filter_params: bool = False,
        export_schema: bool = False,
    ) -> None:
        """
        Run the parser for the specified data source and version.

        This method locates the appropriate parser for the given data source
        and version, and executes it to generate the technology data package.

        Parameters
        ----------
        input_file_name : str
            The name of the input file in the 'raw' directory.
        num_digits : int, optional
            Number of significant digits to round the values. Default is 4.
        archive_source : bool, optional
            Store the source object on the Wayback Machine. Default is False.
        filter_params : bool, optional
            Filter the parameters stored to technologies.json. Default is False.
        export_schema : bool, optional
            Export the Source/TechnologyCollection schemas. Default is False.

        Raises
        ------
        ValueError
            If the specified data source or version is not supported.
        FileNotFoundError
            If the required input data file is not found.

        """
        parser: DeaEnergyStorageParser | ManualInputUsaParser

        if self.data_source == DataSourceName.DEA_ENERGY_STORAGE:
            parser = DeaEnergyStorageParser()
        elif self.data_source == DataSourceName.MANUAL_INPUT_USA:
            parser = ManualInputUsaParser()
        else:
            raise ValueError(
                f"Unsupported data source: {self.data_source}. "
                f"Supported data sources are: {[e for e in DataSourceName]}"
            )

        # Read the raw data
        input_path = pathlib.Path(
            self.data_path,
            "raw",
        )
        DataAccessor.ensure_path_exists(input_path)
        input_data_path = pathlib.Path(input_path, input_file_name)
        logger.info(f"Input data path set to: {input_data_path}")

        if self.version not in parser.get_supported_versions():
            logging.error(
                f"Version '{self.version}' is not supported. "
                f"Supported versions: {parser.get_supported_versions()}"
            )
            sys.exit(1)

        try:
            parser.parse(
                version=self.version,
                input_path=input_data_path,
                num_digits=num_digits,
                archive_source=archive_source,
                filter_params=filter_params,
                export_schema=export_schema,
            )

            logging.info(f"Successfully generated files for version {self.version} ")

        except (ValueError, FileNotFoundError, KeyError) as e:
            logging.error(f"An error occurred during parsing: {e}")
            sys.exit(1)
