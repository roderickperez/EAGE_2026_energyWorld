from mcp.server.fastmcp import FastMCP
import requests
import json

# Create the MCP Server
mcp = FastMCP("EnergyWorldAdvisor")

# The base URL for the PyGame internal API
GAME_API_URL = "http://127.0.0.1:8080"

@mcp.tool()
def get_city_diagnostics() -> str:
    """
    Retrieves the current diagnostic metrics of the city, including population, 
    energy production, demands, and economic balance.
    """
    try:
        response = requests.get(f"{GAME_API_URL}/api/metrics")
        if response.status_code != 200:
            return "Error: Could not retrieve metrics from game."
        
        data = response.json()
        production = data.get("production", {})
        demands = data.get("demands", {})
        
        summary = (
            f"--- CITY STATUS ---\n"
            f"Population: {data.get('population', 0)}\n"
            f"Balance: ${data.get('balance', 0):,}\n\n"
            f"--- ENERGY PRODUCTION ---\n"
            f"Solar: {production.get('solar', 0):.1f} kW\n"
            f"Wind: {production.get('wind', 0):.1f} kW\n"
            f"Coal: {production.get('coal', 0):.1f} kW\n\n"
            f"--- ENERGY DEMANDS ---\n"
            f"Residential Need: {demands.get('res', 0)} kW\n"
            f"Business Requirement: {demands.get('bus', 0)} kW\n"
            f"Industrial Load: {demands.get('ind', 0)} kW\n"
        )
        return summary
    except Exception as e:
        return f"Connection Failed: {e}. Is EnergyWorld running?"

@mcp.tool()
def examine_grid(z: int = 9) -> str:
    """
    Returns the 2D layout of the specified vertical layer (z-axis) of the 10x10x10 city grid.
    z=9 is the surface layer where buildings and assets are placed.
    IDs: 1=Grass, 3=Road, 4=Solar, 5=Wind, 6=Coal, 7/8/9=Zones, 10=House, 11=Office, 12=Factory.
    """
    try:
        response = requests.get(f"{GAME_API_URL}/api/grid")
        if response.status_code != 200:
            return "Error: Could not retrieve grid data."
        
        grid_data = response.json()
        # grid_data is a 10x10x10 list: world_data[z][y][x]
        if z < 0 or z >= len(grid_data):
            return f"Error: Layer z={z} is out of bounds."
            
        layer = grid_data[z]
        grid_str = "Surface Layer (z=9) [10x10]:\n"
        for row in layer:
            grid_str += " ".join(f"{bid:2d}" for bid in row) + "\n"
        
        return grid_str
    except Exception as e:
        return f"Connection Failed: {e}"

@mcp.tool()
def advise_player(message: str) -> str:
    """
    Sends a strategic message or piece of advice to the player's in-game Chat Panel.
    Use this to warn about brownouts or suggest infrastructure placements.
    """
    try:
        payload = {"message": message}
        response = requests.post(f"{GAME_API_URL}/api/advise", json=payload)
        if response.status_code == 200:
            return "Advice sent successfully to the Mayor."
        else:
            return f"Failed to send advice. Status: {response.status_code}"
    except Exception as e:
        return f"Connection Failed: {e}"

if __name__ == "__main__":
    # Start the MCP server
    mcp.run()
