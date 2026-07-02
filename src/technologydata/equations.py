# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""
Equation and EquationRegistry for bidirectional parameter linking via equations in SymPy.

Design
------
Each equation is registered as a symbolic expression equal to zero (e.g.
``eac - sic*wacc/(1-(1+wacc)**(-lifetime))``). SymPy solves the expression
for *any* of its participant variables given the others, so one registration
covers every direction automatically.

Unit handling
-------------
Units are propagated automatically using the pint Quantities that each
``Parameter`` already carries. The lambdified SymPy solution is evaluated with
pint ``Quantity`` objects as inputs, so the result inherits consistent units
without any extra annotation on the formula itself.

One exception: parameters that appear in *exponent positions* in the solved
expression (e.g. ``lifetime`` in ``(1+wacc)**(-lifetime)``) are passed as
plain magnitudes. Raising a quantity to a dimensioned power is physically
undefined; in every real-world formula such a parameter represents a
dimensionless count whose physical unit is a label, not a true dimension.

When pint arithmetic itself fails (e.g. if the solved expression contains a
transcendental function applied to a non-dimensionless quantity), evaluation
falls back to magnitudes and the result is returned with ``units=None``.

Currency consistency check
--------------------------
Before any computation, only the parameters required by the selected equation
are checked. Among those, parameters that carry a currency unit must share the
same currency and currency year. If they do not, a ``ValueError`` is raised.

Solving strategy
----------------
To avoid SymPy hanging on transcendental equations (e.g. solving for WACC
inside an annuity formula where it appears both linearly and as an exponent
base), the solver follows this two-step strategy:

1. **Symbolic-first**: solve the expression with purely abstract symbols, then
   evaluate the result via pint arithmetic. Abstract symbolic solving is
   significantly faster than working with floating-point numbers because
   SymPy's algebraic algorithms are optimised for symbolic manipulation.

2. **Numeric fallback**: if the symbolic step produces no result, substitute
   the known numeric values first, then call solve on the simplified expression.
   This can succeed in cases where SymPy's heuristics prefer concrete numbers.

Both steps are wrapped in a SIGALRM-based timeout (Unix/Linux only). If SymPy
does not return within ``_SOLVE_TIMEOUT_SECONDS`` the call is cancelled and
treated as "no solution found". On platforms without SIGALRM (Windows) the
timeout is silently skipped and transcendental equations may hang — this is
considered acceptable given the primary deployment target.
"""

from __future__ import annotations

# `from __future__ import annotations` makes all annotations lazy strings at
# runtime. Together with the TYPE_CHECKING guard below this lets us reference
# `Parameter` in type hints without importing it at module load time, which
# would create a circular import: __init__.py → technology.py → formulas.py
# → parameter.py → import technologydata (circular).
import signal as _signal
from typing import TYPE_CHECKING

import sympy as sp

if TYPE_CHECKING:
    from technologydata.parameter import Parameter

# Seconds to wait for SymPy before declaring "no analytical solution".
# Most tractable algebraic solutions complete in well under a second; this
# budget is intentionally generous to handle slow-but-solvable cases while
# still catching transcendental equations that would otherwise hang forever.
_SOLVE_TIMEOUT_SECONDS = 5

# SIGALRM is only available on Unix/Linux. On Windows the timeout degrades
# gracefully to a no-op (users may experience hangs on transcendental eqs).
_HAS_SIGALRM = hasattr(_signal, "SIGALRM")


class _SolveTimeout(Exception):
    """Raised by the SIGALRM handler when SymPy exceeds the solve budget."""


def _solve_with_timeout(expr: sp.Expr, symbol: sp.Symbol) -> list[sp.Expr]:
    """
    Call ``sp.solve(expr, symbol)`` with a SIGALRM timeout.

    Returns an empty list if the solver exceeds ``_SOLVE_TIMEOUT_SECONDS`` or
    raises any internal SymPy exception (e.g. ``NotImplementedError``).
    """
    if not _HAS_SIGALRM:
        # Fallback for Windows: no timeout, user must avoid transcendental eqs
        try:
            return sp.solve(expr, symbol)  # type: ignore[return-value]
        except Exception:  # noqa: BLE001
            return []

    def _handler(signum: int, frame: object) -> None:  # noqa: ARG001
        raise _SolveTimeout()

    old_handler = _signal.signal(_signal.SIGALRM, _handler)  # type: ignore[attr-defined]
    _signal.alarm(_SOLVE_TIMEOUT_SECONDS)  # type: ignore[attr-defined]
    try:
        return sp.solve(expr, symbol)  # type: ignore[return-value]
    except _SolveTimeout:
        return []
    except Exception:  # noqa: BLE001
        return []
    finally:
        _signal.alarm(0)  # type: ignore[attr-defined]
        _signal.signal(_signal.SIGALRM, old_handler)  # type: ignore[attr-defined]


def _get_exponent_symbols(expr: sp.Expr) -> set[sp.Symbol]:
    """Return all free symbols that appear in any exponent position within *expr*."""
    result: set[sp.Symbol] = set()
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow):
            result |= node.exp.free_symbols
    return result


class Equation:
    """
    A symbolic equation linking multiple parameters bidirectionally.

    The equation is expressed as a SymPy-parseable string equal to zero
    (e.g. ``"eac - sic*wacc/(1-(1+wacc)**(-lifetime))"``) and can be solved
    for any of its participating parameters given the others.

    Parameters
    ----------
    name : str
        Unique name for this equation variant, used for explicit selection.
    parameters : list of str
        All parameter names that participate in the equation. Names may contain
        spaces or other characters — they are mapped to positional SymPy symbols
        internally and never passed to SymPy's parser directly.
    eq_str : str
        SymPy-parseable expression string. Parameter names must appear exactly
        as listed in *parameters* (including any spaces). The expression is set
        to zero, so ``"a - b*c"`` represents the relationship ``a = b*c``.
    default : bool
        If ``True``, this equation is preferred over others that also cover
        the same target when no equation name is specified explicitly.

    """

    def __init__(
        self,
        name: str,
        parameters: list[str],
        eq_str: str,
        default: bool = False,
    ) -> None:
        self.name = name
        self.parameters = parameters
        self.expr_str = eq_str
        self.default = default

    def can_solve_for(self, target: str, available: dict[str, Parameter]) -> bool:
        """Return ``True`` if every parameter except *target* is in *available*."""
        if target not in self.parameters:
            return False
        return all(p in available for p in self.parameters if p != target)

    def solve_for(self, target: str, params: dict[str, Parameter]) -> Parameter:
        """
        Solve the formula for *target* given the remaining parameters.

        Parameters
        ----------
        target : str
            The parameter to derive.
        params : dict
            Known parameter values — every participant except *target*.

        Returns
        -------
        Parameter
            The derived parameter with magnitude, units, and provenance set.
            Units are propagated automatically from the input pint Quantities.
            Parameters that appear in exponent positions are evaluated using
            their magnitudes only (pint cannot raise a quantity to a dimensioned
            power); their physical unit label does not flow into the result.

        Raises
        ------
        ValueError
            If currencies are inconsistent across the inputs, or if SymPy
            cannot find a closed-form analytical solution within the timeout
            budget (see module-level ``_SOLVE_TIMEOUT_SECONDS``).

        """
        from technologydata.parameter import Parameter as Param

        # Map each parameter to a positional symbol (_p0, _p1, …) so that
        # parameter names with spaces or other non-identifier characters work
        # transparently. Replace longest names first to avoid partial matches
        # (e.g. "investment cost" replaced before "cost").
        param_idx = {p: i for i, p in enumerate(self.parameters)}
        syms = {p: sp.Symbol(f"_p{param_idx[p]}") for p in self.parameters}
        safe_expr = self.expr_str
        for p in sorted(self.parameters, key=len, reverse=True):
            safe_expr = safe_expr.replace(p, f"_p{param_idx[p]}")
        expr = sp.sympify(safe_expr)

        # Only parameters required for solving this target are relevant.
        input_params = [p for p in self.parameters if p != target and p in params]
        input_syms = [syms[p] for p in input_params]

        # Step 1: solve symbolically, evaluate via pint arithmetic.
        # Using lambdify + pint Quantities propagates units automatically.
        # Symbolic solving is significantly faster than working with floats.
        symbolic_solutions = _solve_with_timeout(expr, syms[target])
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
                if syms[p] in exponent_syms
                else params[p]._pint_quantity
                for p in input_params
            ]

            try:
                raw = f(*input_values)
                mag = float(raw.magnitude) if hasattr(raw, "magnitude") else float(raw)
                if mag == mag:  # reject NaN
                    results.append((mag, raw))
            except Exception:  # noqa: BLE001
                # Pint arithmetic failed (e.g. transcendental function on a
                # non-dimensionless quantity). Fall back to magnitude-only.
                mag_values = [params[p].magnitude for p in input_params]
                try:
                    raw_mag = f(*mag_values)
                    mag = float(raw_mag)
                    if mag == mag:
                        results.append((mag, raw_mag))
                except Exception:  # noqa: BLE001
                    pass

        if not results:
            # Step 2: substitute magnitudes first, then solve. This can succeed
            # when SymPy's heuristics prefer concrete numbers over abstract symbols.
            subs_mag = {syms[p]: params[p].magnitude for p in params if p in syms}
            for sol in _solve_with_timeout(expr.subs(subs_mag), syms[target]):
                try:
                    mag = float(sol)
                    if mag == mag:
                        results.append((mag, mag))
                except (TypeError, ValueError):
                    pass

        if not results:
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
        return Param(magnitude=magnitude, units=result_units, provenance=self.name)


class EquationRegistry:
    """
    Registry to make :class:`Equation` available for parameter omni-directional computation.

    Each equation in the registry is registered for every parameter it involves.
    This way the registry can determine the select the equations suitable for
    calculating a parameter without knowing beforehand which equation to use.

    Multiple equations can be associated with the same parameter,
    e.g. two different methods for computing EAC.
    A default equation per parameter can be set, which is used when no explicit choice is made.
    """

    def __init__(self) -> None:
        self._equations: dict[str, list[Equation]] = {}

    def register(
        self,
        name: str,
        parameters: list[str],
        eq_str: str,
        default: bool = False,
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
        default : bool, optional
            If ``True`` this equation is preferred over other equations
            when multiple equations can be used to calculate the same parameter.
            If multiple equations are marked as default, the order of registration
            (last registered, first used) is used to determine which equation to use.

        """
        # Setup the equation
        formula = Equation(
            name=name,
            parameters=parameters,
            eq_str=eq_str,
            default=default,
        )

        # Register the equation in the registry for each parameter it involves
        for param in parameters:
            self._equations.setdefault(param, []).append(formula)

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
        2. Default-flagged equations (`default=True`) whose inputs are all present
           in their order of registration.
        3. Any other registered equation whose inputs are all present in their
           order of registration.

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
        candidates = self._equations.get(target, [])

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

        # Selection by available parameters and by default flags
        # Sort so default=True equations come first;
        # sort such that the registration order within each group is preserved
        for f in sorted(candidates, key=lambda f: f.default, reverse=True):
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
        Check if the registry has an equation that can calculate the `target` parameter
        using the provided parameters.

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
            for equation in self._equations.get(target, [])
        )
