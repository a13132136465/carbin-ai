from langchain_core.tools import tool


@tool
def calculate_carbon_reduction(
    annual_generation_mwh: float,
    grid_emission_factor: float
) -> float:
    """
    Calculate the estimated annual carbon emission reduction
    for a renewable energy project.

    Args:
        annual_generation_mwh:
            Annual renewable electricity generation in MWh.

        grid_emission_factor:
            Grid emission factor in tCO2/MWh.

    Returns:
        Estimated annual carbon emission reduction in tCO2.
    """

    return annual_generation_mwh * grid_emission_factor


print(calculate_carbon_reduction.name)
print(calculate_carbon_reduction.description)
print(calculate_carbon_reduction.args)