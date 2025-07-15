# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""SourceCollection class."""

import csv
import json
import pathlib
from collections.abc import Iterator

from pydantic import BaseModel, Field

from technologydata.source import Source


class SourceCollection(BaseModel):  # type: ignore
    """
    Represent a collection of sources.

    Parameters
    ----------
    sources : List[Source]
        List of Source objects.

    Attributes
    ----------
    sources : List[Source]
        List of Source objects.

    """

    sources: list[Source] = Field(..., description="List of Source objects.")

    def __iter__(self) -> Iterator[Source]:
        """
        Iterate over the sources in this collection.

        Returns
        -------
        Iterator[Source]
            An iterator that yields Source objects from the sources list.

        """
        return iter(self.sources)

    def __len__(self) -> int:
        """
        Return the number of sources in this collection.

        Returns
        -------
        int
            The number of Source objects in the sources list.

        """
        return len(self.sources)

    def retrieve_all_archives(
        self, download_directory: pathlib.Path
    ) -> list[pathlib.Path | None]:
        """
        Download archived files for all sources in the collection using retrieve_from_wayback.

        Parameters
        ----------
        download_directory : pathlib.Path
            The base directory where all files will be saved.

        Returns
        -------
        list[pathlib.Path | None]
            List of paths where each file was stored, or None if download failed for a source.

        """
        return [
            source.retrieve_from_wayback(download_directory) for source in self.sources
        ]

    def export_to_csv(self, file_path: pathlib.Path) -> None:
        """
        Export the SourceCollection to a CSV file.

        Parameters
        ----------
        file_path : pathlib.Path
            The path to the CSV file to be created.

        """
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "title",
                "authors",
                "url",
                "url_archive",
                "url_date",
                "url_date_archive",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write each source as a row in the CSV
            for source in self.sources:
                writer.writerow(source.model_dump())

    def export_to_json(self, file_path: pathlib.Path) -> None:
        """
        Export the SourceCollection to a JSON file, together with a data schema.

        Parameters
        ----------
        file_path : pathlib.Path
            The path to the JSON file to be created.

        """
        schema_path = pathlib.Path(file_path.parent, "source_collection_schema.json")

        # Export the model's schema with descriptions to a dict
        schema = self.model_json_schema()

        # Save the schema (which includes descriptions) to a JSON file
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=4)

        with open(file_path, mode="w", encoding="utf-8") as jsonfile:
            json_data = self.model_dump_json(indent=4)  # Convert to JSON string
            jsonfile.write(json_data)
