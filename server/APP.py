from flask import Flask, request, jsonify
import itertools
import logging

# Initialize Flask app
app = Flask(__name__)

class Battery:
    def __init__(self, max_capacity, discharge_multiplier, initial_charge=None):
        self.max_capacity = max_capacity
        self.charge_value = initial_charge if initial_charge is not None else max_capacity
        self.max_charge_discharge_value = (max_capacity / 1000) * discharge_multiplier

    def charge(self, amount, duration):
        # Adjust charge calculation to consider max charge over the entire duration
        max_charge_possible = self.max_charge_discharge_value * duration
        charge_amount = min(amount, self.max_capacity - self.charge_value, max_charge_possible)
        self.charge_value += charge_amount
        return charge_amount

    def discharge(self, amount, duration):
        # Adjust discharge calculation to consider max discharge over the entire duration
        max_discharge_possible = self.max_charge_discharge_value * duration
        discharge_amount = min(amount, self.charge_value, max_discharge_possible)
        self.charge_value -= discharge_amount
        return discharge_amount

class SolarPanel:
    def __init__(self, generation_profile, cells):
        self.generation_profile = generation_profile  # Dictionary of months: generation parameters (start, end, generation_per_cell)
        self.cells = cells  # Number of PV cells

    def generate(self, time_block, duration, month):
        if month in self.generation_profile:
            generation_start, generation_end, generation_per_cell = self.generation_profile[month]
            if generation_start <= time_block < generation_end:
                return self.cells * generation_per_cell * 1000 * duration  # Convert kW to W and multiply by duration in hours to get Wh
        return 0

class Load:
    def __init__(self, load_profile):
        self.load_profile = load_profile  # Dictionary of time block: load_value

    def get_load(self, time_block, duration):
        return self.load_profile.get(time_block, 0) * duration  # Convert load in Watts to energy in Wh over the given duration

class EnergyBlock:
    def __init__(self, time_block, duration, load, solar_panel, battery, month):
        self.time_block = time_block
        self.duration = duration  # Duration of the time block in hours
        self.load = load.get_load(time_block, duration)
        self.generated = solar_panel.generate(time_block, duration, month)
        self.battery = battery

        self.total_used_energy = 0
        self.injected_energy = 0
        self.taken_energy = 0
        self.new_charge = 0

    def calculate(self):
        # Check if generation exceeds load
        if self.generated > self.load:
            surplus = self.generated - self.load
            charged = self.battery.charge(surplus, self.duration)
            self.injected_energy = surplus - charged
            self.total_used_energy = self.load  # Total used is equal to load in this case
            self.new_charge = self.battery.charge_value
        else:
            deficit = self.load - self.generated
            discharged = self.battery.discharge(deficit, self.duration)
            self.taken_energy = deficit - discharged
            self.total_used_energy = self.load  # Total used should reflect the load entirely
            self.new_charge = self.battery.charge_value

class Day:
    def __init__(self, load_profile, generation_profile, cells, battery, month):
        self.load_profile = load_profile
        self.generation_profile = generation_profile
        self.cells = cells
        self.battery = battery
        self.month = month
        self.blocks = []

        time_blocks = sorted(load_profile.keys())
        for i in range(len(time_blocks) - 1):
            time_block = float(time_blocks[i])  # Convert to float
            next_time_block = float(time_blocks[i + 1])  # Convert to float
            duration = next_time_block - time_block  # Duration in hours between time blocks
            load = Load(load_profile)
            solar_panel = SolarPanel(generation_profile, cells)
            block = EnergyBlock(time_block, duration, load, solar_panel, battery, month)
            block.calculate()
            self.blocks.append(block)

        # Add the final block from the last time block to the end of the day (24:00)
        final_time_block = float(time_blocks[-1])  # Convert to float
        final_duration = 24 - final_time_block  # Duration from the last time block to midnight
        load = Load(load_profile)
        solar_panel = SolarPanel(generation_profile, cells)
        final_block = EnergyBlock(final_time_block, final_duration, load, solar_panel, battery, month)
        final_block.calculate()
        self.blocks.append(final_block)

    def summary(self):
        total_injected = sum(block.injected_energy for block in self.blocks)
        total_taken = sum(block.taken_energy for block in self.blocks)
        return total_injected, total_taken

class Week:
    def __init__(self, weekday_load_profile, weekend_load_profile, generation_profile, cells, battery, month):
        self.days = []
        for day in range(7):
            if day < 5:  # Weekdays
                load_profile = weekday_load_profile
            else:  # Weekend
                load_profile = weekend_load_profile
            day_instance = Day(load_profile, generation_profile, cells, battery, month)
            self.days.append(day_instance)

    def summary(self):
        total_week_injected = 0
        total_week_taken = 0
        for day in self.days:
            injected, taken = day.summary()
            total_week_injected += injected
            total_week_taken += taken
        return total_week_injected, total_week_taken

class InvestmentCalculator:
    def __init__(self, panel_cost, battery_cost_per_kwh, cost_taken_energy, income_injected_energy):
        self.panel_cost = panel_cost
        self.battery_cost_per_kwh = battery_cost_per_kwh
        self.cost_taken_energy = cost_taken_energy
        self.income_injected_energy = income_injected_energy

    def calculate_cost(self, cells, battery_capacity, week_injected, week_taken):
        # Calculate investment cost for PV panels and battery
        investment_cost = (cells * self.panel_cost) + (battery_capacity / 1000 * self.battery_cost_per_kwh)

        # Calculate operational cost for energy interactions with the grid
        operational_cost = (week_taken / 1000 * self.cost_taken_energy) + (week_injected / 1000 * self.income_injected_energy)

        return investment_cost, operational_cost

def find_optimal_configuration(weekday_load_profile, weekend_load_profile, generation_profile, months, panel_cost, battery_cost_per_kwh, cost_taken_energy, income_injected_energy, panel_range, battery_range, goal_type, target_yearly_cost=None, investment_weight=0.5, discharge_multiplier=300, max_investment_cost=None, use_max_investment_cost=False):
    best_configuration = None

    lowest_cost = float('inf')
    lowest_operational_cost = float('inf')
    closest_to_zero_cost = float('inf')
    most_self_sufficient_value = float('inf')
    closest_to_target_cost = float('inf')
    calculator = InvestmentCalculator(panel_cost, battery_cost_per_kwh, cost_taken_energy, income_injected_energy)

    configuration_list = itertools.product(panel_range, battery_range)

    for cells, battery_capacity in configuration_list:
        total_yearly_cost = 0
        total_cost = 0
        total_yearly_cost_without_battery = 0
        total_yearly_cost_without_panels = 0
        total_investment_cost = 0
        self_sufficiency = 0
        total_energy_taken_with_battery = 0
        total_energy_taken_without_battery = 0
        total_energy_injected_with_battery = 0
        total_energy_injected_without_battery = 0

        for month in months:
            battery = Battery(max_capacity=battery_capacity, discharge_multiplier=discharge_multiplier, initial_charge=battery_capacity)
            week = Week(weekday_load_profile, weekend_load_profile, generation_profile, cells, battery, month)
            noBatteryWeek = Week(weekday_load_profile, weekend_load_profile, generation_profile, cells, Battery(0, 0), month)
            noSolarWeek = Week(weekday_load_profile, weekend_load_profile, generation_profile, 0, Battery(0, 0), month)
            total_week_injected, total_week_taken = week.summary()
            total_week_injected_noBattery, total_week_taken_noBattery = noBatteryWeek.summary()
            total_week_injected_noSolar, total_week_taken_noSolar = noSolarWeek.summary()

            investment_cost, operational_cost = calculator.calculate_cost(cells, battery_capacity, total_week_injected, total_week_taken)
            total_investment_cost = investment_cost
            total_yearly_cost += operational_cost * 52

            operational_cost_without_battery = (total_week_taken_noBattery / 1000 * cost_taken_energy) + (total_week_injected_noBattery / 1000 * income_injected_energy)
            total_yearly_cost_without_battery += operational_cost_without_battery * 52

            operational_cost_without_panels = (total_week_taken_noSolar / 1000 * cost_taken_energy) * 52
            total_yearly_cost_without_panels += operational_cost_without_panels

            total_energy_taken_with_battery += total_week_taken
            total_energy_taken_without_battery += total_week_taken_noBattery
            total_energy_injected_with_battery += total_week_injected
            total_energy_injected_without_battery += total_week_injected_noBattery

        total_cost = total_investment_cost + total_yearly_cost

        if use_max_investment_cost and total_investment_cost > max_investment_cost:
            continue

        if total_energy_taken_with_battery + total_week_injected > 0:
            self_sufficiency_with_battery = 10 - (total_energy_taken_with_battery / (total_energy_taken_with_battery + total_week_injected)) * 10
        else:
            self_sufficiency_with_battery = 10

        if total_energy_taken_without_battery + total_week_injected_noBattery > 0:
            self_sufficiency_without_battery = 10 - (total_energy_taken_without_battery / (total_energy_taken_without_battery + total_week_injected_noBattery)) * 10
        else:
            self_sufficiency_without_battery = 10

        weighted_score = investment_weight * total_investment_cost + (1 - investment_weight) * total_yearly_cost

        yearly_savings = total_yearly_cost_without_panels - total_yearly_cost
        payback_period_days = total_investment_cost / (yearly_savings / 365)
        payback_period = payback_period_days / 365

        match goal_type:
            case 'most_self_sufficient':
                if (total_energy_taken_with_battery < most_self_sufficient_value or 
                    (total_energy_taken_with_battery == most_self_sufficient_value and (best_configuration is None or total_investment_cost < best_configuration[6]))):
                    most_self_sufficient_value = total_energy_taken_with_battery
                    best_configuration = (cells, battery_capacity, total_cost, total_yearly_cost, total_yearly_cost_without_battery, total_yearly_cost_without_panels, total_investment_cost, total_energy_taken_with_battery, total_energy_taken_without_battery, self_sufficiency_with_battery, self_sufficiency_without_battery, total_energy_injected_with_battery, total_energy_injected_without_battery)

            case 'target_cost':
                if target_yearly_cost is not None:
                    if total_yearly_cost <= target_yearly_cost:
                        # If we are within the target yearly cost, prioritize a lower investment cost
                        if (
                            best_configuration is None
                            or total_investment_cost < best_configuration[6]
                            or (
                                total_investment_cost == best_configuration[6]
                                and total_yearly_cost < best_configuration[3]
                            )
                        ):
                            closest_to_target_cost = total_investment_cost
                            best_configuration = (
                                cells,
                                battery_capacity,
                                total_cost,
                                total_yearly_cost,
                                total_yearly_cost_without_battery,
                                total_yearly_cost_without_panels,
                                total_investment_cost,
                                total_energy_taken_with_battery,
                                total_energy_taken_without_battery,
                                self_sufficiency_with_battery,
                                self_sufficiency_without_battery,
                                total_energy_injected_with_battery,
                                total_energy_injected_without_battery,
                            )
                    else:
                        # If we exceed the target yearly cost, find the configuration that gets as close as possible
                        if (
                            best_configuration is None
                            or total_yearly_cost < best_configuration[3]
                            or (
                                total_yearly_cost == best_configuration[3]
                                and total_investment_cost < best_configuration[6]
                            )
                        ):
                            closest_to_target_cost = total_investment_cost
                            best_configuration = (
                                cells,
                                battery_capacity,
                                total_cost,
                                total_yearly_cost,
                                total_yearly_cost_without_battery,
                                total_yearly_cost_without_panels,
                                total_investment_cost,
                                total_energy_taken_with_battery,
                                total_energy_taken_without_battery,
                                self_sufficiency_with_battery,
                                self_sufficiency_without_battery,
                                total_energy_injected_with_battery,
                                total_energy_injected_without_battery,
                            )

    return best_configuration

@app.route('/ngrok-url', methods=['GET', 'POST'])
def handle_ngrok_url():
    global ngrok_url
    if request.get == 'POST':
        data = request.get_json()
        ngrok_url = data.get('ngrok_url')
        return jsonify({'message': 'ngrok URL set successfully'}), 200
    else:
        return jsonify({'ngrok_url': ngrok_url})

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()

        # Extracting parameters from the request and converting to appropriate types
        weekday_load_profile = {float(k): float(v) for k, v in data['weekday_load_profile'].items()}
        weekend_load_profile = {float(k): float(v) for k, v in data['weekend_load_profile'].items()}
        generation_profile = {k: (float(v[0]), float(v[1]), float(v[2])) for k, v in data['generation_profile'].items()}
        months = data['months']
        panel_cost = float(data['panel_cost'])
        battery_cost_per_kwh = float(data['battery_cost_per_kwh'])
        cost_taken_energy = float(data['cost_taken_energy'])
        income_injected_energy = float(data['income_injected_energy'])
        panel_range = [int(x) for x in data['panel_range']]
        battery_range = [int(x) for x in data['battery_range']]
        goal_type = data['goal']
        target_yearly_cost = float(data['target_yearly_cost']) if data['target_yearly_cost'] is not None else None
        discharge_multiplier = int(data['discharge_multiplier'])
        max_investment_cost = float(data['max_investment_cost']) if data['max_investment_cost'] is not None else None
        use_max_investment_cost = data['use_max_investment_cost']

        logging.debug(f"Received data: {data}")

        # Calculate the optimal configuration
        best_configuration = find_optimal_configuration(
            weekday_load_profile,
            weekend_load_profile,
            generation_profile,
            months,
            panel_cost,
            battery_cost_per_kwh,
            cost_taken_energy,
            income_injected_energy,
            panel_range,
            battery_range,
            goal_type,
            target_yearly_cost,
            investment_weight=0.5,  # Ensure this parameter is passed
            discharge_multiplier=discharge_multiplier,
            max_investment_cost=max_investment_cost,
            use_max_investment_cost=use_max_investment_cost
        )

        logging.debug(f"Best configuration: {best_configuration}")

        yearly_savings = best_configuration[5] - best_configuration[3]
        payback_period_days = best_configuration[6] / (yearly_savings / 365)
        years = int(payback_period_days // 365)
        months = int((payback_period_days % 365) // 30)
        days = int((payback_period_days % 365) % 30)
        payback_period = f"{years} years, {months} months, and {days} days"

        # Return the calculated configuration
        return jsonify({
            'panels': best_configuration[0],
            'battery_capacity': best_configuration[1],
            'yearly_cost': best_configuration[3],
            'yearly_cost_without_battery': best_configuration[4],
            'yearly_cost_without_panels_and_battery': best_configuration[5],
            'total_investment_cost': best_configuration[6],
            'energy_taken_with_battery': best_configuration[7],
            'energy_taken_without_battery': best_configuration[8],
            'self_sufficiency_with_battery': best_configuration[9],
            'self_sufficiency_without_battery': best_configuration[10],
            'total_energy_injected_with_battery': best_configuration[11],
            'total_energy_injected_without_battery': best_configuration[12],
            'yearly_savings': yearly_savings,
            'payback_period': payback_period
        })
    except Exception as e:
        logging.exception("Exception occurred in /calculate endpoint")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    try:
        app.run(host='0.0.0.0', port=5001)
    except Exception as e:
        logging.exception("Exception occurred while starting the server")