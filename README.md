
# Toll-Based Simulation System

This project is a simulation system designed to simulate vehicle movement and toll-based charging in a predefined road network. It uses Flask for the web interface, SimPy for simulation, and various geospatial libraries for handling and displaying geographic data.

## Features

- Simulates vehicle movement from a start location to an end location.
- Calculates road distance using a network graph.
- Identifies and processes toll zones.
- Displays the road network and toll zones on an interactive map.

## Project Structure

- `app.py`: The main Flask application and simulation logic.
- `templates/`: Directory containing HTML templates.
  - `index.html`: Main page that displays the simulation map.
  - `road_network_And_toll_zones.html`: Page that displays road network and toll zones data.

## Requirements

- Python 3.x
- Flask
- Flask-Caching
- GeoPandas
- Pandas
- Shapely
- Folium
- SimPy
- OSMnx
- NetworkX
- Concurrent.Futures
- os

## Installation

1. Clone the repository:

    git clone https://github.com/Dhanushranga1/toll-based-simulation.git
    cd toll-based-simulation


2. Create and activate a virtual environment (optional but recommended):
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    

3. Install the required dependencies:

## Running the Application

1. Start the Flask app:
    
    python app.py
    

2. Open your web browser and navigate to `http://127.0.0.1:5000/` to see the simulation map.

## Simulation Details

The simulation involves vehicles moving from a start location to an end location while passing through predefined toll zones. The toll amount is calculated based on the distance traveled through these zones. 

## Routes

- `/`: Main route that displays the simulation map.
- `/download`: Route to download the simulation data in GeoJSON format.

## Usage

1. Access the main page to view the interactive map displaying the road network and toll zones.
2. Use the `/download` route to download the current simulation data.

## Contributing

Feel free to fork this repository and contribute by submitting pull requests. Any improvements and suggestions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
