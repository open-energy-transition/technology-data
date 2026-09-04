# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""
Global equation registry and built-in equation definitions.

The module-level ``equation_registry`` instance is the single shared registry
that the ``technologydata`` package uses by default.  Importing this module
loads all built-in equations from
``equations_data/default_equations.yaml``; this happens automatically when the
``technologydata`` package is imported via ``__init__.py``.

Equation limitations
-------------------
Some equations are transcendental in specific variables and cannot be solved
analytically by SymPy. For such variables the user must provide the value
directly rather than deriving it via the registry.

Unit notes
----------
Units are propagated automatically from the input ``Parameter`` objects using
pint arithmetic.  Parameters that appear only in exponent positions (e.g.
``lifetime`` in the annuity equation) are evaluated as plain magnitudes, so
their physical unit label (``year``) does not flow into the result.  This
means equations whose output is implicitly "per year" (annuity factor, EAC,
fixed O&M from fraction) will produce units without the ``/year`` suffix when
all inputs treat time as a dimensionless count.  Where the ``/year`` dimension
matters, use ``eac_simple`` (which divides by ``lifetime`` directly) or supply
an EAC value that already carries the ``/year`` unit as an input to a reverse
solve.
"""

import pathlib

from technologydata.equations import EquationRegistry

equation_registry = EquationRegistry()
equation_registry.load_from_yaml(
    pathlib.Path(__file__).with_name("equations_data") / "default_equations.yaml"
)
