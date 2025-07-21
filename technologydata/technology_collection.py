# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""TechnologyCollection class for representing an iterable of Technology Objects."""

import csv
import json
import pathlib
import re

import pandas
import pydantic

from technologydata.technology import Technology


class TechnologyCollection(pydantic.BaseModel):  # type: ignore
    """
    Represent a collection of technologies.

    Parameters
    ----------
    technologies : List[Technology]
        List of Technology objects.

    Attributes
    ----------
    technologies : List[Technology]
        List of Technology objects.

    """

    technologies: list[Technology] = pydantic.Field(..., description="List of Technology objects.")

    def get(self, title: str, authors: str) -> "TechnologyCollection":
        """
        Filter technologies based on regex patterns for non-optional attributes.

        Parameters
        ----------
        title : str
            Regex pattern to filter titles.
        authors : str
            Regex pattern to filter authors.

        Returns
        -------
        TechnologyCollection
            A new TechnologyCollection with filtered technologies.

        """
        filtered_technologies = self.technologies

        if title is not None:
            pattern_title = re.compile(title, re.IGNORECASE)
            filtered_technologies = [
                s for s in filtered_technologies if pattern_title.search(s.title)
            ]

        if authors is not None:
            pattern_authors = re.compile(authors, re.IGNORECASE)
            filtered_technologies = [
                s for s in filtered_technologies if pattern_authors.search(s.authors)
            ]

        return TechnologyCollection(technologies=filtered_technologies)

    def __len__(self) -> int:
        """
        Return the number of technologies in this collection.

        Returns
        -------
        int
            The number of Technology objects in the technologies list.

        """
        return len(self.technologies)

    def to_dataframe(self) -> pandas.DataFrame:
        """
        Convert the TechnologyCollection to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the technology data.

        """
        return pandas.DataFrame([technology.model_dump() for technology in self.technologies])

    def to_csv(self, **kwargs: pathlib.Path | str | bool) -> None:
        """
        Export the TechnologyCollection to a CSV file.

        Parameters
        ----------
        **kwargs : dict
            Additional keyword arguments passed to pandas.DataFrame.to_csv().
            Common options include:
            - path_or_buf : str or pathlib.Path or file-like object, optional
                File path or object, if None, the result is returned as a string.
                Default is None.
            - sep : str
                String of length 1. Field delimiter for the output file.
                Default is ','.
            - index : bool
                Write row names (index). Default is True.
            - encoding : str
                String representing the encoding to use in the output file.
                Default is 'utf-8'.

        Notes
        -----
        The method converts the collection to a pandas DataFrame using
        `self.to_dataframe()` and then writes it to a CSV file using the provided
        kwargs.

        """
        default_kwargs = {
            "sep": ",",
            "index": False,
            "encoding": "utf-8",
            "quoting": csv.QUOTE_ALL,
        }

        # Merge default_kwargs with user-provided kwargs, giving precedence to user kwargs
        merged_kwargs = {**default_kwargs, **kwargs}
        output_dataframe = self.to_dataframe()
        output_dataframe.to_csv(**merged_kwargs)

    def to_json(
        self, file_path: pathlib.Path, schema_path: pathlib.Path | None = None
    ) -> None:
        """
        Export the TechnologyCollection to a JSON file, together with a data schema.

        Parameters
        ----------
        file_path : pathlib.Path
            The path to the JSON file to be created.
        schema_path : pathlib.Path
            The path to the JSON schema file to be created. By default, created with a `schema` suffix next to `file_path`.

        """
        if schema_path is None:
            schema_path = file_path.with_suffix(".schema.json")

        # Export the model's schema with descriptions to a dict
        schema = self.model_json_schema()

        # Save the schema (which includes descriptions) to a JSON file
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=4)

        with open(file_path, mode="w", encoding="utf-8") as jsonfile:
            json_data = self.model_dump_json(indent=4)  # Convert to JSON string
            jsonfile.write(json_data)

    @classmethod
    def from_json(cls, file_path: pathlib.Path | str) -> "TechnologyCollection":
        """
        Import the TechnologyCollection from a JSON file.

        Parameters
        ----------
        file_path : pathlib.Path
            The path to the JSON file to be imported.

        """
        if isinstance(file_path, pathlib.Path | str):
            file_path = pathlib.Path(file_path)
        else:
            raise TypeError("file_path must be a pathlib.Path or str")
        with open(file_path, encoding="utf-8") as jsonfile:
            json_data = json.load(jsonfile)
        return cls(**json_data)
