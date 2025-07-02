# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
Source class for representing bibliographic and web sources, with archiving support.

Examples
--------
>>> src = Source(name="Example Source", url="http://example.com")
>>> src.store_in_wayback()
>>> src.retrieve_from_wayback()

"""

from pydantic import BaseModel, Field
from savepagenow import capture_or_cache


class Source(BaseModel):
    """
    Represents a data source, including bibliographic and web information.

    Parameters
    ----------
    name : str
        Name of the source.
    authors : Optional[str]
        Authors of the source.
    url : Optional[str]
        URL of the source.
    url_archive : Optional[str]
        Archived URL (e.g., from the Wayback Machine).
    urldate : Optional[str]
        Date the URL was accessed.
    urldate_archive : Optional[str]
        Date the URL was archived.

    Attributes
    ----------
    name : str
        Name of the source.
    authors : Optional[str]
        Authors of the source.
    url : Optional[str]
        URL of the source.
    url_archive : Optional[str]
        Archived URL.
    urldate : Optional[str]
        Date the URL was accessed.
    urldate_archive : Optional[str]
        Date the URL was archived.

    """

    name: str = Field(..., description="Name of the source.")
    authors: str | None = Field(None, description="Authors of the source.")
    url: str | None = Field(None, description="URL of the source.")
    url_archive: str | None = Field(None, description="Archived URL.")
    urldate: str | None = Field(None, description="Date the URL was accessed.")
    urldate_archive: str | None = Field(None, description="Date the URL was archived.")

    def store_in_wayback(self) -> None:
        """
        Archive the source URL in the Internet Archive's Wayback Machine.

        Returns
        -------
        None

        """
        if self.url:
            archive_url = capture_or_cache(self.url)
            self.url_archive = archive_url
        # Optionally, set urldate_archive here

    def retrieve_from_wayback(self) -> str | None:
        """
        Retrieve the archived URL from the Wayback Machine.

        Returns
        -------
        Optional[str]
            The archived URL if available, else None.

        """
        return self.url_archive
