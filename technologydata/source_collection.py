# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
SourceCollection class.

"""

from pydantic import BaseModel, Field
from technologydata.source import Source


class SourceCollection(BaseModel):
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

    def __iter__(self):
        return iter(self.sources)

    def __len__(self):
        return len(self.sources)
