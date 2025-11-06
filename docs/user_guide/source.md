# `Source` Class Documentation

<!--
SPDX-FileCopyrightText: The technology-data authors

SPDX-License-Identifier: MIT
-->

## Overview

The `Source` class in `technologydata` represents bibliographic and web sources, supporting metadata, archiving, and retrieval from the Wayback Machine. It is designed to track provenance, ensure reproducibility, and facilitate the management of references for technology parameters and datasets.

## Features

- **Bibliographic Metadata**: Stores title, authors, and optional URL, access date, archive URL, and archive date.
- **Equality and Hashing**: Implements equality and hashing for use in sets and as dictionary keys.
- **String Representation**: Provides a readable string summary of the source.
- **Wayback Machine Archiving**: Ensures URLs are archived and retrieves archive URLs and timestamps from the Wayback Machine.
- **File Retrieval**: Downloads archived files from the Wayback Machine to a specified directory.
- **Automatic File Naming**: Determines file extension and save path based on content type or URL.

## Usage Examples

### Creating a Source

```python
from technologydata.source import Source
src = Source(title="Example Source", authors="The Authors", url="http://example.com")
```

### Archiving a URL

```python
from technologydata.source import Source
src = Source(title="Example Source", authors="The Authors", url="http://example.com")

src.ensure_in_wayback()
print(src.url_archive)  # Archived URL
print(src.url_date_archive)  # Archive timestamp
```

### Downloading an Archived File

```python
import pathlib
from technologydata.source import Source
src = Source(title="Example Source", authors="The Authors", url="http://example.com")

output_path = src.retrieve_from_wayback(pathlib.Path("downloads/"))
print(output_path)  # Path to downloaded file
```

## API Reference

### Attributes

- `title`: Title of the source (str).
- `authors`: Authors of the source (str).
- `url`: Optional URL of the source (str or None).
- `url_archive`: Optional archived URL (str or None).
- `url_date`: Optional date the URL was accessed (str or None).
- `url_date_archive`: Optional date the URL was archived (str or None).

### Methods

- `__eq__(other)`: Checks equality with another Source.
- `__hash__()`: Returns a hash value for the Source.
- `__str__()`: Returns a string representation of the Source.
- `ensure_in_wayback()`: Archives the URL in the Wayback Machine and updates attributes.
- `retrieve_from_wayback(download_directory)`: Downloads the archived file to the specified directory.
- `_store_in_wayback(url_to_archive)`: Static (private) method to archive a URL and extract timestamp.
- `_get_save_path(url_archived, source_path, source_title)`: Static (private) method to determine save path and extension.
- `_get_content_type(url_archived)`: Static method to fetch content type from archived URL.
- `_download_file(url_archived, save_path)`: Static (private) method to download file from archived URL.

## Limitations & Notes

- **Archiving**: If the URL is not set, archiving will raise a `ValueError`.
- **File Extensions**: File extension is inferred from content type or URL; unsupported types raise a `ValueError`.
- **HTTP Errors**: Download and content type retrieval may raise `requests.exceptions.RequestException`.
- **Duplicates**: Equality and hashing are based on all attributes; sources with identical metadata are considered equal.
