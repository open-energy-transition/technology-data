from technologydata import Parameter

EnergyDensityLHV: dict[str, Parameter] = dict(
    hydrogen=Parameter(
        magnitude=119.6,
        unit="GJ/t",
        carrier="hydrogen",
        # source=  # TODO
    ),
    methane=Parameter(
        magnitude=50.0,
        unit="GJ/t",
        carrier="methane",
        # source=  # TODO
    ),
    # Add more energy densities as needed
)

EnergyDensityHHV: dict[str, Parameter] = dict(
    hydrogen=Parameter(
        magnitude=141.8,
        unit="GJ/t",
        carrier="hydrogen",
        # source=  # TODO
    ),
    methane=Parameter(
        magnitude=55.5,
        unit="GJ/t",
        carrier="methane",
        # source=  # TODO
    ),
    # Add more energy densities as needed
)
