# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""SourceCollection class."""

import pathlib
from collections.abc import Iterator

from pydantic import BaseModel, Field

from technologydata.source import Source


class SourceCollection(BaseModel):  # type: ignore
    """
    Represents a collection of sources.

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
