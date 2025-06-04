import pytest
from server.APP import Battery


def test_charge_respects_capacity_limit():
    battery = Battery(max_capacity=1000, discharge_multiplier=100, initial_charge=900)
    charged = battery.charge(amount=200, duration=1)
    assert charged == 100
    assert battery.charge_value == 1000

def test_charge_respects_rate_limit():
    battery = Battery(max_capacity=1000, discharge_multiplier=50, initial_charge=0)
    charged = battery.charge(amount=1000, duration=1)
    assert charged == 50  # rate limit 50 per hour
    assert battery.charge_value == 50

def test_discharge_respects_capacity():
    battery = Battery(max_capacity=1000, discharge_multiplier=100, initial_charge=100)
    discharged = battery.discharge(amount=200, duration=1)
    assert discharged == 100
    assert battery.charge_value == 0

def test_discharge_respects_rate_limit():
    battery = Battery(max_capacity=1000, discharge_multiplier=100, initial_charge=1000)
    discharged = battery.discharge(amount=300, duration=1)
    assert discharged == 100  # rate limit 100 per hour
    assert battery.charge_value == 900
