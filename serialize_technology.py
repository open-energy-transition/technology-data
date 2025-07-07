import json

from technologydata.parameter import Parameter
from technologydata.source import Source
from technologydata.technology import Technology
from technologydata.unit_value import UnitValue

# Example data
src = Source(name="example01", url="http://example.com")
param = Parameter(quantity=UnitValue(value=1000, unit="EUR_2020/kW"), sources=[src])
technology = Technology(
    name="Electrolyzer",
    region="EU",
    year=2025,
    parameters={"specific_investment": param},
)

# Serialize to JSON (using Pydantic's .model_dump for nested models)
technology_json = technology.model_dump()

with open("technology.json", "w") as f:
    json.dump(technology_json, f, indent=2)

print("technology.json created.")
