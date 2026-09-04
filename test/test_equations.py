# SPDX-FileCopyrightText: technologydata contributors
#
# SPDX-License-Identifier: MIT

"""Tests for Equation, EquationRegistry, and Technology.calculate_parameters."""

import pathlib

import pytest

import technologydata  # noqa: F401 — ensures default_formulas are registered
import technologydata.equations as equations_module
from technologydata.default_equations import equation_registry
from technologydata.equations import Equation, EquationRegistry
from technologydata.parameter import Parameter
from technologydata.technology import Technology

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

EAC_ANNUITY_PARAMS = {
    "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
    "wacc": Parameter(magnitude=0.07, units="dimensionless"),
    "lifetime": Parameter(magnitude=20.0, units="year"),
}

EAC_SIMPLE_PARAMS = {
    "total_investment_cost": Parameter(magnitude=2000.0, units="USD_2020/kW"),
    "lifetime": Parameter(magnitude=20.0, units="year"),
}

# eac_annuity forward result: 1000 * 0.07 / (1 - 1.07^-20)
_EAC_ANNUITY_EXPECTED = 1000.0 * 0.07 / (1 - 1.07**-20)
# eac_simple forward result: 2000 / 20
_EAC_SIMPLE_EXPECTED = 100.0
# annuity_factor for wacc=0.07, lifetime=20
_AF_EXPECTED = 0.07 / (1 - 1.07**-20)


# ---------------------------------------------------------------------------
# Equation.can_solve_for
# ---------------------------------------------------------------------------


class TestEquationCanSolveFor:
    """Test suite for Equation.can_solve_for."""

    def test_can_solve_for_target_when_all_others_present(self) -> None:
        """Test that can_solve_for returns True when all other parameters are present."""
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )
        params = {
            "b": Parameter(magnitude=1.0, units="dimensionless"),
            "c": Parameter(magnitude=2.0, units="dimensionless"),
        }
        assert link.can_solve_for("a", params) is True

    def test_cannot_solve_for_target_not_in_parameters(self) -> None:
        """Test that can_solve_for returns False when the target is not one of the equation's parameters."""
        link = Equation(
            name="test",
            parameters=["a", "b"],
            eq_str="a - b",
        )
        params = {"a": Parameter(magnitude=1.0, units="dimensionless")}
        assert link.can_solve_for("x", params) is False

    def test_cannot_solve_when_input_missing(self) -> None:
        """Test that can_solve_for returns False when a required input parameter is missing."""
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )
        # c is missing
        params = {"b": Parameter(magnitude=1.0, units="dimensionless")}
        assert link.can_solve_for("a", params) is False


class TestEquationRepr:
    """Test suite for Equation.__repr__."""

    def test_repr_includes_core_fields(self) -> None:
        """Test that repr includes the equation's name, parameters, eq_str, and priority."""
        equation = Equation(
            name="simple",
            parameters=["target", "input_a", "input_b"],
            eq_str="target - input_a - input_b",
            priority=2,
        )

        rep = repr(equation)

        assert rep.startswith("Equation(")
        assert "name='simple'" in rep
        assert "parameters=['target', 'input_a', 'input_b']" in rep
        assert "eq_str='target - input_a - input_b'" in rep
        assert "priority=2" in rep

    def test_repr_preserves_parameter_order(self) -> None:
        """Test that repr preserves the original order of the parameters list."""
        equation = Equation(
            name="ordered",
            parameters=["z", "x", "y"],
            eq_str="z - x - y",
        )

        rep = repr(equation)

        assert "parameters=['z', 'x', 'y']" in rep

    def test_repr_truncates_long_expression(self) -> None:
        """Test that repr truncates a long eq_str expression with an ellipsis."""
        long_expr = "x - " + " + ".join(f"p{i}" for i in range(100))
        equation = Equation(
            name="long",
            parameters=["x", "p0"],
            eq_str=long_expr,
        )

        rep = repr(equation)

        assert "eq_str='" in rep
        assert "...'" in rep
        assert long_expr not in rep


class TestEquationStr:
    """Test suite for Equation.__str__."""

    def test_str_without_description(self) -> None:
        """Test that str formats the equation without a description."""
        equation = Equation(
            name="simple",
            parameters=["target", "input_a", "input_b"],
            eq_str="target - input_a - input_b",
        )

        assert str(equation) == "simple: target - input_a - input_b = 0"

    def test_str_with_description(self) -> None:
        """Test that str appends the description in parentheses when present."""
        equation = Equation(
            name="simple",
            parameters=["target", "input_a", "input_b"],
            eq_str="target - input_a - input_b",
            description="Sum of two inputs.",
        )

        assert (
            str(equation)
            == "simple: target - input_a - input_b = 0 (Sum of two inputs.)"
        )

    def test_str_does_not_truncate_long_expression(self) -> None:
        """Test that str does not truncate a long eq_str expression."""
        long_expr = "x - " + " + ".join(f"p{i}" for i in range(100))
        equation = Equation(
            name="long",
            parameters=["x", "p0"],
            eq_str=long_expr,
        )

        assert long_expr in str(equation)


class TestEquationCaching:
    """Test suite for symbolic solution caching on Equation."""

    def test_symbolic_solutions_precomputed_on_registration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that symbolic solutions are precomputed once per parameter at registration time."""
        calls = {"count": 0}

        def fake_solve_with_timeout(expr: object, symbol: object) -> list[object]:
            calls["count"] += 1
            return []

        monkeypatch.setattr(
            equations_module, "_solve_with_timeout", fake_solve_with_timeout
        )

        Equation(
            name="precompute",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )

        assert calls["count"] == 3

    def test_solve_for_uses_cached_symbolic_solution(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that solve_for reuses the cached symbolic solution instead of recomputing it."""
        equation = Equation(
            name="cached_linear",
            parameters=["a", "b"],
            eq_str="a - b",
        )

        # Any new call to _solve_with_timeout during solve_for would indicate
        # that symbolic caching is not used.
        def fail_if_called(expr: object, symbol: object) -> list[object]:
            raise AssertionError(
                "_solve_with_timeout should not be called during solve_for"
            )

        monkeypatch.setattr(equations_module, "_solve_with_timeout", fail_if_called)

        result = equation.solve_for(
            "a", {"b": Parameter(magnitude=2.0, units="dimensionless")}
        )

        assert result.magnitude == pytest.approx(2.0)

    def test_unsolved_target_skips_symbolic_step_per_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that solve_for re-invokes the symbolic solver once per call when no cached solution exists for the target."""
        equation = Equation(
            name="annuity",
            parameters=["annuity_factor", "wacc", "lifetime"],
            eq_str="annuity_factor - wacc / (1 - (1 + wacc)**(-lifetime))",
        )

        calls = {"total": 0, "symbolic": 0}

        def fake_solve_with_timeout(expr: object, symbol: object) -> list[object]:
            calls["total"] += 1
            # Symbolic step would still contain multiple free symbols.
            if len(expr.free_symbols) > 1:  # type: ignore[attr-defined]
                calls["symbolic"] += 1
            raise NotImplementedError

        monkeypatch.setattr(
            equations_module, "_solve_with_timeout", fake_solve_with_timeout
        )

        af = Parameter(magnitude=_AF_EXPECTED, units="dimensionless")
        lifetime = Parameter(magnitude=20.0, units="year")

        with pytest.raises(NotImplementedError):
            equation.solve_for("wacc", {"annuity_factor": af, "lifetime": lifetime})
        with pytest.raises(NotImplementedError):
            equation.solve_for("wacc", {"annuity_factor": af, "lifetime": lifetime})

        assert calls["symbolic"] == 0
        assert calls["total"] == 2


# ---------------------------------------------------------------------------
# Currency consistency checks
# ---------------------------------------------------------------------------


class TestCurrencyConsistency:
    """Test suite for currency-year consistency checks during solve_for."""

    def _link(self) -> Equation:
        return Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b - c",
        )

    def test_required_matching_currency_years_pass(self) -> None:
        """Test that solve_for succeeds when all required currency parameters share the same currency year."""
        params = {
            "b": Parameter(magnitude=1.0, units="USD_2020/kW"),
            "c": Parameter(magnitude=2.0, units="USD_2020/kW"),
        }
        result = self._link().solve_for("a", params)
        assert result.magnitude == pytest.approx(3.0)
        assert "USD_2020" in (result.units or "")

    def test_no_currency_required_params_does_not_raise(self) -> None:
        """Test that solve_for does not raise when no required parameters carry currency units."""
        params = {
            "b": Parameter(magnitude=0.5, units="year"),
            "c": Parameter(magnitude=0.5, units="year"),
        }
        result = self._link().solve_for("a", params)
        assert result.magnitude == pytest.approx(1.0)

    def test_mixed_with_non_currency_required_param_passes(self) -> None:
        """Test that solve_for succeeds when required parameters mix currency and non-currency units."""
        link = Equation(
            name="test",
            parameters=["a", "b", "c"],
            eq_str="a - b * c",
        )
        params = {
            "b": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "c": Parameter(magnitude=0.07, units="dimensionless"),
        }
        result = link.solve_for("a", params)
        assert result.magnitude == pytest.approx(70.0)
        assert "USD_2020" in (result.units or "")

    def test_extra_non_required_currency_param_is_ignored(self) -> None:
        """Test that a currency mismatch on a parameter not required by the equation is ignored."""
        params = {
            "b": Parameter(magnitude=2.0, units="USD_2020/kW"),
            # `x` is unrelated to this equation and should not be validated.
            "x": Parameter(magnitude=1.0, units="EUR_2020/kW"),
        }
        result = Equation(
            name="test",
            parameters=["a", "b"],
            eq_str="a - b",
        ).solve_for("a", params)
        assert result.magnitude == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# EAC — forward and backward
# ---------------------------------------------------------------------------


class TestEacAnnuity:
    """Test suite for the eac_annuity formula (forward and backward)."""

    def test_forward_eac(self) -> None:
        """Test that eac_annuity computes the expected forward EAC value."""
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.magnitude == pytest.approx(_EAC_ANNUITY_EXPECTED, rel=1e-6)

    def test_forward_eac_currency_inherited(self) -> None:
        """Test that the forward EAC result inherits the specific investment's currency and power units."""
        # lifetime appears only as exponent, so pint gives USD_2020/kW (not /year)
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.units is not None
        assert "USD_2020" in result.units
        assert "kilowatt" in result.units  # pint canonicalises kW → kilowatt

    def test_forward_eac_provenance(self) -> None:
        """Test that the forward EAC result records provenance describing the formula and inputs used."""
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.provenance is not None
        assert len(result.provenance) == 1
        entry = result.provenance[0]
        assert "calculated from other parameters" in entry.lower()
        assert "formula 'eac_annuity'" in entry
        equation = equation_registry.get_equation("eac", EAC_ANNUITY_PARAMS)
        assert equation.expr_str in entry
        for name, param in EAC_ANNUITY_PARAMS.items():
            assert name in entry
            assert str(param) in entry

    def test_backward_specific_investment(self) -> None:
        """Test that eac_annuity can be solved backward for specific_investment given eac, wacc, and lifetime."""
        eac = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        params = {
            "eac": eac,
            "wacc": EAC_ANNUITY_PARAMS["wacc"],
            "lifetime": EAC_ANNUITY_PARAMS["lifetime"],
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(1000.0, rel=1e-4)
        assert result.units is not None
        assert "USD_2020" in result.units
        assert "kilowatt" in result.units

    def test_backward_lifetime(self) -> None:
        """Test that eac_annuity can be solved backward for lifetime using the numeric fallback."""
        # Solving for lifetime requires log(); pint falls back to magnitudes.
        eac = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        params = {
            "eac": eac,
            "specific_investment": EAC_ANNUITY_PARAMS["specific_investment"],
            "wacc": EAC_ANNUITY_PARAMS["wacc"],
        }
        result = equation_registry.calculate("lifetime", params)
        assert result.magnitude == pytest.approx(20.0, rel=1e-4)


class TestEacSimple:
    """Test suite for the eac_simple formula (forward and backward)."""

    def test_forward_eac(self) -> None:
        """Test that eac_simple computes the expected forward EAC value with correct provenance and units."""
        result = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        assert result.magnitude == pytest.approx(_EAC_SIMPLE_EXPECTED)
        assert result.provenance is not None
        assert len(result.provenance) == 1
        assert "formula 'eac_simple'" in result.provenance[0]
        # eac_simple divides by lifetime directly, so pint gives /year correctly
        assert result.units is not None
        assert "kilowatt" in result.units
        assert "year" in result.units

    def test_backward_total_investment_cost(self) -> None:
        """Test that eac_simple can be solved backward for total_investment_cost given eac and lifetime."""
        eac = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        params = {"eac": eac, "lifetime": EAC_SIMPLE_PARAMS["lifetime"]}
        result = equation_registry.calculate(
            "total_investment_cost", params, equation_name="eac_simple"
        )
        assert result.magnitude == pytest.approx(2000.0)


# ---------------------------------------------------------------------------
# Annuity factor
# ---------------------------------------------------------------------------


class TestAnnuityFactor:
    """Test suite for the annuity_factor formula (forward and backward)."""

    _PARAMS = {
        "wacc": Parameter(magnitude=0.07, units="dimensionless"),
        "lifetime": Parameter(magnitude=20.0, units="year"),
    }

    def test_forward_annuity_factor(self) -> None:
        """Test that annuity_factor computes the expected forward value with provenance."""
        result = equation_registry.calculate("annuity_factor", self._PARAMS)
        assert result.magnitude == pytest.approx(_AF_EXPECTED, rel=1e-6)
        assert result.units == "dimensionless"
        assert result.provenance is not None
        assert len(result.provenance) == 1
        assert "formula 'annuity_factor'" in result.provenance[0]

    def test_backward_lifetime(self) -> None:
        """Test that annuity_factor can be solved backward for lifetime using the numeric fallback."""
        # Solving for lifetime requires log(); pint falls back to magnitudes.
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "annuity_factor": af,
            "wacc": self._PARAMS["wacc"],
        }
        result = equation_registry.calculate("lifetime", params)
        assert result.magnitude == pytest.approx(20.0, rel=1e-4)

    def test_backward_wacc_no_analytical_solution(self) -> None:
        """Test that solving annuity_factor backward for wacc raises NotImplementedError since no closed-form solution exists."""
        # WACC appears in a transcendental position (both linearly and as an
        # exponent base), so SymPy cannot find a closed-form solution and does not support
        # this type of equation
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "annuity_factor": af,
            "lifetime": self._PARAMS["lifetime"],
        }
        with pytest.raises(NotImplementedError):
            equation_registry.calculate("wacc", params, equation_name="annuity_factor")

    def test_eac_via_annuity_factor_matches_direct_formula(self) -> None:
        """Test that computing eac via the annuity_factor formula matches the direct eac_annuity formula."""
        af = equation_registry.calculate("annuity_factor", self._PARAMS)
        params = {
            "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "annuity_factor": af,
        }
        eac_via_af = equation_registry.calculate(
            "eac", params, equation_name="eac_via_annuity_factor"
        )
        assert eac_via_af.magnitude == pytest.approx(_EAC_ANNUITY_EXPECTED, rel=1e-6)


# ---------------------------------------------------------------------------
# Total investment cost
# ---------------------------------------------------------------------------


class TestTotalInvestment:
    """Test suite for the total_investment_cost formula (forward and backward)."""

    _SIC = Parameter(magnitude=800.0, units="USD_2020/kW")
    _CAP = Parameter(magnitude=100.0, units="kW")
    _TOTAL_EXPECTED = 80_000.0

    def test_forward_total(self) -> None:
        """Test that total_investment_cost computes the expected forward value from specific investment and capacity."""
        params = {"specific_investment": self._SIC, "capacity": self._CAP}
        result = equation_registry.calculate("total_investment_cost", params)
        assert result.magnitude == pytest.approx(self._TOTAL_EXPECTED)
        # sic [USD/kW] * capacity [kW] → pint cancels kW, gives currency only
        assert result.units == "USD_2020"

    def test_backward_specific_investment(self) -> None:
        """Test that total_investment_cost can be solved backward for specific_investment given total cost and capacity."""
        params = {
            "total_investment_cost": Parameter(
                magnitude=self._TOTAL_EXPECTED, units="USD_2020"
            ),
            "capacity": self._CAP,
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(800.0)
        assert result.units is not None
        assert "USD_2020" in result.units

    def test_backward_capacity(self) -> None:
        """Test that total_investment_cost can be solved backward for capacity given total cost and specific investment."""
        params = {
            "total_investment_cost": Parameter(
                magnitude=self._TOTAL_EXPECTED, units="USD_2020"
            ),
            "specific_investment": self._SIC,
        }
        result = equation_registry.calculate("capacity", params)
        assert result.magnitude == pytest.approx(100.0)
        assert result.units is not None
        assert "kilowatt" in result.units


# ---------------------------------------------------------------------------
# Fixed O&M cost
# ---------------------------------------------------------------------------


class TestFixedOm:
    """Test suite for the fixed_om formula (forward and backward)."""

    _SIC = Parameter(magnitude=1000.0, units="USD_2020/kW")
    _FRACTION = Parameter(magnitude=0.03, units="dimensionless")
    _FOM_EXPECTED = 30.0

    def test_forward_fixed_om(self) -> None:
        """Test that fixed_om computes the expected forward value from specific investment and fixed O&M fraction."""
        params = {
            "specific_investment": self._SIC,
            "fixed_om_fraction": self._FRACTION,
        }
        result = equation_registry.calculate("fixed_om", params)
        assert result.magnitude == pytest.approx(self._FOM_EXPECTED)
        assert result.units is not None
        assert "USD_2020" in result.units

    def test_backward_fraction(self) -> None:
        """Test that fixed_om can be solved backward for fixed_om_fraction given fixed_om and specific investment."""
        params = {
            "fixed_om": Parameter(
                magnitude=self._FOM_EXPECTED, units="USD_2020/kW/year"
            ),
            "specific_investment": self._SIC,
        }
        result = equation_registry.calculate("fixed_om_fraction", params)
        assert result.magnitude == pytest.approx(0.03)

    def test_backward_specific_investment(self) -> None:
        """Test that fixed_om can be solved backward for specific_investment given fixed_om and fixed_om_fraction."""
        params = {
            "fixed_om": Parameter(
                magnitude=self._FOM_EXPECTED, units="USD_2020/kW/year"
            ),
            "fixed_om_fraction": self._FRACTION,
        }
        result = equation_registry.calculate("specific_investment", params)
        assert result.magnitude == pytest.approx(1000.0)


# ---------------------------------------------------------------------------
# Round-trip efficiency
# ---------------------------------------------------------------------------


class TestRoundtripEfficiency:
    """Test suite for the roundtrip_efficiency formula (forward and backward)."""

    _CE = Parameter(magnitude=0.95, units="dimensionless")
    _DE = Parameter(magnitude=0.90, units="dimensionless")
    _RT_EXPECTED = 0.855

    def test_forward_roundtrip(self) -> None:
        """Test that roundtrip_efficiency computes the expected forward value from charge and discharge efficiency."""
        params = {"charge_efficiency": self._CE, "discharge_efficiency": self._DE}
        result = equation_registry.calculate("roundtrip_efficiency", params)
        assert result.magnitude == pytest.approx(self._RT_EXPECTED)
        assert result.units == "dimensionless"

    def test_backward_charge_efficiency(self) -> None:
        """Test that roundtrip_efficiency can be solved backward for charge_efficiency given roundtrip and discharge efficiency."""
        params = {
            "roundtrip_efficiency": Parameter(
                magnitude=self._RT_EXPECTED, units="dimensionless"
            ),
            "discharge_efficiency": self._DE,
        }
        result = equation_registry.calculate("charge_efficiency", params)
        assert result.magnitude == pytest.approx(0.95, rel=1e-4)

    def test_backward_discharge_efficiency(self) -> None:
        """Test that roundtrip_efficiency can be solved backward for discharge_efficiency given roundtrip and charge efficiency."""
        params = {
            "roundtrip_efficiency": Parameter(
                magnitude=self._RT_EXPECTED, units="dimensionless"
            ),
            "charge_efficiency": self._CE,
        }
        result = equation_registry.calculate("discharge_efficiency", params)
        assert result.magnitude == pytest.approx(0.90, rel=1e-4)


# ---------------------------------------------------------------------------
# Fuel variable cost
# ---------------------------------------------------------------------------


class TestFuelVariableCost:
    """Test suite for the fuel_variable_cost formula (forward and backward)."""

    _FUEL_COST = Parameter(magnitude=50.0, units="USD_2020/MWh")
    _EFF = Parameter(magnitude=0.5, units="dimensionless")
    _FVC_EXPECTED = 100.0

    def test_forward_fuel_variable_cost(self) -> None:
        """Test that fuel_variable_cost computes the expected forward value from fuel cost and efficiency."""
        params = {"fuel_cost": self._FUEL_COST, "efficiency": self._EFF}
        result = equation_registry.calculate("fuel_variable_cost", params)
        assert result.magnitude == pytest.approx(self._FVC_EXPECTED)
        assert result.units is not None
        assert "USD_2020" in result.units

    def test_backward_efficiency(self) -> None:
        """Test that fuel_variable_cost can be solved backward for efficiency given fuel_variable_cost and fuel_cost."""
        params = {
            "fuel_variable_cost": Parameter(
                magnitude=self._FVC_EXPECTED, units="USD_2020/MWh"
            ),
            "fuel_cost": self._FUEL_COST,
        }
        result = equation_registry.calculate("efficiency", params)
        assert result.magnitude == pytest.approx(0.5)
        assert result.units == "dimensionless"

    def test_backward_fuel_cost(self) -> None:
        """Test that fuel_variable_cost can be solved backward for fuel_cost given fuel_variable_cost and efficiency."""
        params = {
            "fuel_variable_cost": Parameter(
                magnitude=self._FVC_EXPECTED, units="USD_2020/MWh"
            ),
            "efficiency": self._EFF,
        }
        result = equation_registry.calculate("fuel_cost", params)
        assert result.magnitude == pytest.approx(50.0)
        assert result.units is not None
        assert "USD_2020" in result.units


# ---------------------------------------------------------------------------
# CO₂ cost
# ---------------------------------------------------------------------------


class TestCo2Cost:
    """Test suite for the co2_cost formula (forward and backward)."""

    _CO2_PRICE = Parameter(magnitude=80.0, units="USD_2020/t")
    _CO2_INTENSITY = Parameter(magnitude=0.3, units="t/MWh")
    _CO2_COST_EXPECTED = 24.0

    def test_forward_co2_cost(self) -> None:
        """Test that co2_cost computes the expected forward value from co2 price and intensity."""
        params = {"co2_price": self._CO2_PRICE, "co2_intensity": self._CO2_INTENSITY}
        result = equation_registry.calculate("co2_cost", params)
        assert result.magnitude == pytest.approx(self._CO2_COST_EXPECTED)
        assert result.units is not None
        assert "USD_2020" in result.units

    def test_backward_co2_price(self) -> None:
        """Test that co2_cost can be solved backward for co2_price given co2_cost and co2_intensity."""
        params = {
            "co2_cost": Parameter(
                magnitude=self._CO2_COST_EXPECTED, units="USD_2020/MWh"
            ),
            "co2_intensity": self._CO2_INTENSITY,
        }
        result = equation_registry.calculate("co2_price", params)
        assert result.magnitude == pytest.approx(80.0)
        assert result.units is not None
        assert "USD_2020" in result.units

    def test_backward_co2_intensity(self) -> None:
        """Test that co2_cost can be solved backward for co2_intensity given co2_cost and co2_price."""
        params = {
            "co2_cost": Parameter(
                magnitude=self._CO2_COST_EXPECTED, units="USD_2020/MWh"
            ),
            "co2_price": self._CO2_PRICE,
        }
        result = equation_registry.calculate("co2_intensity", params)
        assert result.magnitude == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# Formula selection
# ---------------------------------------------------------------------------


class TestFormulaSelection:
    """Test suite for equation/formula selection logic in EquationRegistry.calculate."""

    def test_default_formula_chosen_when_not_specified(self) -> None:
        """Test that the default (highest-priority) formula is chosen when no equation name is specified."""
        result = equation_registry.calculate("eac", EAC_ANNUITY_PARAMS)
        assert result.provenance is not None
        assert "formula 'eac_annuity'" in result.provenance[0]

    def test_explicit_equation_name_overrides_default(self) -> None:
        """Test that an explicitly named equation overrides the default formula selection."""
        result = equation_registry.calculate(
            "eac", EAC_SIMPLE_PARAMS, equation_name="eac_simple"
        )
        assert result.provenance is not None
        assert "formula 'eac_simple'" in result.provenance[0]

    def test_fallback_to_applicable_when_default_cannot_apply(self) -> None:
        """Test that calculate falls back to an applicable formula when the default formula's inputs are unavailable."""
        # Only total_investment_cost + lifetime available:
        # eac_annuity is default but requires sic/wacc/lifetime — cannot apply.
        # eac_simple can apply.
        result = equation_registry.calculate("eac", EAC_SIMPLE_PARAMS)
        assert result.provenance is not None
        assert "formula 'eac_simple'" in result.provenance[0]

    def test_unknown_equation_name_raises(self) -> None:
        """Test that calculate raises KeyError when given an unknown equation name."""
        with pytest.raises(KeyError, match="No equation named"):
            equation_registry.calculate(
                "eac", EAC_ANNUITY_PARAMS, equation_name="bogus"
            )

    def test_named_formula_with_missing_params_raises(self) -> None:
        """Test that calculate raises ValueError when a named formula is missing required parameters."""
        with pytest.raises(ValueError, match="missing parameters"):
            equation_registry.calculate(
                "eac",
                {"lifetime": Parameter(magnitude=20.0, units="year")},
                equation_name="eac_annuity",
            )

    def test_no_applicable_formula_raises_with_diagnosis(self) -> None:
        """Test that calculate raises ValueError with a diagnostic message when no formula is applicable."""
        with pytest.raises(ValueError, match="No equation for"):
            equation_registry.calculate(
                "eac",
                {"lifetime": Parameter(magnitude=20.0, units="year")},
            )

    def test_unknown_target_raises(self) -> None:
        """Test that calculate raises ValueError when the target parameter is not registered."""
        with pytest.raises(ValueError, match="No equation registered"):
            equation_registry.calculate("does_not_exist", EAC_ANNUITY_PARAMS)


# ---------------------------------------------------------------------------
# can_calculate
# ---------------------------------------------------------------------------


class TestCanCalculate:
    """Test suite for EquationRegistry.can_calculate."""

    def test_returns_true_when_applicable(self) -> None:
        """Test that can_calculate returns True when the target is computable from the given parameters."""
        assert equation_registry.can_calculate("eac", EAC_ANNUITY_PARAMS) is True

    def test_returns_false_when_inputs_missing(self) -> None:
        """Test that can_calculate returns False when required input parameters are missing."""
        assert (
            equation_registry.can_calculate(
                "eac", {"lifetime": Parameter(magnitude=20.0, units="year")}
            )
            is False
        )

    def test_returns_false_for_unknown_target(self) -> None:
        """Test that can_calculate returns False for a target that has no registered equations."""
        assert (
            equation_registry.can_calculate("unknown_param", EAC_ANNUITY_PARAMS)
            is False
        )


# ---------------------------------------------------------------------------
# Custom registry (isolated from built-in)
# ---------------------------------------------------------------------------


class TestCustomRegistry:
    """Verify users can create an independent registry and register their own formulas."""

    def test_custom_formula_forward(self) -> None:
        """Test that a custom registry can compute a user-registered formula in the forward direction."""
        reg = EquationRegistry()
        reg.register(
            name="ohms_law",
            parameters=["voltage", "current", "resistance"],
            eq_str="voltage - current * resistance",
        )
        params = {
            "current": Parameter(magnitude=2.0, units="ampere"),
            "resistance": Parameter(magnitude=5.0, units="ohm"),
        }
        result = reg.calculate("voltage", params)
        assert result.magnitude == pytest.approx(10.0)
        # pint returns "ampere * ohm" (correct but not simplified to "volt")
        assert result.units is not None

    def test_custom_formula_backward(self) -> None:
        """Test that a custom registry can solve a user-registered formula in the backward direction."""
        reg = EquationRegistry()
        reg.register(
            name="ohms_law",
            parameters=["voltage", "current", "resistance"],
            eq_str="voltage - current * resistance",
        )
        params = {
            "voltage": Parameter(magnitude=10.0, units="volt"),
            "resistance": Parameter(magnitude=5.0, units="ohm"),
        }
        result = reg.calculate("current", params)
        assert result.magnitude == pytest.approx(2.0)

    def test_custom_registry_isolated_from_builtin(self) -> None:
        """Test that a custom EquationRegistry does not have access to the built-in equations."""
        reg = EquationRegistry()
        assert not reg.can_calculate("eac", EAC_ANNUITY_PARAMS)

    def test_parameter_names_with_spaces(self) -> None:
        """Parameter names containing spaces must work end-to-end."""
        reg = EquationRegistry()
        reg.register(
            name="simple_product",
            parameters=["unit cost", "quantity", "total cost"],
            eq_str="total cost - unit cost * quantity",
        )
        params = {
            "unit cost": Parameter(magnitude=800.0, units="USD_2020/kW"),
            "quantity": Parameter(magnitude=100.0, units="kW"),
        }
        result = reg.calculate("total cost", params)
        assert result.magnitude == pytest.approx(80_000.0)
        # pint: USD_2020/kW * kW = USD_2020
        assert result.units == "USD_2020"

        # Backward direction: derive quantity from total cost and unit cost
        params_back = {
            "unit cost": Parameter(magnitude=800.0, units="USD_2020/kW"),
            "total cost": Parameter(magnitude=80_000.0, units="USD_2020"),
        }
        qty = reg.calculate("quantity", params_back)
        assert qty.magnitude == pytest.approx(100.0)
        assert qty.units is not None
        assert "kilowatt" in qty.units


# ---------------------------------------------------------------------------
# list_equations
# ---------------------------------------------------------------------------


class TestListEquations:
    """Test suite for EquationRegistry.list_equations and duplicate registration handling."""

    def test_list_equations_empty_registry(self) -> None:
        """Test that list_equations returns an empty list for a registry with no equations."""
        reg = EquationRegistry()
        assert reg.list_equations() == []

    def test_list_equations_sorted_case_insensitive(self) -> None:
        """Test that list_equations returns entries sorted by name case-insensitively."""
        reg = EquationRegistry()
        reg.register("beta", ["x", "y"], "x - y")
        reg.register("Alpha", ["a", "b"], "a - b", priority=2)
        reg.register("gamma", ["g", "h"], "g - h")

        listed = reg.list_equations()

        assert [entry["name"] for entry in listed] == ["Alpha", "beta", "gamma"]
        assert listed[0] == {
            "name": "Alpha",
            "parameters": ["a", "b"],
            "eq_str": "a - b",
            "priority": 2,
            "description": None,
        }

    def test_list_equations_for_target(self) -> None:
        """Test that list_equations filters and orders equations applicable to a given target by priority."""
        reg = EquationRegistry()
        reg.register("z_from_xy", ["z", "x", "y"], "z - x - y")
        reg.register("z_from_k", ["z", "k"], "z - k", priority=2)
        reg.register("other", ["q", "r"], "q - r")

        listed = reg.list_equations(target="z")

        assert [entry["name"] for entry in listed] == ["z_from_k", "z_from_xy"]

    def test_list_equations_unknown_target_raises(self) -> None:
        """Test that list_equations raises ValueError for an unknown target."""
        reg = EquationRegistry()
        reg.register("z_from_xy", ["z", "x", "y"], "z - x - y")

        with pytest.raises(ValueError, match="No equation registered"):
            reg.list_equations(target="missing_target")

    def test_register_duplicate_equation_name_raises(self) -> None:
        """Test that registering a duplicate equation name with a different definition raises ValueError."""
        reg = EquationRegistry()
        reg.register("dup_name", ["a", "b"], "a - b")

        with pytest.raises(ValueError, match="different definition"):
            reg.register("dup_name", ["x", "y"], "x - y")


class TestEquationYamlLoading:
    """Test suite for loading equations from YAML files into an EquationRegistry."""

    def test_load_from_yaml_single_file(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_yaml loads a single equation definition from a YAML file."""
        yaml_file = tmp_path / "equations.yaml"
        yaml_file.write_text(
            "\n".join(
                [
                    "- name: test_sum",
                    "  parameters: [z, x, y]",
                    "  eq_str: z - x - y",
                    "  priority: 3",
                ]
            ),
            encoding="utf-8",
        )

        reg = EquationRegistry()
        reg.load_from_yaml(yaml_file)

        listed = reg.list_equations()
        assert len(listed) == 1
        assert listed[0]["name"] == "test_sum"
        assert listed[0]["priority"] == 3
        assert listed[0]["description"] is None

    def test_load_from_yaml_multiple_files(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_yaml loads equation definitions from multiple YAML files."""
        file_a = tmp_path / "a.yaml"
        file_b = tmp_path / "b.yaml"
        file_a.write_text(
            """
- name: eq_a
  parameters: [a, b]
  eq_str: a - b
""".strip(),
            encoding="utf-8",
        )
        file_b.write_text(
            """
- name: eq_b
  parameters: [x, y]
  eq_str: x - y
""".strip(),
            encoding="utf-8",
        )

        reg = EquationRegistry()
        reg.load_from_yaml([file_a, file_b])

        assert [item["name"] for item in reg.list_equations()] == ["eq_a", "eq_b"]

    def test_load_from_yaml_conflicting_name_raises(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Test that load_from_yaml raises ValueError when two files define the same equation name differently."""
        file_a = tmp_path / "a.yaml"
        file_b = tmp_path / "b.yaml"
        file_a.write_text(
            """
- name: same
  parameters: [a, b]
  eq_str: a - b
""".strip(),
            encoding="utf-8",
        )
        file_b.write_text(
            """
- name: same
  parameters: [x, y]
  eq_str: x - y
""".strip(),
            encoding="utf-8",
        )

        reg = EquationRegistry()
        reg.load_from_yaml(file_a)

        with pytest.raises(ValueError, match="different definition"):
            reg.load_from_yaml(file_b)

    def test_load_from_yaml_overwrite_replaces(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_yaml with overwrite=True replaces an existing equation definition."""
        file_a = tmp_path / "a.yaml"
        file_b = tmp_path / "b.yaml"
        file_a.write_text(
            """
- name: same
  parameters: [a, b]
  eq_str: a - b
""".strip(),
            encoding="utf-8",
        )
        file_b.write_text(
            "\n".join(
                [
                    "- name: same",
                    "  parameters: [z, x, y]",
                    "  eq_str: z - x - y",
                    "  priority: 4",
                ]
            ),
            encoding="utf-8",
        )

        reg = EquationRegistry()
        reg.load_from_yaml(file_a)
        reg.load_from_yaml(file_b, overwrite=True)

        listed = reg.list_equations()
        assert len(listed) == 1
        assert listed[0]["name"] == "same"
        assert listed[0]["parameters"] == ["z", "x", "y"]
        assert listed[0]["priority"] == 4

    def test_from_yaml_factory(self, tmp_path: pathlib.Path) -> None:
        """Test that EquationRegistry.from_yaml creates a registry populated from a YAML file."""
        yaml_file = tmp_path / "factory.yaml"
        yaml_file.write_text(
            """
- name: factory_eq
  parameters: [a, b]
  eq_str: a - b
""".strip(),
            encoding="utf-8",
        )

        reg = EquationRegistry.from_yaml(yaml_file)
        assert [entry["name"] for entry in reg.list_equations()] == ["factory_eq"]

    def test_register_with_description(self) -> None:
        """Test that register stores and exposes an equation's description."""
        reg = EquationRegistry()
        reg.register(
            name="described_eq",
            parameters=["a", "b"],
            eq_str="a - b",
            description="Arbitrary context",
        )

        listed = reg.list_equations()
        assert listed[0]["name"] == "described_eq"
        assert listed[0]["description"] == "Arbitrary context"

    def test_load_from_yaml_description(self, tmp_path: pathlib.Path) -> None:
        """Test that load_from_yaml preserves an equation's description field."""
        yaml_file = tmp_path / "described.yaml"
        yaml_file.write_text(
            "\n".join(
                [
                    "- name: with_description",
                    "  parameters: [a, b]",
                    "  eq_str: a - b",
                    "  description: free-text details",
                ]
            ),
            encoding="utf-8",
        )

        reg = EquationRegistry.from_yaml(yaml_file)
        listed = reg.list_equations()
        assert listed[0]["name"] == "with_description"
        assert listed[0]["description"] == "free-text details"


# ---------------------------------------------------------------------------
# Technology.calculate_parameters integration
# ---------------------------------------------------------------------------


class TestTechnologyCalculateParameters:
    """Test suite for Technology.calculate_parameters."""

    def _tech(self, **extra: Parameter) -> Technology:
        params = {**EAC_ANNUITY_PARAMS, **extra}
        return Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=params,
        )

    def test_explicit_target_calculated(self) -> None:
        """Test that calculate_parameters computes an explicitly requested target."""
        result = self._tech().calculate_parameters(targets=["eac"])
        assert "eac" in result.parameters
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-6
        )

    def test_returns_new_instance_original_unchanged(self) -> None:
        """Test that calculate_parameters returns a new Technology instance and leaves the original unchanged."""
        tech = self._tech()
        _ = tech.calculate_parameters(targets=["eac"])
        assert "eac" not in tech.parameters

    def test_auto_discovery_derives_all_possible_params(self) -> None:
        """Test that calculate_parameters auto-discovers and derives all possible parameters when no targets are given."""
        result = self._tech().calculate_parameters()
        assert "eac" in result.parameters

    def test_already_present_params_not_overwritten(self) -> None:
        """Test that calculate_parameters does not overwrite a parameter that is already present."""
        sentinel = Parameter(magnitude=999.0, units="USD_2020/kW/year")
        result = self._tech(eac=sentinel).calculate_parameters()
        assert result.parameters["eac"].magnitude == pytest.approx(999.0)

    def test_equation_names_dict_selects_formula(self) -> None:
        """Test that calculate_parameters uses the equation_names mapping to select a specific formula."""
        tech = Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=EAC_SIMPLE_PARAMS,
        )
        result = tech.calculate_parameters(
            targets=["eac"], equation_names={"eac": "eac_simple"}
        )
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_SIMPLE_EXPECTED, rel=1e-6
        )

    def test_unrelated_currency_mismatch_is_ignored(self) -> None:
        """Test that calculate_parameters ignores a currency-year mismatch on a parameter not required by the selected equation."""
        params = {
            "specific_investment": Parameter(magnitude=1000.0, units="USD_2020/kW"),
            "wacc": Parameter(magnitude=0.07, units="dimensionless"),
            "lifetime": Parameter(magnitude=20.0, units="year"),
            # Different currency year on a parameter that is not required by
            # the selected equation and should therefore be ignored.
            "total_investment_cost": Parameter(magnitude=2000.0, units="USD_2022/kW"),
        }
        tech = Technology(
            name="electrolyzer",
            detailed_technology="PEM",
            case="base",
            region="DEU",
            year=2030,
            parameters=params,
        )
        result = tech.calculate_parameters(
            targets=["eac"], equation_names={"eac": "eac_annuity"}
        )
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-6
        )

    def test_chained_calculation(self) -> None:
        """Derive annuity_factor first, then eac — both in a single call."""
        result = self._tech().calculate_parameters()
        assert result.parameters["eac"].magnitude == pytest.approx(
            _EAC_ANNUITY_EXPECTED, rel=1e-4
        )
