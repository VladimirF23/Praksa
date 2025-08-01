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
        # Ocekivana proizvodnja: (5000 Wp / 1000 W/m2) * 800 W/m2 * 0.80 (system_eff) * 1.0 (temp_eff) / 1000 = 3.2 kW
        # Ograniceno na inverter 4.5 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 3.2, places=2)                                   #da tolerancija izmedju production-a i izracunatog 3.2 bude +- 0.01

    def test_solar_production_cloudy_day(self):
        """Testira proizvodnju po oblacnom danu sa niskim zracenjem."""
        weather_data = {
            "global_tilted_irradiance_instant": 150.0, # W/m2
            "temperature_2m": 15.0, # °C
            "is_day": 1
        }
        # Ocekivana proizvodnja: (5000 / 1000) * 150 * 0.80 * (1 - max(0, (15-25)*0.004)) / 1000
        # = 5 * 150 * 0.80 * 1.0 / 1000 = 0.6 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 0.6, places=2)

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
        # Potencijalna proizvodnja: (10000 / 1000) * 1000 * 0.80 * 1.0 / 1000 = 8.0 kW
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
        # Eff_temp = 1 - (20 * 0.004) = 1 - 0.08 = 0.92
        # Potencijalna proizvodnja: (5000 / 1000) * 1000 * 0.80 * 0.92 / 1000 = 3.68 kW
        # Ograniceno na inverter 4.5 kW
        production = calculate_solar_production(self.solar_system_config, weather_data)
        self.assertAlmostEqual(production, 3.68, places=2)

    # --- Testovi za calculate_household_consumption ---

    def test_household_consumption_base_only(self):
        """Testira potrosnju samo sa baznom potrosnjom (IoT iskljuceni)."""
        # Bazna potrosnja je 0.5 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.solar_system_config, self.iot_devices_data_all_off)
        self.assertAlmostEqual(consumption, 0.5, places=2)

    def test_household_consumption_with_some_iot_on(self):
        """Testira potrosnju sa baznom i nekim ukljucenim IoT uredajima."""
        # Bazna potrosnja: 0.5 kW
        # IoT: 100W (0.1 kW) + 50W (0.05 kW) = 0.15 kW
        # Ukupno: 0.5 + 0.15 = 0.65 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.solar_system_config, self.iot_devices_data_some_on)
        self.assertAlmostEqual(consumption, 0.65, places=2)

    def test_household_consumption_with_all_iot_on(self):
        """Testira potrosnju sa baznom i svim ukljucenim IoT uredajima."""
        # Bazna potrosnja: 0.5 kW
        # IoT: 100W (0.1 kW) + 2000W (2.0 kW) + 50W (0.05 kW) = 2.15 kW
        # Ukupno: 0.5 + 2.15 = 2.65 kW
        consumption = calculate_household_consumption(self.solar_system_config, self.solar_system_config, self.iot_devices_data_all_on)
        self.assertAlmostEqual(consumption, 2.65, places=2)

    # --- Testovi za update_battery_charge ---

    def test_battery_charge_charging(self):
        """Testira scenario punjenja baterije."""
        # Pocetna napunjenost: 50% (5 kWh)
        # Neto snaga: 2.0 kW (visak, puni se)
        # Time step: 1/60 h
        # Dostupna energija: 2.0 * (1/60) = 0.0333 kWh
        # Max punjenje po brzini: 3.0 * (1/60) = 0.05 kWh
        # Preostali kapacitet: 10.0 - 5.0 = 5.0 kWh
        # Stvarno punjenje: min(0.0333 * 0.9, 0.05, 5.0) = min(0.03, 0.05, 5.0) = 0.03 kWh
        # Nova napunjenost kWh: 5.0 + 0.03 = 5.03 kWh
        # Nova napunjenost %: (5.03 / 10.0) * 100 = 50.3%
        # Protok: 0.03 / (1/60) = 1.8 kW
        
        # Kopiramo konfiguraciju baterije i azuriramo pocetni procenat za test
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow = update_battery_charge(battery_config_test, 2.0, self.time_step_hours)
        self.assertAlmostEqual(new_percentage, 50.3, places=2)
        self.assertAlmostEqual(actual_flow, 1.8, places=2) # 0.03 kWh / (1/60 h) = 1.8 kW

    def test_battery_charge_discharging(self):
        """Testira scenario praznjenja baterije."""
        # Pocetna napunjenost: 50% (5 kWh)
        # Neto snaga: -2.0 kW (deficit, prazni se)
        # Time step: 1/60 h
        # Potrebna energija: 2.0 * (1/60) = 0.0333 kWh
        # Max praznjenje po brzini: 4.0 * (1/60) = 0.0667 kWh
        # Stvarno praznjenje: min(0.0333 / 0.9, 0.0667, 5.0) = min(0.037, 0.0667, 5.0) = 0.037 kWh
        # Nova napunjenost kWh: 5.0 - 0.037 = 4.963 kWh
        # Nova napunjenost %: (4.963 / 10.0) * 100 = 49.63%
        # Protok: -0.037 / (1/60) = -2.22 kW
        
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow = update_battery_charge(battery_config_test, -2.0, self.time_step_hours)
        self.assertAlmostEqual(new_percentage, 49.63, places=2)
        self.assertAlmostEqual(actual_flow, -2.22, places=2) # -0.037 kWh / (1/60 h) = -2.22 kW

    def test_battery_charge_full(self):
        """Testira da baterija ostaje puna kada je vec 100% i ima viska snage."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 100.0 # 10 kWh

        new_percentage, actual_flow = update_battery_charge(battery_config_test, 5.0, self.time_step_hours) # Veliki visak
        self.assertAlmostEqual(new_percentage, 100.0, places=2)
        self.assertAlmostEqual(actual_flow, 0.0, places=2) # Nema protoka jer je puna

    def test_battery_charge_empty(self):
        """Testira da baterija ostaje prazna kada je vec 0% i ima deficit snage."""
        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 0.0 # 0 kWh

        new_percentage, actual_flow = update_battery_charge(battery_config_test, -5.0, self.time_step_hours) # Veliki deficit
        self.assertAlmostEqual(new_percentage, 0.0, places=2)
        self.assertAlmostEqual(actual_flow, 0.0, places=2) # Nema protoka jer je prazna

    def test_battery_charge_clipping_charge_rate(self):
        """Testira ogranicenje brzine punjenja."""
        # Pocetna napunjenost: 50% (5 kWh)
        # Neto snaga: 10.0 kW (ogroman visak)
        # Time step: 1/60 h
        # Dostupna energija: 10.0 * (1/60) = 0.1667 kWh
        # Max punjenje po brzini: 3.0 * (1/60) = 0.05 kWh (Ovo je limitirajuci faktor)
        # Preostali kapacitet: 5.0 kWh
        # Stvarno punjenje: min(0.1667 * 0.9, 0.05, 5.0) = min(0.15, 0.05, 5.0) = 0.05 kWh
        # Nova napunjenost kWh: 5.0 + 0.05 = 5.05 kWh
        # Nova napunjenost %: (5.05 / 10.0) * 100 = 50.5%
        # Protok: 0.05 / (1/60) = 3.0 kW (ograniceno na max_charge_rate_kw)

        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow = update_battery_charge(battery_config_test, 10.0, self.time_step_hours)
        self.assertAlmostEqual(new_percentage, 50.5, places=2)
        self.assertAlmostEqual(actual_flow, 3.0, places=2) # Ocekuje se clipping na 3.0 kW

    def test_battery_charge_clipping_discharge_rate(self):
        """Testira ogranicenje brzine praznjenja."""
        # Pocetna napunjenost: 50% (5 kWh)
        # Neto snaga: -10.0 kW (ogroman deficit)
        # Time step: 1/60 h
        # Potrebna energija: 10.0 * (1/60) = 0.1667 kWh
        # Max praznjenje po brzini: 4.0 * (1/60) = 0.0667 kWh (Ovo je limitirajuci faktor)
        # Stvarno praznjenje: min(0.1667 / 0.9, 0.0667, 5.0) = min(0.185, 0.0667, 5.0) = 0.0667 kWh
        # Nova napunjenost kWh: 5.0 - 0.0667 = 4.9333 kWh
        # Nova napunjenost %: (4.9333 / 10.0) * 100 = 49.33%
        # Protok: -0.0667 / (1/60) = -4.0 kW (ograniceno na max_discharge_rate_kw)

        battery_config_test = self.battery_config.copy()
        battery_config_test["current_charge_percentage"] = 50.0

        new_percentage, actual_flow = update_battery_charge(battery_config_test, -10.0, self.time_step_hours)
        self.assertAlmostEqual(new_percentage, 49.33, places=2)
        self.assertAlmostEqual(actual_flow, -4.0, places=2) # Ocekuje se clipping na -4.0 kW

    def test_battery_charge_no_battery_system(self):
        """Testira ponasanje kada sistem nema bateriju (capacity_kwh = 0)."""
        no_battery_config = self.battery_config.copy()
        no_battery_config["capacity_kwh"] = 0.0

        new_percentage, actual_flow = update_battery_charge(no_battery_config, 2.0, self.time_step_hours)
        self.assertAlmostEqual(new_percentage, 0.0, places=2)
        self.assertAlmostEqual(actual_flow, 0.0, places=2)

    # --- Testovi za calculate_grid_contribution ---


       

    def test_grid_contribution_export_scenario(self):
        """Testira scenario izvoza snage u mrezu."""
        # Proizvodnja: 5.0 kW
        # Potrosnja: 1.0 kW
        # Baterija puni: 2.0 kW (battery_flow_kw je pozitivno, znaci baterija APSORBUJE 2.0 kW tj ona se puni)
        # net_demand_or_surplus = household_consumption_kw - solar_production_kw
        # net_demand_or_surplus =  1 kW  - 5kW = -4kW
        # grid_contribution_kw = net_demand_or_surplus + battery_flow_kw = -4kW + 2kW = -2kW

        # Po nasoj konvenciji, visak koji ide u mrezu je NEGATIVAN. Ocekujemo -2.0 kW.
        grid_contribution = calculate_grid_contribution(5.0, 1.0, 2.0)
        self.assertAlmostEqual(grid_contribution, -2.0, places=2)

    def test_grid_contribution_import_scenario(self):
        """Testira scenario uvoza snage iz mreze."""
        # Proizvodnja: 1.0 kW
        # Potrosnja: 5.0 kW
        # Baterija prazni: -2.0 kW (battery_flow_kw je negativno, znaci baterija ISPORUCUJE 2.0 kW tj smanjuje potrosnju)
        # Neto bilans: 1.0 (proizvodnja) + 2.0 (iz baterije) - 5.0 (potrosnja) = -2.0 kW deficita
        # Po nasoj konvenciji, deficit koji se pokriva iz mreze je POZITIVAN. Ocekujemo 2.0 kW.
        grid_contribution = calculate_grid_contribution(1.0, 5.0, -2.0)
        self.assertAlmostEqual(grid_contribution, 2.0, places=2)

    def test_grid_contribution_self_sufficient(self):
        """Testira scenario samoodrzivosti (bez razmene sa mrezom)."""
        # Proizvodnja: 3.0 kW
        # Potrosnja: 2.0 kW
        # Baterija puni: 1.0 kW
        # Neto bilans: 3.0 - 2.0 - 1.0 = 0.0 kW
        grid_contribution = calculate_grid_contribution(3.0, 2.0, 1.0)
        self.assertAlmostEqual(grid_contribution, 0.0, places=2)

    def test_grid_contribution_no_battery_import(self):
        """Testira uvoz bez baterije."""
        # Proizvodnja: 1.0 kW
        # Potrosnja: 3.0 kW
        # Baterija: 0.0 kW (nema baterije ili ne radi)
        # Neto bilans: 1.0 - 3.0 - 0.0 = -2.0 kW
        # Po konvenciji, -2.0 kW znaci uvoz, pa treba biti 2.0 kW
        grid_contribution = calculate_grid_contribution(1.0, 3.0, 0.0)
        self.assertAlmostEqual(grid_contribution, 2.0, places=2)

    def test_grid_contribution_no_battery_export(self):
        """Testira izvoz bez baterije."""
        # Proizvodnja: 3.0 kW
        # Potrosnja: 1.0 kW
        # Baterija: 0.0 kW
        # Neto bilans: 3.0 - 1.0 - 0.0 = 2.0 kW
        # Po konvenciji, 2.0 kW znaci izvoz, pa treba biti -2.0 kW
        grid_contribution = calculate_grid_contribution(3.0, 1.0, 0.0)
        self.assertAlmostEqual(grid_contribution, -2.0, places=2)


if __name__ == '__main__':
    unittest.main()
