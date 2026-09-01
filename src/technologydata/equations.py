# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""
Equation and EquationRegistry for bidirectional parameter linking via equations in SymPy.

**Design**
Each equation is registered as a symbolic expression equal to zero, e.g.
for ``a = b`` the equation is registered as ``a - b`` and the ``= 0`` part is
not registered.
The package SymPy is used to solve the expression for *any* of its participant
variables after registration assuming all other variables are given.
This allows for performant usage of the equations post the initial registration
in any direction.

**Equation registry**
An equation registry is used to collect all equations.
The registry contains functions for managing the member equations and look-up
functions for finding equations that contain specific variables (parameters).

Similarly to the unit registry, there is a default equation registry for the package
with default equations already loaded in from the package data.
Equations can be programmatically added or loaded from external file.

**Units**
Units are propagated automatically using the ``pint`` of the ``Parameter`` objects
used in the calculations without any extra annotation on the formula itself.

Exception: Parameters that appear in *exponent positions* in the solved
expression (e.g. ``lifetime`` in ``(1+wacc)**(-lifetime)``) are passed as
plain magnitudes without units.
Raising a quantity to a dimensioned power is physically undefined.
In real-world formulas such a parameter usually represents a dimensionless count
whose physical unit is a label, not a true dimension, and thus we ignore them.

When pint arithmetic itself fails (e.g. if the solved expression contains a
transcendental function applied to a non-dimensionless quantity), evaluation
falls back to magnitudes and the result is returned with ``units=None``.
Might not be the best design, but if someone stumbles across it, we're open to
suggestions on how to improve this.

**Unit consistency check**
Unit consistency is checked through pint with symbolic calculations.
With numeric calculations this check does not work so nicely.

**Solving of equations**
----------------
To avoid SymPy hanging on transcendental equations (e.g. solving for WACC
inside an annuity formula where it appears both linearly and as an exponent
base), the solver follows this two-step strategy:

1. Symbolic-first: solve the expression with purely abstract symbols, then
   evaluate the result via pint arithmetic. Abstract symbolic solving is
   faster than working with floating-point numbers because
   SymPy's algebraic algorithms are optimised for symbolic manipulation.

2. **Numeric fallback**: if the symbolic step produces no result, substitute
   the known numeric values first, then call solve on the simplified expression.
   This can succeed in cases where SymPy's heuristics prefer concrete numbers.

The solving is wrapped in a timeout using `overdue` to prevent the system
from hanging indefinitely on difficult equations.
If no SymPy solution is found
within `_SOLVE_TIMEOUT_SECONDS` the call is cancelled and an error raised.
"""

from __future__ import annotations

# `from __future__ import annotations` makes all annotations lazy strings at
# runtime. With the TYPE_CHECKING guard below this lets us reference
# `Parameter` in type hints without importing which may lead to circular imports
import math
import pathlib
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, TypedDict, cast

import overdue
import pydantic
import sympy as sp
import yaml

from technologydata.parameter import Parameter

if TYPE_CHECKING:
    from technologydata.parameter import Parameter


class EquationSummary(TypedDict):
    """Serializable summary of a registered equation."""

    name: str
    parameters: list[str]
    eq_str: str
    priority: int
    description: str | None


class EquationConfig(pydantic.BaseModel):
    """Schema for one equation entry loaded from YAML."""

    name: str
    parameters: list[str]
    eq_str: str
    priority: int = pydantic.Field(default=0, ge=0)
    description: str | None = None


# Seconds to wait for SymPy before declaring "no analytical solution".
# Equations should usually solve well below under a second, but
# transcendental equations will hang forever
_SOLVE_TIMEOUT_SECONDS = 5
_EQUATION_REPR_MAX_EXPR_LENGTH = 80


def _solve_with_timeout(expr: sp.Expr, symbol: sp.Symbol) -> list[sp.Expr]:
    """Call `sp.solve(expr, symbol)` with a timeout to prevent hanging on transcendental equations."""
    with overdue.timeout_set_to(_SOLVE_TIMEOUT_SECONDS, raise_exception=True):
        # sp.solve is untyped (returns Any); the actual runtime type here is a
        # list of solved expressions.
        return cast("list[sp.Expr]", sp.solve(expr, symbol))


def _get_exponent_symbols(expr: sp.Expr) -> set[sp.Symbol]:
    """Return all free symbols that appear in any exponent position within *expr*."""
    result: set[sp.Symbol] = set()
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow):
            result |= node.exp.free_symbols
    return result


def _evaluate_solution(
    f: Callable[..., Any], values: list[object]
) -> tuple[float, object] | None:
    """
    Evaluate a lambdified solution with the given input values.

    Returns the ``(magnitude, raw_result)`` pair, or ``None`` if the
    evaluation fails or does not produce a finite number.
    """
    try:
        raw = f(*values)
        mag = float(raw.magnitude) if hasattr(raw, "magnitude") else float(raw)
    except Exception:  # noqa: BLE001
        return None
    return None if math.isnan(mag) else (mag, raw)


class Equation:
    """
    A symbolic equation linking multiple parameters.

    The equation is expressed as a string equal to zero.
    Sympy is used to solve the equation for any of its participating parameters
    given the others.

    Parameters
    ----------
    name : str
        Unique name given to this equation. Used to identify the equation in
        a equation registry and for tracking `Parameter` provenance information.
    parameters : list of str
        The names of all parameters that participate in the equation. Names must be
        exactly the same as those used in the equation string.
        Internally they are not passed directly to SymPy's parser, i.e. are not subject
        to the naming restriction of SymPy identifiers.
    eq_str : str
        The equation string, using SymPy-compatible syntax. Parameter names must appear
        exactly as listed in `parameters` and may include spaces or other special characters,
        they are not directly passed on to SymPy's parser and can therefore be arbitrary strings.
        The expression is set to zero, so `"a - b*c"` represents the relationship ``a = b*c``.
    priority : int
        Priority used when multiple equations can solve the same target.
        Higher values are preferred. Defaults to ``0``.

    """

    def __init__(
        self,
        name: str,
        parameters: list[str],
        eq_str: str,
        priority: int = 0,
        description: str | None = None,
    ) -> None:
        self.name = name
        self.parameters = parameters
        self.expr_str = eq_str
        if priority < 0:
            raise ValueError("Equation priority must be >= 0.")
        self.priority = priority
        self.description = description

        # Validate names once and build the internal symbolic representation once.
        if any(p.startswith("_p") and p[2:].isdigit() for p in self.parameters):
            raise ValueError(
                f"Equation '{self.name}' has parameters that conflict with internal symbol naming: {self.parameters}. "
                "Parameter names cannot start with '_p' followed by digits."
            )

        self._param_idx = {p: i for i, p in enumerate(self.parameters)}
        self._symbols_by_parameter = {
            p: sp.Symbol(f"_p{self._param_idx[p]}") for p in self.parameters
        }

        safe_expr = self.expr_str
        for p in sorted(self.parameters, key=len, reverse=True):
            safe_expr = safe_expr.replace(p, f"_p{self._param_idx[p]}")
        self._expr = sp.sympify(safe_expr)

        # Precompute symbolic solutions for each target once at registration.
        # Targets with no symbolic solution are cached as an empty tuple.
        self._symbolic_solutions_by_target: dict[str, tuple[sp.Expr, ...]] = {}
        for target in self.parameters:
            try:
                solutions = _solve_with_timeout(
                    self._expr, self._symbols_by_parameter[target]
                )
            except Exception:  # noqa: BLE001
                solutions = []
            self._symbolic_solutions_by_target[target] = tuple(solutions)

    def __repr__(self) -> str:
        """Return a concise human-readable representation for REPL usage."""
        expr = self.expr_str
        if len(expr) > _EQUATION_REPR_MAX_EXPR_LENGTH:
            expr = expr[: _EQUATION_REPR_MAX_EXPR_LENGTH - 3] + "..."

        return (
            "Equation("
            f"name={self.name!r}, "
            f"parameters={self.parameters!r}, "
            f"eq_str={expr!r}, "
            f"priority={self.priority!r}, "
            f"description={self.description!r}"
            ")"
        )

    def __str__(self) -> str:
        """Return a human-readable, math-like rendering of the equation."""
        s = f"{self.name}: {self.expr_str} = 0"
        if self.description:
            s += f" ({self.description})"
        return s

    def can_solve_for(self, target: str, available: dict[str, Parameter]) -> bool:
        """
        Check if an equation can solve for `target` parameter with the provided `available` parameters.

        Parameters
        ----------
        target : str
            The parameter to check.
        available : dict
            Known parameter values.

        Returns
        -------
        bool
            `True` if the equation can solve for `target`, else `False`.

        """
        # The equation must involve the target parameter, and all other
        # participating parameters must be available for solving.
        return target in self.parameters and all(
            p in available for p in self.parameters if p != target
        )

    def solve_for(self, target: str, params: dict[str, Parameter]) -> Parameter:
        """
        Solve the equation for the `target` parameter given the remaining parameters.

        Parameters
        ----------
        target : str
            The parameter to solve for.
        params : dict
            Known parameter values, i.e. all other equation participants except the `target`.

        Returns
        -------
        Parameter
            The calculated parameter including provenance information.
            Unit information from parameters that appear as an exponent are evaluated using
            their magnitudes only as pint cannot raise a quantity to a dimensioned power;
            their physical unit label does not flow into the result.

        Raises
        ------
        ValueError
            If SymPy cannot find a closed-form analytical solution.

        """
        # Only parameters required for solving this target are relevant.
        input_params = [p for p in self.parameters if p != target and p in params]
        input_syms = [self._symbols_by_parameter[p] for p in input_params]

        # Step 1: solve symbolically, evaluate via pint arithmetic.
        # Using lambdify + pint Quantities propagates units automatically.
        # Symbolic solving is significantly faster than working with floats.
        symbolic_solutions = self._symbolic_solutions_by_target.get(target, ())
        has_symbolic_solution = bool(symbolic_solutions)
        results: list[tuple[float, object]] = []

        for sym_sol in symbolic_solutions:
            # Parameters in exponent positions must be passed as plain magnitudes:
            # pint cannot raise a quantity to a dimensioned power (e.g. x**20year).
            # Such parameters are typically dimensionless counts (e.g. number of
            # years) whose unit is a label, not a true physical dimension.
            exponent_syms = _get_exponent_symbols(sym_sol)
            f = sp.lambdify(input_syms, sym_sol, modules="math")

            input_values = [
                params[p].magnitude
                if self._symbols_by_parameter[p] in exponent_syms
                else params[p]._pint_quantity
                for p in input_params
            ]

            result = _evaluate_solution(f, input_values)
            if result is None:
                # Pint arithmetic failed (e.g. transcendental function on a
                # non-dimensionless quantity). Fall back to magnitude-only.
                mag_values: list[object] = [params[p].magnitude for p in input_params]
                result = _evaluate_solution(f, mag_values)
            if result is not None:
                results.append(result)

        if not results:
            # Step 2: substitute magnitudes first, then solve. This can succeed
            # when SymPy's heuristics prefer concrete numbers over abstract symbols.
            subs_mag = {
                self._symbols_by_parameter[p]: params[p].magnitude for p in input_params
            }
            try:
                for sol in _solve_with_timeout(
                    self._expr.subs(subs_mag), self._symbols_by_parameter[target]
                ):
                    try:
                        mag = float(sol)
                        if not math.isnan(mag):
                            results.append((mag, mag))
                    except (TypeError, ValueError):
                        pass
            except Exception as exc:  # noqa: BLE001
                if not has_symbolic_solution:
                    raise NotImplementedError(
                        f"Formula '{self.name}' cannot solve for '{target}' analytically."
                    ) from exc
                raise

        if not results:
            if not has_symbolic_solution:
                raise NotImplementedError(
                    f"Formula '{self.name}' cannot solve for '{target}' analytically."
                )
            raise ValueError(
                f"Formula '{self.name}' has no analytical solution for '{target}' "
                "with the given parameter values. "
                "This typically means the variable appears in a transcendental term "
                "(e.g. as an exponent base). Consider providing the value directly."
            )

        # Physical parameters are positive by convention in energy system
        # modelling (costs, efficiencies, lifetimes are never negative).
        # Prefer positive real solutions; if none exist, fall back to any real.
        positive = [(mag, raw) for mag, raw in results if mag > 0]
        magnitude, raw_result = (positive or results)[0]

        result_units = str(raw_result.units) if hasattr(raw_result, "units") else None

        input_values_str = "\n".join(f"  {p} = {params[p]}" for p in input_params)
        provenance_entry = (
            f"Calculated from other parameters using formula '{self.name}': "
            f"{self.expr_str} = 0\n"
            f"Input values:\n{input_values_str}"
        )
        return Parameter(
            magnitude=magnitude,
            units=result_units,
            provenance=[provenance_entry],
        )


class EquationRegistry:
    """
    Registry to make :class:`Equation` available for parameter omni-directional computation.

    Each equation in the registry is registered for every parameter it involves.
    This way the registry can determine the select the equations suitable for
    calculating a parameter without knowing beforehand which equation to use.

    Multiple equations can be associated with the same parameter,
    e.g. two different methods for computing EAC.
    Equation selection can be influenced by assigning per-equation priorities.

    Attributes
    ----------
    _equations_by_parameter : dict[str, list[Equation]]
        Index from parameter name to all equations that include this parameter.
        Used for equation discovery when solving for a target parameter.
    _equations_by_name : dict[str, Equation]
        Index from unique equation name to the corresponding equation object.
        Used for uniqueness checks and global equation listing.

    """

    def __init__(self) -> None:
        # Parameter-centric index used by get_equation/can_calculate.
        self._equations_by_parameter: dict[str, list[Equation]] = {}
        # Name-centric index used for uniqueness checks and full registry listing.
        self._equations_by_name: dict[str, Equation] = {}

    def register(
        self,
        name: str,
        parameters: list[str],
        eq_str: str,
        priority: int = 0,
        overwrite: bool = False,
        description: str | None = None,
    ) -> None:
        """
        Register an equation linking a set of parameters.

        All the `parameters` are indexed to this equation for equation discovery.

        Parameters
        ----------
        name : str
            Unique equation name to identify the equation.
        parameters : list of str
            All parameter names that participate in this equation.
        eq_str : str
            The equation as string representation equal to zero, i.e. LHS of the
            equation with $LHS = 0$. The equation must contain the parameter names
            exactly as listed in `parameters` (including any spaces).
        priority : int, optional
            Priority used when multiple equations can solve for the same target.
            Higher values are preferred. Defaults to ``0``.
        overwrite : bool, optional
            If ``True`` and an equation with the same name already exists,
            the existing equation is replaced.
        description : str, optional
            Optional free-text description for documentation or context.

        """
        existing = self._equations_by_name.get(name)
        if existing is not None:
            same_definition = (
                existing.parameters == parameters
                and existing.expr_str == eq_str
                and existing.priority == priority
                and existing.description == description
            )
            if same_definition:
                return

            if not overwrite:
                raise ValueError(
                    f"Equation name '{name}' already exists with a different definition. "
                    "Set overwrite=True to replace it."
                )

            self._remove_equation(name)

        # Setup the equation
        formula = Equation(
            name=name,
            parameters=parameters,
            eq_str=eq_str,
            priority=priority,
            description=description,
        )
        self._equations_by_name[name] = formula

        # Register the equation in the registry for each parameter it involves
        for param in parameters:
            self._equations_by_parameter.setdefault(param, []).append(formula)

    def _remove_equation(self, name: str) -> None:
        """Remove one equation by name from all internal indexes."""
        equation = self._equations_by_name.pop(name)
        for param in equation.parameters:
            equations = self._equations_by_parameter.get(param)
            if equations is None:
                continue
            self._equations_by_parameter[param] = [
                current for current in equations if current.name != name
            ]
            if not self._equations_by_parameter[param]:
                del self._equations_by_parameter[param]

    def load_from_yaml(
        self,
        yaml_files: str | pathlib.Path | Sequence[str | pathlib.Path],
        overwrite: bool = False,
    ) -> None:
        """
        Load equation definitions from one or multiple YAML files.

        Parameters
        ----------
        yaml_files : str | pathlib.Path | Sequence[str | pathlib.Path]
            Path(s) to YAML file(s) containing equation definitions.
        overwrite : bool, optional
            If ``True``, allow replacing existing equations with the same name.
            Defaults to ``False``.

        Raises
        ------
        ValueError
            If the YAML content is not a list of equation definitions or
            if conflicting equation names are found and ``overwrite=False``.

        """
        if isinstance(yaml_files, (str, pathlib.Path)):
            files = [yaml_files]
        else:
            files = list(yaml_files)

        for file in files:
            path = pathlib.Path(file)
            with path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle)

            if payload is None:
                continue
            if not isinstance(payload, list):
                raise ValueError(
                    f"YAML file '{path}' must contain a list of equations at the root."
                )

            for raw_entry in payload:
                config = EquationConfig.model_validate(raw_entry)
                self.register(
                    name=config.name,
                    parameters=config.parameters,
                    eq_str=config.eq_str,
                    priority=config.priority,
                    overwrite=overwrite,
                    description=config.description,
                )

    @classmethod
    def from_yaml(
        cls,
        yaml_files: str | pathlib.Path | Sequence[str | pathlib.Path],
    ) -> EquationRegistry:
        """
        Create a new registry initialized from one or more YAML files.

        Parameters
        ----------
        yaml_files : str | pathlib.Path | Sequence[str | pathlib.Path]
            Path(s) to YAML file(s) containing equation definitions.

        Returns
        -------
        EquationRegistry
            A new instance of EquationRegistry with equations loaded from the specified YAML files.

        """
        registry = cls()
        registry.load_from_yaml(yaml_files=yaml_files, overwrite=False)
        return registry

    def list_equations(self, target: str | None = None) -> list[EquationSummary]:
        """
        List registered equations as serializable summaries.

        Parameters
        ----------
        target : str, optional
            If provided, only equations registered for this target parameter
            are returned.

        Returns
        -------
        list[EquationSummary]
            Equation summaries sorted alphabetically by equation name,
            case-insensitive.

        Raises
        ------
        ValueError
            If `target` is provided but no equation is registered for it.

        """
        if target is None:
            equations = list(self._equations_by_name.values())
        else:
            equations = self._equations_by_parameter.get(target, [])
            if not equations:
                raise ValueError(f"No equation registered for parameter '{target}'.")

        return [
            {
                "name": equation.name,
                "parameters": equation.parameters,
                "eq_str": equation.expr_str,
                "priority": equation.priority,
                "description": equation.description,
            }
            for equation in sorted(equations, key=lambda eq: eq.name.lower())
        ]

    def get_equation(
        self,
        target: str,
        params: dict[str, Parameter],
        equation_name: str | None = None,
    ) -> Equation:
        """
        Return the best applicable :class:`Equation` for the `target` parameter.

        Selection priority:
        1. The equation explicitly requested by `equation_name`
          2. Higher-priority equations whose inputs are all present.
          3. For equal priority, earlier registration order.

        Parameters
        ----------
        target : str
            The name of the parameter to derive. Must match the name in the registered equation.
        params : dict
            Known parameter values, possible participants of the equation.
            Must contain all parameters except `target`.
            Used to determine eligible equations for calculating the `target`.
        equation_name : str, optional
            Name of a specific equation variant to use.
            If not provided, an applicable equation is selected automatically.

        Raises
        ------
        KeyError
            If the equation requested by `equation_name` is not registered.
        ValueError
            If there is no equation registered that allows for calculation of the
            `target` parameter with the provided `params`.

        """
        # All possible registered equations for the target parameter
        candidates = self._equations_by_parameter.get(target, [])

        # Fail fast
        if not candidates:
            raise ValueError(f"No equation registered for parameter '{target}'.")

        # Selection by equation_name
        if equation_name is not None:
            # Find the requested equation
            named = [f for f in candidates if f.name == equation_name]
            if not named:
                raise KeyError(
                    f"No equation named '{equation_name}' registered for '{target}'."
                )

            # Check if all required parameters are available for this equation
            f = named[0]
            if not f.can_solve_for(target, params):
                missing = [p for p in f.parameters if p != target and p not in params]
                raise ValueError(
                    f"Equation '{equation_name}' cannot solve for '{target}' because "
                    f"of missing parameters: {missing}."
                )
            return f

        # Selection by available parameters and equation priority.
        # Higher priority first; stable sort preserves registration order on ties.
        for f in sorted(candidates, key=lambda f: f.priority, reverse=True):
            if f.can_solve_for(target, params):
                return f

        missing_params_in_equations = "\n".join(
            f" * '{f.name}': provided params = {[p for p in f.parameters if p != target and p in params]}, missing params = {[p for p in f.parameters if p != target and p not in params]}"
            for f in candidates
        )
        raise ValueError(
            f"No equation for parameter '{target}' can be used with the provided parameters.\n"
            f"Available equations for '{target}' are:\n" + missing_params_in_equations
        )

    def calculate(
        self,
        target: str,
        params: dict[str, Parameter],
        equation_name: str | None = None,
    ) -> Parameter:
        """
        Calculate the `target` parameter using the available equations in the registry.

        If `equation_name` is provided, the corresponding equation is used. Otherwise,
        the registry automatically selects an applicable equation based on the provided parameters.

        Information on the equation used and calculation performed is recorded in the `provenance`
        attribute of the returned :class:`Parameter`.

        Parameters
        ----------
        target : str
            The parameter to derive.
        params : dict
            Names of the known parameters and their corresponding :class:`Parameter` values.
        equation_name : str, optional
            Name of a specific equation to use for the calculation. If not provided, an applicable
            equation is selected automatically.

        Returns
        -------
        Parameter
            The calculated parameter.

        """
        equation = self.get_equation(target, params, equation_name)
        return equation.solve_for(target, params)

    def can_calculate(self, target: str, params: dict[str, Parameter]) -> bool:
        """
        Check if the registry has an equation to calculate the `target` parameter from the provided parameters.

        Parameters
        ----------
        target : str
            The parameter to calculate.
        params : dict
            Names of the known parameters and their corresponding :class:`Parameter` values.

        Returns
        -------
        bool
            `True` if any registered formula can solve for `target`, else `False`.

        """
        return any(
            equation.can_solve_for(target, params)
            for equation in self._equations_by_parameter.get(target, [])
        )
