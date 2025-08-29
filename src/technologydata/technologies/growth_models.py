# SPDX-FileCopyrightText: 2025 The technology-data authors
#
# SPDX-License-Identifier: MIT
"""Growth models for projecting technology parameters over time."""

import inspect
import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Annotated, Self

import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


class GrowthModel(BaseModel):
    """
    Abstract base for growth models used in projections.

    To implement a new growth model that inherits from this class, the following must be provided:
    1. A mathematical function representing the growth model by implementing the abstract method `function(self, x: float, **parameters) -> float`.
       The parameters of the function (besides `x`) will be automatically detected and used for fitting and projection.
    2. The parameters should be defined as attributes of the class, initialized to `None` if they are to be fitted.
    """

    data_points: Annotated[
        list[tuple[float, float]],
        Field(
            description="Data points (x, y) for fitting the model, where f(x) = y.",
            default=list(),
        ),
    ]

    class Config:
        """Pydantic configuration."""

        # Ensure that assignments to model fields are validated
        validate_assignment = True

    @abstractmethod
    def function(self, x: float, **kwargs: dict[str, float]) -> float:
        """Function that represents the growth model."""  # noqa: D401
        pass

    @property
    def model_parameters(self) -> list[str]:
        """Return the set of model parameters that have been provided (are not None)."""
        return [
            p for p in inspect.signature(self.function).parameters.keys() if p != "x"
        ]

    @property
    def provided_parameters(self) -> list[str]:
        """Return the set of model parameters that have been provided (are not None)."""
        return list(
            self.model_dump(include=self.model_parameters, exclude_none=True).keys()
        )

    @property
    def missing_parameters(self) -> list[str]:
        """Return the set of model parameters that are missing (have not been provided)."""
        return [p for p in self.model_parameters if p not in self.provided_parameters]

    def add_data(self, data_point: tuple[float, float]) -> Self:
        """Add a data point to the model for fitting."""
        self.data_points.append(data_point)
        return self

    def project(
        self,
        to_year: int,
    ) -> float:
        """
        Project using the model to the specified year.

        This function uses the parameters that have been provided for the model either directly or through fitting to data points.

        Parameters
        ----------
        to_year : int
            The year to which to project the values.

        Returns
        -------
        float
            The projected value for the specified year.

        """
        if len(self.missing_parameters) > 0:
            raise ValueError(
                f"Cannot project. The following parameters have not been specified yet and are missing: {self.missing_parameters}."
            )

        return self.function(
            to_year, **self.model_dump(include=self.provided_parameters)
        )

    @classmethod
    def _kwpartial(
        cls, f: Callable[..., float], **fixed_params: dict[str, float]
    ) -> Callable[..., float]:
        """
        Like functools.partial, but for keyword arguments.

        Enables us to wrap a function in a way that is compatible with scipy.optimize.curve_fit,
        which does not play nicely with standard functools.partial.
        For details see: https://stackoverflow.com/questions/79749129/use-curve-fit-with-partial-using-named-parameters-instead-of-positional-para/79749198#79749198

        """
        f_sig = inspect.signature(f)
        positional_params = (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        )
        args = [
            p.name for p in f_sig.parameters.values() if p.kind in positional_params
        ]
        new_args = [
            inspect.Parameter(arg, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            for arg in args
            if arg not in fixed_params
        ]
        new_sig = inspect.Signature(new_args)

        def wrapper(*f_args: float, **f_kwargs: dict[str, float]) -> float:
            bound_args = new_sig.bind(*f_args, **f_kwargs)
            bound_args.apply_defaults()
            return f(**bound_args.arguments, **fixed_params)

        wrapper.__signature__ = new_sig  # type: ignore[attr-defined]
        wrapper.__name__ = f"kwpartial({f.__name__}, {fixed_params})"

        return wrapper

    def fit(self, p0: dict[str, float] | None = None) -> Self:
        """
        Fit the growth model using the parameters and data points provided to the model.

        Parameters
        ----------
        p0 : dict[str, float], optional
            Initial guesses for the missing parameters to be fitted.
            May contain all or a subset of the missing parameters.
            Any parameter not provided will be initialized with a starting guess of 1.0 (scipy's default).

        Returns
        -------
        Self
            The model instance with the fitted parameters set.

        """
        # if all parameters of the model are already fixed, then we cannot fit anything
        if len(self.provided_parameters) == len(self.model_parameters):
            logger.info("All parameters are already fixed, cannot fit anything.")
            return self

        # The number of data points must be at least equal to the number of parameters to fit
        if len(self.data_points) < len(self.missing_parameters):
            raise ValueError(
                f"Not enough data points to fit the model. Need at least {len(self.missing_parameters)}, got {len(self.data_points)}."
            )

        # Fit the model to the data points:
        # build a partial function that includes the already fixed parameters
        func = self._kwpartial(
            self.function,
            **self.model_dump(include=self.provided_parameters, exclude_none=True),
        )

        # p0 optionally allows to provide initial guesses for the parameters to fit
        if p0 is None:
            p0 = {}

        # the dict needs to be transformed into a list with the parameters in the correct order
        # if a parameter is missing from p0, we use 1 as a default initial guess (scipy's default)
        p0_ = [p0.get(param, 1) for param in self.missing_parameters]

        # fit the function to the data points
        xdata, ydata = zip(*self.data_points)
        popt, pcov = curve_fit(f=func, xdata=xdata, ydata=ydata, p0=p0_)

        logger.debug(f"Fitted parameters: {popt}")
        logger.debug(f"Covariance of the parameters: {pcov}")

        # assign the fitted parameters to the model
        for param, value in zip(self.missing_parameters, popt):
            logger.debug(f"Setting parameter {param} to fitted value {value}")
            setattr(self, param, value)

        return self


class LinearGrowth(GrowthModel):
    """Project with linear growth model."""

    m: Annotated[
        float | None,
        Field(description="Annual growth rate for the linear function.", default=None),
    ]
    c: Annotated[
        float | None,
        Field(description="Starting value for the linear function.", default=None),
    ]

    def function(self, x: float, m: float, c: float) -> float:  # type: ignore[override]
        """
        Linear function for the growth model.

        f(x) = m * x + c

        Parameters
        ----------
        x : float
            The input value on which to evaluate the function, e.g. a year '2025'.
        m : float, optional
            The slope of the linear function.
        c : float, optional
            The constant offset of the linear function.

        Returns
        -------
        float
            The result of the linear function evaluation at x.

        """
        return m * x + c


class ExponentialGrowth(GrowthModel):
    """Project with exponential growth model."""

    A: Annotated[
        float | None,
        Field(description="Initial value for the exponential function.", default=None),
    ]
    k: Annotated[
        float | None,
        Field(description="Growth rate for the exponential function.", default=None),
    ]
    x0: Annotated[
        float | None,
        Field(
            description="The reference x-value (e.g., starting year) for the exponential function.",
            default=None,
        ),
    ]

    def function(self, x: float, A: float, k: float, x0: float) -> float:  # type: ignore[override]
        """
        Exponential function for the growth model.

        f(x) = A * exp(k * (x - x0))

        Parameters
        ----------
        x : float
            The input value on which to evaluate the function, e.g. a year '2025'.
        A : float
            The initial value of the exponential function.
        k : float
            The growth rate of the exponential function.
        x0 : float
            The reference x-value (e.g., starting year) for the exponential function.

        Returns
        -------
        float
            The result of the exponential function evaluation at x.

        """
        return float(A * np.exp(k * (x - x0)))


class LogisticGrowth(GrowthModel):
    """Project with a logistic growth model."""

    L: Annotated[
        float | None,
        Field(
            description="Carrying capacity of the logistic function.",
            default=None,
        ),
    ]
    k: Annotated[
        float | None,
        Field(
            description="Growth rate of the logistic function.",
            default=None,
        ),
    ]
    x0: Annotated[
        float | None,
        Field(
            description="The x-value of the sigmoid's midpoint (inflection point/midpoint year).",
            default=None,
        ),
    ]

    def function(self, x: float, L: float, k: float, x0: float) -> float:  # type: ignore[override]
        """
        Logistic function for the growth model.

        f(x) = L / (1 + exp(-k * (x - x0)))

        Parameters
        ----------
        x : float
            The input value on which to evaluate the function, e.g. a year '2025'.
        L : float
            The carrying capacity of the logistic function.
        k : float
            The growth rate of the logistic function.
        x0 : float
            The x-value of the sigmoid's midpoint (inflection point).

        Returns
        -------
        float
            The result of the logistic function evaluation at x.

        """
        return float(L / (1 + np.exp(-k * (x - x0))))


class GompertzGrowth(GrowthModel):
    """Project with a Gompertz growth model."""

    A: Annotated[
        float | None,
        Field(
            description="The upper asymptote (maximum value) of the Gompertz function.",
            default=None,
        ),
    ]
    k: Annotated[
        float | None,
        Field(
            description="The growth rate of the Gompertz function.",
            default=None,
        ),
    ]
    x0: Annotated[
        float | None,
        Field(
            description="The x-value of the inflection point (midpoint year) of the Gompertz function.",
            default=None,
        ),
    ]
    b: Annotated[
        float | None,
        Field(
            description="The displacement along the x-axis of the Gompertz function.",
            default=None,
        ),
    ]

    def function(self, x: float, A: float, k: float, x0: float, b: float) -> float:  # type: ignore[override]
        """
        Gompertz function for the growth model.

        f(x) = A * exp(-b * exp(-k * (x - x0)))

        Parameters
        ----------
        x : float
            The input value on which to evaluate the function, e.g. a year '2025'.
        A : float
            The upper asymptote (maximum value) of the Gompertz function.
        k : float
            The growth rate of the Gompertz function.
        x0 : float
            The x-value of the inflection point (midpoint year) of the Gompertz function.
        b : float
            The displacement along the x-axis of the Gompertz function.

        Returns
        -------
        float
            The result of the Gompertz function evaluation at x.

        """
        return float(A * np.exp(-b * np.exp(-k * (x - x0))))
