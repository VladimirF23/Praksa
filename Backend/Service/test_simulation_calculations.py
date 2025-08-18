#Service/test_simulation_calculations.py
import unittest




from SimulationService import *

class TestSolarSimulationCalculations(unittest.TestCase):

    def setUp(self):
        """
        Postavlja zajednicke podatke za testove.
        Koristimo realisticne (ili granicne) vrednosti za simulaciju.
        """
        self.solar_system_config = {
            "total_panel_wattage_wp": 5000.0,  # 5 kWp sistem
            "inverter_capacity_kw": 4.5,       # 4.5 kW inverter
            "tilt_degrees": 35,                # Nagib panela
            "azimuth_degrees": 180,            # Azimut panela (jug)
            "base_consumption_kw": 0.5         # Bazna potrosnja od 0.5 kW
        }

        self.battery_config = {
            "capacity_kwh": 10.0,              # 10 kWh kapacitet baterije
            "current_charge_percentage": 50.0, # Pocetna napunjenost 50%
            "max_charge_rate_kw": 3.0,         # Maksimalna snaga punjenja 3 kW
            "max_discharge_rate_kw": 4.0,      # Maksimalna snaga praznjenja 4 kW
            "efficiency": 0.9                  # Efikasnost punjenja/praznjenja 90%
        }

        self.iot_devices_data_all_off = [
            {"device_id": 1, "base_consumption_watts": 100, "current_status": "off"},
            {"device_id": 2, "base_consumption_watts": 2000, "current_status": "off"}, # Npr. EV punjac
            {"device_id": 3, "base_consumption_watts": 50, "current_status": "off"},
        ]

        self.iot_devices_data_some_on = [
            {"device_id": 1, "base_consumption_watts": 100, "current_status": "on"},  # Sijalice
            {"device_id": 2, "base_consumption_watts": 2000, "current_status": "off"}, # EV punjac iskljucen
            {"device_id": 3, "base_consumption_watts": 50, "current_status": "on"},   # TV
        ]

        self.iot_devices_data_all_on = [
            {"device_id": 1, "base_consumption_watts": 100, "current_status": "on"},
            {"device_id": 2, "base_consumption_watts": 2000, "current_status": "on"},
            {"device_id": 3, "base_consumption_watts": 50, "current_status": "on"},
        ]

        self.time_step_hours = 1/60.0 # 1 minut vremenski korak

    # --- Testovi za calculate_solar_production ---

    def test_solar_production_sunny_day(self):
        """Testira proizvodnju po suncanom danu sa visokim zracenjem."""
        weather_data = {
            "global_tilted_irradiance_instant": 800.0, # W/m2
            "temperature_2m": 25.0, # °C
            "is_day": 1
        }
        # Ocekivana proizvodnja: (5000 Wp / 1000 W/m2) * 800 W/m2 * 0.90 (system_eff) * 1.0 (temp_eff) / 1000 = 3.6 kW
        # Ograniceno na inverter 4.5 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 3.6, places=2)

    def test_solar_production_cloudy_day(self):
        """Testira proizvodnju po oblacnom danu sa niskim zracenjem."""
        weather_data = {
            "global_tilted_irradiance_instant": 150.0, # W/m2
            "temperature_2m": 15.0, # °C
            "is_day": 1
        }
        # Ocekivana proizvodnja: (5000 / 1000) * 150 * 0.90 * 1.0 / 1000 = 0.675 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 0.675, places=2)

    def test_solar_production_night(self):
        """Testira proizvodnju nocu (is_day = 0)."""
        weather_data = {
            "global_tilted_irradiance_instant": 0.0,
            "temperature_2m": 10.0,
            "is_day": 0
        }
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 0.0, places=2)

    def test_solar_production_inverter_clipping(self):
        """Testira ogranicenje proizvodnje kapacitetom invertera."""
        high_production_config = self.solar_system_config.copy()
        high_production_config["total_panel_wattage_wp"] = 10000.0 # 10 kWp paneli
        high_production_config["inverter_capacity_kw"] = 4.5      # Inverter ostaje 4.5 kW

        weather_data = {
            "global_tilted_irradiance_instant": 1000.0, # W/m2 (pun sunce)
            "temperature_2m": 25.0, # °C
            "is_day": 1
        }
        # Potencijalna proizvodnja: (10000 / 1000) * 1000 * 0.90 * 1.0 / 1000 = 9.0 kW
        # Ali inverter je 4.5 kW, pa bi trebalo da bude 4.5 kW
        production = calculate_solar_production(high_production_config, weather_data)
        self.assertAlmostEqual(production, 4.5, places=2) # Ocekuje se clipping na 4.5 kW

    def test_solar_production_high_temperature_derating(self):
        """Testira pad efikasnosti pri visokim temperaturama."""
        weather_data = {
            "global_tilted_irradiance_instant": 1000.0, # W/m2
            "temperature_2m": 45.0, # °C
            "is_day": 1
        }
        # Temp razlika: 45 - 25 = 20 °C
        # Eff_temp = 1 - (20 * 0.004) = 0.92
        # Potencijalna proizvodnja: (5000 / 1000) * 1000 * 0.90 * 0.92 / 1000 = 4.14 kW
        # Ograniceno na inverter 4.5 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 4.14, places=2)

    # --- Testovi za calculate_household_consumption ---

    def test_household_consumption_base_only(self):
        """Testira potrosnju samo sa baznom potrosnjom (IoT iskljuceni)."""
        # Bazna potrosnja je 0.5 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.iot_devices_data_all_off)
        self.assertAlmostEqual(consumption, 0.5, places=2)

    def test_household_consumption_with_some_iot_on(self):
        """Testira potrosnju sa baznom i nekim ukljucenim IoT uredajima."""
        # Bazna potrosnja: 0.5 kW
        # IoT: 100W (0.1 kW) + 50W (0.05 kW) = 0.15 kW
        # Ukupno: 0.5 + 0.15 = 0.65 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.iot_devices_data_some_on)
        self.assertAlmostEqual(consumption, 0.65, places=2)

    def test_household_consumption_with_all_iot_on(self):
        """Testira potrosnju sa baznom i svim ukljucenim IoT uredajima."""
        # Bazna potrosnja: 0.5 kW
        # IoT: 100W (0.1 kW) + 2000W (2.0 kW) + 50W (0.05 kW) = 2.15 kW
        # Ukupno: 0.5 + 2.15 = 2.65 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.iot_devices_data_all_on)
        self.assertAlmostEqual(consumption, 2.65, places=2)

    # --- Testovi za update_battery_charge ---

   

    def test_battery_charge_charging(self):
        """Testira scenario punjenja baterije."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow, battery_loss_kw = update_battery_charge(
            battery_config_test, 2.0, self.time_step_hours
        )
        self.assertAlmostEqual(new_percentage, 50.3, places=2)
        self.assertAlmostEqual(actual_flow, 1.8, places=2)
        self.assertGreaterEqual(battery_loss_kw, 0.0)   # gubici moraju biti >= 0

    def test_battery_charge_discharging(self):
        """Testira scenario praznjenja baterije."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow, battery_loss_kw = update_battery_charge(
            battery_config_test, -2.0, self.time_step_hours
        )
        self.assertAlmostEqual(new_percentage, 49.63, places=2)
        self.assertAlmostEqual(actual_flow, -2.22, places=2)
        self.assertGreaterEqual(battery_loss_kw, 0.0)

    def test_battery_charge_full(self):
        """Testira da baterija ostaje puna kada je vec 100% i ima viska snage."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 100.0

        new_percentage, actual_flow, battery_loss_kw = update_battery_charge(
            battery_config_test, 5.0, self.time_step_hours
        )
        self.assertAlmostEqual(new_percentage, 100.0, places=2)
        self.assertAlmostEqual(actual_flow, 0.0, places=2)
        self.assertAlmostEqual(battery_loss_kw, 0.0, places=2)

    def test_battery_charge_empty(self):
        """Testira da baterija ostaje prazna kada je vec 0% i ima deficit snage."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 0.0

        new_percentage, actual_flow, battery_loss_kw = update_battery_charge(
            battery_config_test, -5.0, self.time_step_hours
        )
        self.assertAlmostEqual(new_percentage, 0.0, places=2)
        self.assertAlmostEqual(actual_flow, 0.0, places=2)
        self.assertAlmostEqual(battery_loss_kw, 0.0, places=2)

    def test_battery_charge_clipping_charge_rate(self):
        """Testira ogranicenje brzine punjenja."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow, battery_loss_kw = update_battery_charge(
            battery_config_test, 10.0, self.time_step_hours
        )
        # Punjenje ograniceno na max_charge_rate 3 kW → 0.05 kWh u 1/60 h → *0.9 = 0.045 kWh
        expected_percentage = (5.0 + 0.045) / 10.0 * 100
        self.assertAlmostEqual(new_percentage, expected_percentage, places=2)
        self.assertAlmostEqual(actual_flow, 2.7, places=2)   # 0.045 / (1/60 h) = 2.7 kW
        self.assertGreaterEqual(battery_loss_kw, 0.0)

    # --- Novi testovi za calculate_grid_contribution ---

    def test_grid_contribution_import(self):
        """Ako je potrosnja veca od proizvodnje, treba pozitivan import."""
        grid_contribution = calculate_grid_contribution(
            solar_production_kw=1.0,
            household_consumption_kw=3.0,
            battery_flow_kw=0.0,
            battery_loss_kw=0.0
        )
        self.assertAlmostEqual(grid_contribution, 2.0, places=2)

    def test_grid_contribution_export(self):
        """Ako je proizvodnja veca od potrosnje, treba negativan export."""
        grid_contribution = calculate_grid_contribution(
            solar_production_kw=5.0,
            household_consumption_kw=2.0,
            battery_flow_kw=0.0,
            battery_loss_kw=0.0
        )
        self.assertAlmostEqual(grid_contribution, -3.0, places=2)

    def test_grid_contribution_with_battery(self):
        """Ako baterija pomaze kod deficita, grid import treba da se smanji."""
        grid_contribution = calculate_grid_contribution(
            solar_production_kw=1.0,
            household_consumption_kw=4.0,
            battery_flow_kw=-2.0,   # baterija prazni 2 kW
            battery_loss_kw=0.1     # ima malo gubitaka
        )
        # Neto: (4 - 1) + (-2) + 0.1 = 1.1 kW
        self.assertAlmostEqual(grid_contribution, 1.1, places=2)


if __name__ == '__main__':
    unittest.main()
