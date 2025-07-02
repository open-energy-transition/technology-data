# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
Parameter class for encapsulating a value, its unit, provenance, notes, and sources.

Examples
--------
>>> from technologydata.unit_value import UnitValue
>>> from technologydata.source import Source
>>> uv = UnitValue(value=1000, unit="EUR_2020/kW")
>>> src = Source(name="Example Source", url="http://example.com")
>>> param = Parameter(quantity=uv, provenance="literature", note="Estimated", sources=[src])

"""

from pydantic import BaseModel, Field

from technologydata.source import Source
from technologydata.unit_value import UnitValue


class Parameter(BaseModel):
    """
    Encapsulates a value with its unit, provenance, notes, and sources.

    Parameters
    ----------
    quantity : UnitValue
        The value and its unit.
    provenance : Optional[str]
        Description of the data's provenance.
    note : Optional[str]
        Additional notes about the parameter.
    sources : Union[Source, List[Source]]
        One or more sources for the parameter.

    Attributes
    ----------
    quantity : UnitValue
        The value and its unit.
    provenance : Optional[str]
        Description of the data's provenance.
    note : Optional[str]
        Additional notes about the parameter.
    sources : List[Source]
        List of sources for the parameter.

    """

    quantity: UnitValue = Field(..., description="The value and its unit.")
    provenance: str | None = Field(None, description="Data provenance.")
    note: str | None = Field(None, description="Additional notes.")
    sources: list[Source] = Field(..., description="List of sources.")

    def __init__(self, **data):
        # Accept a single Source or list of Sources
        sources = data.get("sources")
        if sources is not None and not isinstance(sources, list):
            data["sources"] = [sources]
        super().__init__(**data)

    @property
    def value(self) -> float:
        """
        The numerical value of the parameter.

        Returns
        -------
        float
            The value.

        """
        return self.quantity.value

    @property
    def unit(self) -> str:
        """
        The unit of the parameter.

        Returns
        -------
        str
            The unit.

        """
        return self.quantity.unit
