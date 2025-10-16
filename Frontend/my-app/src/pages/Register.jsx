import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

import { handleRegistration } from "../services/authServices";

import { clearAuthError } from "../features/authorization/authSlice";
import { 
    SYSTEM_TYPES, 
    PREDEFINED_BATTERIES, 
    PREDEFINED_IOT_DEVICES 
} from "../constants/predefinedData"; 

const Register = () => {
    // Lokalni state za sva polja
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        latitude: '',
        longitude: '',
        house_size_sqm: '',
        num_household_members: '',
        system_name: 'My Solar System',
        system_type: 'grid_tied_hybrid', // Default
        total_panel_wattage_wp: '',
        azimuth_degrees: '',
        tilt_degrees: '',
        inverter_capacity_kw: '',
        
        // Polja za Bateriju
        selectedBatteryId: 1, // Default za izbor iz PREDEFINED_BATTERIES
        isBatteryCustom: false, // NOVO: Da li korisnik unosi ručne vrednosti za bateriju
        customBattery: {        // NOVO: Ručne vrednosti za bateriju
            model_name: 'Custom Battery Model',
            manufacturer: 'Custom Manufacturer',
            capacity_kwh: '5.0',
            max_charge_rate_kw: '2.5',
            max_discharge_rate_kw: '2.5',
            efficiency: '0.90',
        },

        // Polja za IoT uredjaje
        selectedIotDeviceIds: [101, 102], // Default
        customIotConsumptionWatts: {} // NOVO: { id: vrednost, ... } za ručni unos potrošnje
    });

    const error = useSelector((state) => state.auth.error);
    const dispatch = useDispatch();
    const navigate = useNavigate();

    // --- Glavni handler za jednostavna polja (username, email, house_size...) ---
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // --- Handler za ručni unos specifikacija baterije ---
    const handleCustomBatteryChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            customBattery: {
                ...prev.customBattery,
                [name]: value
            }
        }));
    };
    
    // --- Handler za ručni unos potrošnje IoT uređaja ---
    const handleCustomIotConsumptionChange = (id, value) => {
        setFormData(prev => ({
            ...prev,
            customIotConsumptionWatts: {
                ...prev.customIotConsumptionWatts,
                [id]: value
            }
        }));
    };

    // --- Handler za selekciju/deselekciju IoT uređaja ---
    const handleIotSelect = (id, isChecked) => {
        setFormData(prev => {
            const currentIds = prev.selectedIotDeviceIds;
            if (isChecked) {
                return { ...prev, selectedIotDeviceIds: [...currentIds, id] };
            } else {
                return { ...prev, selectedIotDeviceIds: currentIds.filter(i => i !== id) };
            }
        });
    };
    
    // --- Glavni handler za slanje forme ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        dispatch(clearAuthError());

        // --- 1. Mapiranje izabranih predefinisanih/RUČNIH podataka u API format ---
        
        // Logika za BATERIJU
        let batteryPayload = null;
        const isGridTied = formData.system_type === 'grid_tied';

        if (!isGridTied) {
            if (formData.isBatteryCustom) {
                // Koristi ručne vrednosti
                batteryPayload = {
                    model_name: formData.customBattery.model_name || 'Custom Model',
                    capacity_kwh: parseFloat(formData.customBattery.capacity_kwh) || 0,
                    max_charge_rate_kw: parseFloat(formData.customBattery.max_charge_rate_kw) || 0,
                    max_discharge_rate_kw: parseFloat(formData.customBattery.max_discharge_rate_kw) || 0,
                    efficiency: parseFloat(formData.customBattery.efficiency) || 0,
                    manufacturer: formData.customBattery.manufacturer || 'Custom Manufacturer',
                    current_charge_percentage: 50.00,
                };
            } else {
                // Koristi predefinisane vrednosti
                const selectedBattery = PREDEFINED_BATTERIES.find(b => b.id === formData.selectedBatteryId);
                if (selectedBattery) {
                    batteryPayload = {
                        model_name: selectedBattery.name,
                        capacity_kwh: selectedBattery.capacity_kwh,
                        max_charge_rate_kw: selectedBattery.max_charge_rate_kw,
                        max_discharge_rate_kw: selectedBattery.max_discharge_rate_kw,
                        efficiency: selectedBattery.efficiency,
                        manufacturer: selectedBattery.manufacturer,
                        current_charge_percentage: 50.00,
                    };
                }
            }
        }


        // Logika za IoT UREĐAJE
        const selectedIotDevices = PREDEFINED_IOT_DEVICES
            .filter(d => formData.selectedIotDeviceIds.includes(d.id))
            .map(d => {
                const customValue = formData.customIotConsumptionWatts[d.id];
                return {
                    device_name: d.device_name,
                    device_type: d.device_type,
                    // Koristi RUČNU VREDNOST ako postoji i nije prazan string, inače koristi predefinisanu
                    base_consumption_watts: (customValue !== undefined && customValue !== '') 
                                            ? parseFloat(customValue)
                                            : d.base_consumption_watts,
                    priority_level: d.priority_level,
                    current_status: 'off',
                    is_smart_device: d.is_smart_device
                }
            });

        // Kreiranje API Payload-a
        const apiPayload = {
            username: formData.username,
            email: formData.email,
            password: formData.password,
            user_type: "regular", // Fiksirano
            house_size_sqm: parseFloat(formData.house_size_sqm),
            num_household_members: parseInt(formData.num_household_members, 10) || 1,
            latitude: parseFloat(formData.latitude),
            longitude: parseFloat(formData.longitude),
            system_name: formData.system_name,
            system_type: formData.system_type,
            total_panel_wattage_wp: parseFloat(formData.total_panel_wattage_wp),
            azimuth_degrees: parseInt(formData.azimuth_degrees, 10),
            tilt_degrees: parseInt(formData.tilt_degrees, 10),
            inverter_capacity_kw: parseFloat(formData.inverter_capacity_kw),
            
            // USLOVNO DODAVANJE POLJA ZA BATERIJU
            ...(batteryPayload && { ...batteryPayload }),
            
            // Dodavanje liste IoT uređaja
            iot_devices: selectedIotDevices
        };

        // --- 2. Poziv Service logike ---
        await handleRegistration(apiPayload, dispatch, navigate);
    };

    return (
        <div className="flex justify-center items-center min-h-screen bg-gray-100 p-4">
            <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl space-y-6">
                <h2 className="text-3xl font-bold text-gray-800 text-center">Registracija Novog Sistema</h2>
                
                {/* 1. KORAK: Osnovni podaci */}
                <fieldset className="border p-4 rounded-lg space-y-4">
                    <legend className="text-lg font-semibold text-blue-600">Lični i Lokacijski Podaci</legend>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Username */}
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Korisničko Ime</label>
                            <input
                                type="text"
                                name="username"
                                id="username"
                                value={formData.username}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Email */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                            <input
                                type="email"
                                name="email"
                                id="email"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Password */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Lozinka</label>
                            <input
                                type="password"
                                name="password"
                                id="password"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Veličina Kuće (m²) */}
                        <div>
                            <label htmlFor="house_size_sqm" className="block text-sm font-medium text-gray-700">Veličina Kuće (m²)</label>
                            <input
                                type="number"
                                name="house_size_sqm"
                                id="house_size_sqm"
                                value={formData.house_size_sqm}
                                onChange={handleChange}
                                required
                                min="1"
                                step="0.1"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Broj Članova Domaćinstva */}
                        <div>
                            <label htmlFor="num_household_members" className="block text-sm font-medium text-gray-700">Broj Članova</label>
                            <input
                                type="number"
                                name="num_household_members"
                                id="num_household_members"
                                value={formData.num_household_members}
                                onChange={handleChange}
                                required
                                min="1"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Latituda */}
                        <div>
                            <label htmlFor="latitude" className="block text-sm font-medium text-gray-700">Geografska Širina (Latituda)</label>
                            <input
                                type="number"
                                name="latitude"
                                id="latitude"
                                value={formData.latitude}
                                onChange={handleChange}
                                required
                                step="any"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Longituda */}
                        <div>
                            <label htmlFor="longitude" className="block text-sm font-medium text-gray-700">Geografska Dužina (Longituda)</label>
                            <input
                                type="number"
                                name="longitude"
                                id="longitude"
                                value={formData.longitude}
                                onChange={handleChange}
                                required
                                step="any"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                    </div>
                </fieldset>

                {/* 2. KORAK: Solar System Konfiguracija */}
                <fieldset className="border p-4 rounded-lg space-y-4">
                    <legend className="text-lg font-semibold text-blue-600">Konfiguracija Sistema</legend>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                         {/* Naziv Sistema */}
                        <div>
                            <label htmlFor="system_name" className="block text-sm font-medium text-gray-700">Naziv Sistema</label>
                            <input
                                type="text"
                                name="system_name"
                                id="system_name"
                                value={formData.system_name}
                                onChange={handleChange}
                                required
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Total Panel Wattage (Wp) */}
                        <div>
                            <label htmlFor="total_panel_wattage_wp" className="block text-sm font-medium text-gray-700">Ukupna Snaga Panela (Wp)</label>
                            <input
                                type="number"
                                name="total_panel_wattage_wp"
                                id="total_panel_wattage_wp"
                                value={formData.total_panel_wattage_wp}
                                onChange={handleChange}
                                required
                                min="100"
                                step="any"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Kapacitet Invertera (kW) */}
                        <div>
                            <label htmlFor="inverter_capacity_kw" className="block text-sm font-medium text-gray-700">Kapacitet Invertera (kW)</label>
                            <input
                                type="number"
                                name="inverter_capacity_kw"
                                id="inverter_capacity_kw"
                                value={formData.inverter_capacity_kw}
                                onChange={handleChange}
                                required
                                min="0.1"
                                step="any"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Nagib (Tilt Degrees) */}
                        <div>
                            <label htmlFor="tilt_degrees" className="block text-sm font-medium text-gray-700">Nagib Panela (Stepeni)</label>
                            <input
                                type="number"
                                name="tilt_degrees"
                                id="tilt_degrees"
                                value={formData.tilt_degrees}
                                onChange={handleChange}
                                required
                                min="0"
                                max="90"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                        {/* Azimut (Azimuth Degrees) */}
                        <div>
                            <label htmlFor="azimuth_degrees" className="block text-sm font-medium text-gray-700">Azimut (Stepeni)</label>
                            <input
                                type="number"
                                name="azimuth_degrees"
                                id="azimuth_degrees"
                                value={formData.azimuth_degrees}
                                onChange={handleChange}
                                required
                                min="0"
                                max="360"
                                className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Tip Sistema</label>
                        <select name="system_type" value={formData.system_type} onChange={handleChange} className="mt-1 block w-full border border-gray-300 rounded-md p-2">
                            {SYSTEM_TYPES.map(type => (
                                <option key={type.value} value={type.value}>{type.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* USLOVNO PRIKAZIVANJE BATERIJE */}
                    {formData.system_type === 'grid_tied_hybrid' && (
                        <div className="border-t pt-4">
                            <h3 className="text-md font-semibold mb-2">Izbor Baterije</h3>
                            
                            {/* TOGGLE za Custom/Predefinisano */}
                            <div className="flex items-center space-x-4 mb-4">
                                <label className="flex items-center space-x-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="battery_choice"
                                        checked={!formData.isBatteryCustom}
                                        onChange={() => setFormData(prev => ({ ...prev, isBatteryCustom: false }))}
                                        className="h-4 w-4 text-green-600 border-gray-300"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Koristi predefinisane modele</span>
                                </label>
                                <label className="flex items-center space-x-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="battery_choice"
                                        checked={formData.isBatteryCustom}
                                        onChange={() => setFormData(prev => ({ ...prev, isBatteryCustom: true }))}
                                        className="h-4 w-4 text-blue-600 border-gray-300"
                                    />
                                    <span className="text-sm font-medium text-gray-700">Ručni unos specifikacija</span>
                                </label>
                            </div>

                            {/* PRIKAZ: Predefinisani Modeli */}
                            {!formData.isBatteryCustom ? (
                                <div className="grid grid-cols-2 gap-4">
                                    {PREDEFINED_BATTERIES.map(battery => (
                                        <div 
                                            key={battery.id} 
                                            className={`p-3 border rounded-lg cursor-pointer transition ${formData.selectedBatteryId === battery.id ? 'border-green-500 ring-2 ring-green-500 bg-green-50' : 'hover:border-gray-400'}`} 
                                            onClick={() => setFormData(prev => ({ ...prev, selectedBatteryId: battery.id }))}
                                        >
                                            <img src={battery.image} alt={battery.name} className="h-12 w-12 mx-auto mb-2 object-contain" /> 
                                            <p className="text-sm font-medium">{battery.name}</p>
                                            <p className="text-xs text-gray-500">{battery.capacity_kwh} kWh</p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                /* PRIKAZ: Ručni Unos Baterije */
                                <div className="grid grid-cols-2 gap-4 border p-4 rounded-lg bg-gray-50">
                                    <h4 className="col-span-2 text-md font-semibold text-gray-800 mb-2">Ručni Unos Specifikacija Baterije</h4>
                                    
                                    {/* Model Name */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Model</label>
                                        <input type="text" name="model_name" value={formData.customBattery.model_name} onChange={handleCustomBatteryChange} required className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                    {/* Manufacturer */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Proizvođač</label>
                                        <input type="text" name="manufacturer" value={formData.customBattery.manufacturer} onChange={handleCustomBatteryChange} required className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                    {/* Capacity (kWh) */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Kapacitet (kWh)</label>
                                        <input type="number" name="capacity_kwh" value={formData.customBattery.capacity_kwh} onChange={handleCustomBatteryChange} required step="any" min="0.1" className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                    {/* Efficiency */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Efikasnost (0.01 - 1.0)</label>
                                        <input type="number" name="efficiency" value={formData.customBattery.efficiency} onChange={handleCustomBatteryChange} required step="0.01" min="0.5" max="1.0" className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                    {/* Max Charge Rate (kW) */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Max Punjenje (kW)</label>
                                        <input type="number" name="max_charge_rate_kw" value={formData.customBattery.max_charge_rate_kw} onChange={handleCustomBatteryChange} required step="any" min="0.1" className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                    {/* Max Discharge Rate (kW) */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Max Pražnjenje (kW)</label>
                                        <input type="number" name="max_discharge_rate_kw" value={formData.customBattery.max_discharge_rate_kw} onChange={handleCustomBatteryChange} required step="any" min="0.1" className="mt-1 block w-full border border-gray-300 rounded-md p-2" />
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </fieldset>

                {/* 3. KORAK: IoT Uredjaji */}
                <fieldset className="border p-4 rounded-lg space-y-4">
                    <legend className="text-lg font-semibold text-blue-600">IoT Uređaji (Opcionalno)</legend>
                    <div className="grid grid-cols-1 gap-4">
                        {PREDEFINED_IOT_DEVICES.map(device => (
                            <div key={device.id} className="flex flex-col border rounded-lg p-3 bg-white">
                                <div className="flex items-center space-x-3">
                                    {/* Checkbox */}
                                    <input
                                        type="checkbox"
                                        id={`device-${device.id}`}
                                        checked={formData.selectedIotDeviceIds.includes(device.id)}
                                        onChange={(e) => handleIotSelect(device.id, e.target.checked)}
                                        className="h-5 w-5 text-indigo-600 border-gray-300 rounded"
                                    />
                                    
                                    {/* Label i slika */}
                                    <label htmlFor={`device-${device.id}`} className="flex items-center space-x-2 cursor-pointer flex-grow">
                                        <img src={device.image} alt={device.device_name} className="h-8 w-8 object-contain" /> 
                                        <span className="text-sm font-medium">{device.device_name}</span>
                                        <span className="text-xs text-gray-500">
                                            (Default: {device.base_consumption_watts}W)
                                        </span>
                                    </label>
                                </div>

                                {/* Ručni unos potrošnje (Prikazuje se samo ako je uređaj izabran) */}
                                {formData.selectedIotDeviceIds.includes(device.id) && (
                                    <div className="mt-2 pl-8 pt-2 border-t border-gray-100">
                                        <label htmlFor={`custom-watts-${device.id}`} className="block text-xs font-medium text-gray-500 mb-1">
                                            Ručni Unos Potrošnje (W):
                                        </label>
                                        <input
                                            type="number"
                                            id={`custom-watts-${device.id}`}
                                            placeholder={`Ostavite prazno za ${device.base_consumption_watts}W`}
                                            value={formData.customIotConsumptionWatts[device.id] || ''}
                                            onChange={(e) => handleCustomIotConsumptionChange(device.id, e.target.value)}
                                            min="1"
                                            step="any"
                                            className="w-full text-sm border-gray-300 rounded-md p-2"
                                        />
                                        <p className="text-xs text-gray-500 mt-1">Ako ostavite prazno, koristiće se default vrednost.</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </fieldset>
                
                {error && (
                    <p className="text-red-600 text-center font-medium">{error}</p>
                )}

                <button
                    type="submit"
                    className="w-full py-3 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition duration-150"
                >
                    Registruj se i Uloguj
                </button>
            </form>
        </div>
    );
};

export default Register;