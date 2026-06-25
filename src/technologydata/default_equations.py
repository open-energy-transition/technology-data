# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Global equation registry and built-in equation definitions.

The module-level ``equation_registry`` instance is the single shared registry
that the ``technologydata`` package uses by default.  Importing this module
registers all built-in equations; this happens automatically when the
``technologydata`` package is imported via ``__init__.py``.

Equation limitations
-------------------
Some equations are transcendental in specific variables and cannot be solved
analytically by SymPy.  These cases are noted per equation below.  For such
variables the user must provide the value directly rather than deriving it
via the registry.

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

from technologydata.equations import EquationRegistry

equation_registry = EquationRegistry()

# ---------------------------------------------------------------------------
# Capital cost / investment
# ---------------------------------------------------------------------------

# The annuity factor (capital recovery factor) converts a one-off specific
# investment cost into a levelised annual payment.  It is the foundation of
# most annualised-cost calculations in energy system models.
#
# Note: WACC cannot be solved analytically from this equation because it
# appears both linearly (numerator) and as a base of an exponent (denominator),
# making the equation transcendental.  Solve for annuity_factor or lifetime
# instead.
equation_registry.register(
    name="annuity_factor",
    parameters=["annuity_factor", "wacc", "lifetime"],
    expr_str="annuity_factor - wacc / (1 - (1 + wacc)**(-lifetime))",
    default=True,
)

# EAC expressed as the product of specific investment and the annuity factor.
# This separates the two concerns — computing the annuity factor and scaling
# by the investment — which is useful when the annuity factor is already known
# or needs to be inspected independently.
equation_registry.register(
    name="eac_via_annuity_factor",
    parameters=["eac", "specific_investment", "annuity_factor"],
    expr_str="eac - specific_investment * annuity_factor",
)

# EAC computed directly from the three underlying variables in a single step.
# This is the most commonly cited equation and is set as the default for "eac"
# because it requires only the three fundamental inputs without an intermediate
# annuity_factor parameter.
#
# Note: WACC not analytically solvable (see annuity_factor note above).
equation_registry.register(
    name="eac_annuity",
    parameters=["eac", "specific_investment", "wacc", "lifetime"],
    expr_str="eac - specific_investment * wacc / (1 - (1 + wacc)**(-lifetime))",
    default=True,
)

# Simplified EAC: total investment divided by lifetime.  Ignores time value of
# money (i.e. assumes wacc = 0).  Useful as a quick estimate or when financing
# costs are handled separately.  Because lifetime divides directly here (not as
# an exponent), pint correctly propagates the /year dimension to the result.
equation_registry.register(
    name="eac_simple",
    parameters=["eac", "total_investment_cost", "lifetime"],
    expr_str="eac - total_investment_cost / lifetime",
)

# Converts between specific investment (per unit capacity) and absolute total
# investment cost for a given capacity.  Useful when data sources report one
# form but the model requires the other.
#
# Unit note: ensure power units are consistent (all kW or all MW) before using.
equation_registry.register(
    name="total_investment_from_specific",
    parameters=["total_investment_cost", "specific_investment", "capacity"],
    expr_str="total_investment_cost - specific_investment * capacity",
    default=True,
)

# ---------------------------------------------------------------------------
# Operations and maintenance costs
# ---------------------------------------------------------------------------

# Fixed O&M cost derived from specific investment and a fractional annual rate.
# The fraction is dimensionless (e.g. 0.03 for 3 % per year of CAPEX).
equation_registry.register(
    name="fixed_om_from_fraction",
    parameters=["fixed_om", "specific_investment", "fixed_om_fraction"],
    expr_str="fixed_om - specific_investment * fixed_om_fraction",
    default=True,
)

# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------

# Round-trip efficiency is the product of charging and discharging efficiency.
# All three variables are analytically solvable in every direction.
equation_registry.register(
    name="roundtrip_efficiency",
    parameters=["roundtrip_efficiency", "charge_efficiency", "discharge_efficiency"],
    expr_str="roundtrip_efficiency - charge_efficiency * discharge_efficiency",
    default=True,
)

# ---------------------------------------------------------------------------
# Variable cost
# ---------------------------------------------------------------------------

# Fuel contribution to variable cost: fuel price per unit of input energy
# divided by thermal efficiency gives cost per unit of output energy.
#
# Unit note: fuel_cost and fuel_variable_cost must use the same energy unit.
equation_registry.register(
    name="fuel_variable_cost",
    parameters=["fuel_variable_cost", "fuel_cost", "efficiency"],
    expr_str="fuel_variable_cost - fuel_cost / efficiency",
    default=True,
)

# ---------------------------------------------------------------------------
# CO₂ cost
# ---------------------------------------------------------------------------

# Carbon cost per unit of output energy: carbon price times specific CO₂
# intensity.  co2_intensity must be in t/MWh of *output* energy.
equation_registry.register(
    name="co2_cost",
    parameters=["co2_cost", "co2_price", "co2_intensity"],
    expr_str="co2_cost - co2_price * co2_intensity",
    default=True,
)
