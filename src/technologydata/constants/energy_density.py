# SPDX-FileCopyrightText: The technology-data authors
#
# SPDX-License-Identifier: MIT

"""
Energy density parameters for various carriers.

This module defines dictionaries containing energy density parameters
for different fuel carriers, specifically focusing on lower heating value (LHV)
and higher heating value (HHV). Each entry maps a carrier name to a `Parameter`
object that includes magnitude, unit, and carrier type.

Attributes
----------
EnergyDensityLHV : dict[str, Parameter]
    Dictionary mapping carrier names to their lower heating value (LHV)
    parameters.
    - Key: carrier name (e.g., 'hydrogen', 'methane')
    - Value: Parameter object with magnitude, unit, and carrier info.

EnergyDensityHHV : dict[str, Parameter]
    Dictionary mapping carrier names to their higher heating value (HHV)
    parameters.
    - Key: carrier name (e.g., 'hydrogen', 'methane')
    - Value: Parameter object with magnitude, unit, and carrier info.

"""

from technologydata import Parameter, Source, SourceCollection

EnergyDensityLHV: dict[str, Parameter] = dict(
    hydrogen=Parameter(
        magnitude=119.6,
        units="GJ/t",
        carrier="hydrogen",
        # source=  # TODO
    ),
    methane=Parameter(
        magnitude=50.0,
        units="GJ/t",
        carrier="methane",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    natural_gas=Parameter(
        magnitude=47.1,
        units="GJ/t",
        carrier="natural_gas",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    ammonia=Parameter(
        magnitude=18.6,
        units="GJ/t",
        carrier="ammonia",
        sources=SourceCollection(
            sources=[
                Source(
                    title="Computational Thermodynamics",
                    authors="Kyle E. Niemeyer. (2020) computational-thermo v0.1.0 [software]. Zenodo. https://doi.org/10.5281/zenodo.4017943",
                    url="https://github.com/kyleniemeyer/computational-thermo",
                ),
            ],
        ),
    ),
    wood=Parameter(
        magnitude=15.4,
        units="GJ/t",
        carrier="wood",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    # Add more energy densities as needed
)

EnergyDensityHHV: dict[str, Parameter] = dict(
    hydrogen=Parameter(
        magnitude=141.8,
        units="GJ/t",
        carrier="hydrogen",
        # source=  # TODO
    ),
    methane=Parameter(
        magnitude=55.5,
        units="GJ/t",
        carrier="methane",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    natural_gas=Parameter(
        magnitude=52.2,
        units="GJ/t",
        carrier="natural_gas",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    ammonia=Parameter(
        magnitude=22.5,
        units="GJ/t",
        carrier="ammonia",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    wood=Parameter(
        magnitude=16.2,
        units="GJ/t",
        carrier="wood",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    carbon=Parameter(
        magnitude=32.8,
        units="GJ/t",
        carrier="carbon",
        sources=SourceCollection(
            sources=[
                Source(
                    title="The Engineering ToolBox",
                    authors="The Engineering ToolBox (2003). Higher Calorific Values of Common Fuels: Reference & Data. [online] Available at:https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html [Accessed 6 September 2025].",
                    url="https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html",
                ),
            ],
        ),
    ),
    # Add more energy densities as needed
)
