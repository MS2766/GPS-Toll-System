from flask import Flask, render_template, send_file
from flask_caching import Cache
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
import folium
import simpy
import osmnx as ox
import networkx as nx
import concurrent.futures
import os

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def run_simulation(vehicle_id, start_location, end_location, toll_zones, rates, accounts, G):
    class Vehicle:
        def __init__(self, env, vehicle_id, start_location, end_location, toll_zones, rates, accounts, G):
            self.env = env
            self.vehicle_id = vehicle_id
            self.start_location = start_location
            self.current_location = start_location
            self.end_location = end_location
            self.toll_zones = toll_zones
            self.rates = rates
            self.accounts = accounts
            self.crossed_zones = set()
            self.total_toll = 0.0
            self.total_distance = 0.0
            self.G = G  # Road network graph
            self.action = env.process(self.run())

        def calculate_road_distance(self):
            start_node = ox.distance.nearest_nodes(self.G, self.start_location.x, self.start_location.y)
            end_node = ox.distance.nearest_nodes(self.G, self.end_location.x, self.end_location.y)
            self.total_distance = nx.shortest_path_length(self.G, start_node, end_node, weight='length')

        def move(self):
            step_size = 0.001  # Reduced step size for higher precision
            while self.current_location.distance(self.end_location) > step_size:
                prev_location = self.current_location
                new_x = self.current_location.x + (self.end_location.x - self.current_location.x) * step_size / self.current_location.distance(self.end_location)
                new_y = self.current_location.y + (self.end_location.y - self.current_location.y) * step_size / self.current_location.distance(self.end_location)
                self.current_location = Point(new_x, new_y)
                self.check_toll_zones(prev_location)
                yield self.env.timeout(0.01)
            self.current_location = self.end_location

        def check_toll_zones(self, prev_location):
            for _, zone in self.toll_zones.iterrows():
                if prev_location.buffer(0.001).intersects(zone.geometry):
                    self.calculate_road_distance()
                    if zone.zone_id not in self.crossed_zones:
                        self.crossed_zones.add(zone.zone_id)

        def run(self):
            while not self.current_location.equals_exact(self.end_location, 0.001):
                yield self.env.process(self.move())
            self.process_payment()

        def process_payment(self):
            self.total_toll = self.total_distance * self.rates
            self.accounts[self.vehicle_id] -= self.total_toll

    env = simpy.Environment()
    vehicle = Vehicle(env, vehicle_id, start_location, end_location, toll_zones, rates, accounts, G)
    env.run(until=100)

    vehicle_data = {
        'vehicle_id': vehicle.vehicle_id,
        'entry point': vehicle.start_location,
        'exit point': vehicle.end_location,
        'crossed_zones': list(vehicle.crossed_zones),
        'total distance': round(vehicle.total_distance / 1000, 2),
        'total_toll': vehicle.total_toll,
        'account_balance': vehicle.accounts[vehicle.vehicle_id],
    }
    return vehicle_data

@cache.cached(timeout=300)
def prepare_simulation():
    road_network = gpd.GeoDataFrame({
        'road_id': [1, 2, 3, 4],
        'geometry': [
            LineString([
                (77.47249734051701, 13.057311536012028),
                (77.4739418482509,  13.056930904868965),
                (77.47442451666745, 13.056948482047458),
                (77.47508762189501, 13.056763921605565),
                (77.47559563361101, 13.056747596644135),
                (77.47688746290746, 13.05710182151551),
                (77.47730212416313, 13.056635736052938),
                (77.47690085826824, 13.054055916031114),
                (77.47665599760786, 13.052118552821883),
                (77.47628292569452, 13.050287567879304),
                (77.47536912206463, 13.044523686811814),
                (77.47539478436559, 13.042154387399776),
                (77.47611790965406, 13.036744993868902),
                (77.47547661989523, 13.029651082626584),
                (77.47554730628895, 13.023372891407181),
                (77.47618197529408, 13.0173627019377),
                (77.47593081655492, 13.013359026660217),
                (77.47461195320281, 13.006684533333498),
                (77.47407761359283, 12.997658400851929),
                (77.47219227011887, 12.98896439645191)
            ]),
            LineString([
                (77.47880993773907, 13.055137922284267),
                (77.47821629937825, 13.055320833309482),
                (77.47779322236094, 13.055225248386666),
                (77.47746054426267, 13.05505455251026),
                (77.47709801930544, 13.054680375648656),
                (77.47690085826824, 13.054055916031114)
            ]),
            LineString([
                (77.47536781949456, 13.043201932046639),
                (77.47574476122185, 13.043129215858327),
                (77.47582313524435, 13.042787449486818),
                (77.47605945283462, 13.042766513508187),
            ]),
            LineString([
                (77.47302238050207, 12.992710856898563),
                (77.47329278144292, 12.992017143148514),
                (77.47366686628436, 12.991652163766275),
                (77.47375088970591, 12.991421165796439),
                (77.47360985039299, 12.991070282395688),
                (77.47305571535811, 12.990704255001114),
                (77.47290971711307, 12.99033416331594),
                (77.4727206644122,  12.98950958292108),
                (77.47274467110745, 12.988997873847191),
                (77.47265164517427, 12.988711316303007)
            ])
        ]
    })

    toll_zones = gpd.GeoDataFrame({
        'zone_id': [1, 2, 3],
        'geometry': [
            LineString([
                (77.4739418482509,  13.056930904868965),
                (77.47442451666745, 13.056948482047458),
                (77.47508762189501, 13.056763921605565),
                (77.47559563361101, 13.056747596644135),
                (77.47688746290746, 13.05710182151551),
                (77.47730212416313, 13.056635736052938),
                (77.47690085826824, 13.054055916031114),
                (77.47665599760786, 13.052118552821883),
                (77.47628292569452, 13.050287567879304),
                (77.47536912206463, 13.044523686811814),
                (77.47539478436559, 13.042154387399776),
                (77.47611790965406, 13.036744993868902),
                (77.47547661989523, 13.029651082626584),
                (77.47554730628895, 13.023372891407181),
                (77.47618197529408, 13.0173627019377),
                (77.47593081655492, 13.013359026660217),
                (77.47461195320281, 13.006684533333498),
                (77.47407761359283, 12.997658400851929),
                (77.47219227011887, 12.98896439645191)
            ]),
            LineString([
                (77.47821629937825, 13.055320833309482),
                (77.47779322236094, 13.055225248386666),
                (77.47746054426267, 13.05505455251026),
                (77.47709801930544, 13.054680375648656),
                (77.47690085826824, 13.054055916031114)
            ]),
            LineString([
                (77.47302238050207, 12.992710856898563),
                (77.47329278144292, 12.992017143148514),
                (77.47366686628436, 12.991652163766275),
                (77.47375088970591, 12.991421165796439),
                (77.47360985039299, 12.991070282395688),
                (77.47305571535811, 12.990704255001114),
                (77.47290971711307, 12.99033416331594),
                (77.4727206644122,  12.98950958292108),
                (77.47274467110745, 12.988997873847191),
                (77.47265164517427, 12.988711316303007)
            ])
        ]
    })

    m = folium.Map(location=[13.05, 77.48], zoom_start=13)  # Adjusted center for better map view
    for _, row in road_network.iterrows():
        folium.PolyLine(locations=[(coord[1], coord[0]) for coord in row.geometry.coords], color='blue', weight=5, popup=f"Road {row.road_id}").add_to(m)
    for _, row in toll_zones.iterrows():
        folium.PolyLine(locations=[(coord[1], coord[0]) for coord in row.geometry.coords], color='red', weight=5, name=f"Zone {row.zone_id}").add_to(m)

    entry_points = [
        (13.056930904868965, 77.4739418482509),
        (13.055320833309482, 77.47821629937825)
    ]
    for entry in entry_points:
        folium.Marker(
            location=entry,
            popup='Entry Point',
            icon=folium.Icon(color='green', icon='play')
        ).add_to(m)

    exit_points = [
        (13.043201932046639, 77.47536781949456)
    ]
    for exit in exit_points:
        folium.Marker(
            location=exit,
            popup='Exit Point',
            icon=folium.Icon(color='red', icon='stop')
        ).add_to(m)

    m.save('templates/road_network_and_toll_zones.html')

    G = ox.graph_from_point((13.025369058991071, 77.47556873116585), dist=6000, network_type='drive')

    return toll_zones, G

@app.route('/')
def index():
    toll_zones, G = prepare_simulation()
    toll_rates = 0.003025
    user_accounts = {i: 100.0 for i in range(1, 7)}
    
    start_locations = [
        Point(77.4739418482509, 13.056930904868965),
        Point(77.4739418482509, 13.056930904868965),
        Point(77.47880993773907, 13.055137922284267),
        Point(77.47880993773907, 13.055137922284267),
        Point(77.47605945283462, 13.042766513508187),
        Point(77.47880993773907, 13.055137922284267)
    ]
    end_locations = [
        Point(77.47265164517427, 12.988711316303007),
        Point(77.47605945283462, 13.042766513508187),
        Point(77.47265164517427, 12.988711316303007),
        Point(77.47605945283462, 13.042766513508187),
        Point(77.47265164517427, 12.988711316303007),
        Point(77.47265164517427, 12.988711316303007)
    ]

    vehicle_data = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_simulation, i+1, start_locations[i], end_locations[i], toll_zones, toll_rates, user_accounts, G) for i in range(6)]
        for future in concurrent.futures.as_completed(futures):
            vehicle_data.append(future.result())

    df = pd.DataFrame(vehicle_data)
    html_table = df.to_html(classes='table table-striped')
    return render_template('index.html', tables=[html_table], titles=df.columns.values)

@app.route('/map')
def map():
    return send_file('templates/road_network_and_toll_zones.html')

if __name__ == '__main__':
    app.run(debug=True)
