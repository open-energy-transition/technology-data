# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""SourceCollection class."""

from collections.abc import Iterator

from pydantic import BaseModel, Field

from technologydata.source import Source


class SourceCollection(BaseModel):  # type: ignore
    """
    Represents a collection of sources.

    Parameters
    ----------
    sources : list[Source]
        List of Source objects.

    Attributes
    ----------
    sources : list[Source]
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
