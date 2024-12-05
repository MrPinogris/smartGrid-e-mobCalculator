from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging
import requests  # Import the requests module

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

backend_url = ""

# Default parameters
parameters = {
    'panel_cost': 1250,  # EUR per PV panel
    'battery_cost_per_kwh': 300,  # EUR per kWh
    'cost_taken_energy': 0.30,  # EUR per kWh taken from the grid
    'income_injected_energy': -0.04,  # EUR per kWh injected to the grid
    'panel_range': list(range(1, 11)),  # Number of PV panels to consider
    'battery_range': list(range(1000, 21000, 1000)),  # Battery capacities to consider in Wh (20 kWh to 21 kWh)
    'goals': ['most_self_sufficient', 'target_cost'],  # Removed 'cheapest' and 'fastest_ROI'
    'generation_profile': {
        'April-September': (6.5, 21, 0.275),  # (generation_start, generation_end, generation_per_cell)
        'October-March': (8.5, 18.5, 0.175)
    },
    'weekday_load_profile': {0: 300, 6.5: 500, 9: 400, 18: 600, 23: 300},
    'weekend_load_profile': {0: 300, 8: 400, 17: 600, 23: 300},
    'goal': 'most_self_sufficient',
    'discharge_multiplier': 300,
    'max_investment_cost': 10000,  # New parameter
    'use_max_investment_cost': False  # New flag
}

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    return render_template('index.html', parameters=parameters)

@app.route('/backend_url', methods=['POST'])
def set_backend_url():
    global backend_url
    data = request.get_json()
    backend_url = data.get('backend_url')
    app.logger.debug(f"Received backend URL: {backend_url}")
    return jsonify({'message': 'Backend URL set successfully'}), 200

@app.route('/backend_url', methods=['GET'])
def get_backend_url():
    global backend_url
    app.logger.debug(f"Returning backend URL: {backend_url}")
    return jsonify({'backend_url': backend_url})

@app.route('/update_parameters', methods=['POST'])
def update_parameters():
    print("Updating parameters")
    try:
        data = request.get_json()

        include_battery = data['include_battery']
        include_solar = data['include_solar']
        use_max_investment_cost = data['use_max_investment_cost']

        new_parameters = {
            'panel_cost': float(data['panel_cost']),
            'battery_cost_per_kwh': float(data['battery_cost_per_kwh']),
            'cost_taken_energy': float(data['cost_taken_energy']),
            'income_injected_energy': float(data['income_injected_energy']),
            'weekday_load_profile': {
                float(data['weekday_time_1']): float(data['weekday_load_1']),
                float(data['weekday_time_2']): float(data['weekday_load_2']),
                float(data['weekday_time_3']): float(data['weekday_load_3']),
                float(data['weekday_time_4']): float(data['weekday_load_4']),
                float(data['weekday_time_5']): float(data['weekday_load_5'])
            },
            'weekend_load_profile': {
                float(data['weekend_time_1']): float(data['weekend_load_1']),
                float(data['weekend_time_2']): float(data['weekend_load_2']),
                float(data['weekend_time_3']): float(data['weekend_load_3']),
                float(data['weekend_time_4']): float(data['weekend_load_4'])
            },
            'generation_profile': {
                'April-September': (float(data['summer_start_time']), float(data['summer_end_time']), float(data['summer_generation'])),
                'October-March': (float(data['winter_start_time']), float(data['winter_end_time']), float(data['winter_generation']))
            },
            'goal': data['goal'],
            'months': ['April-September', 'October-March'],
            'panel_range': list(range(int(data['panel_range_start']), int(data['panel_range_end']) + 1)) if include_solar else [0],
            'battery_range': list(range(int(data['battery_range_start']), int(data['battery_range_end']) + 1000, 1000)) if include_battery else [0],
            'target_yearly_cost': float(data['target_yearly_cost']) if data['goal'] == 'target_cost' else None,
            'discharge_multiplier': int(data['discharge_multiplier']),
            'max_investment_cost': float(data['max_investment_cost']),
            'use_max_investment_cost': use_max_investment_cost
        }

        logging.debug(f"Sending parameters to backend: {new_parameters}")

        response = requests.post(f"{backend_url}/calculate", json=new_parameters)
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Received response from backend: {data}")
            return jsonify(data)
        else:
            logging.error("Failed to calculate optimal configuration")
            return jsonify({"error": "Failed to calculate optimal configuration"}), 500
    except Exception as e:
        logging.exception("Exception occurred in /update_parameters endpoint")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(filename='client.log', level=logging.DEBUG)
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logging.exception("Exception occurred while starting the server")
