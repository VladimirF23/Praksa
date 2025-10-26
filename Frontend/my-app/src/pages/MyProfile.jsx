// MyProfile.js
import React, { useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { addIotDevice, deleteIotDevice } from "../api/iotApi"; 
import { addBatteryApi,deleteBatteryApi } from "../api/batteryApi";
import { setIotDevices,setBatteryDetails } from "../features/authorization/authSlice";

// --- TEMPORARY CONSTANTS (Should be imported from constants/predefinedData.js) ---
const IOT_DEVICE_TYPES = ['Light', 'HVAC', 'Appliance', 'Other'];
const IOT_PRIORITY_LEVELS = ['low', 'medium', 'critical'];
// ---------------------------------------------------------------------------------

export default function MyProfile() {
  const user = useSelector((state) => state.auth.user);
  const battery = useSelector((state) => state.auth.battery);
  const solarSystem = useSelector((state) => state.auth.solarSystem);
  const iotDevices = useSelector((state) => state.auth.iotDevices || []);
  const dispatch = useDispatch();

  // Local state for modals/forms
  const [isModalOpen, setIsModalOpen] = useState(false); 
  const [isBatteryModalOpen, setIsBatteryModalOpen] = useState(false); 
  

  const [newDeviceForm, setNewDeviceForm] = useState({
    device_name: '',
    device_type: IOT_DEVICE_TYPES[0] || 'Other', 
    base_consumption_watts: 50,
    priority_level: 'low',
    is_smart_device: false,
  });
  
  const [newBatteryForm, setNewBatteryForm] = useState({
    model_name: 'Powerwall 2',
    capacity_kwh: 13.5,
    manufacturer: 'Tesla',
    efficiency: 0.9,
    max_charge_rate_kw: 5.0, 
    max_discharge_rate_kw: 7.0,
  });


  if (!user) {
    // ... (Not logged in JSX unchanged)
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h2 className="text-xl font-bold text-gray-700">Not logged in</h2>
            <p className="text-gray-500 mt-2">
              Please log in to view your profile.
            </p>
          </div>
        </div>
      );
  }

  // --- Handlers for BATTERY Functionality (Unchanged) ---
  const handleBatteryFormChange = (e) => {
    const { name, value } = e.target;
    const numericFields = [
        'capacity_kwh', 
        'efficiency', 
        'max_charge_rate_kw', 
        'max_discharge_rate_kw'
    ];
    setNewBatteryForm(prev => ({ 
        ...prev, 
        [name]: numericFields.includes(name) ? parseFloat(value) : value
    }));
  };

  const handleAddBatterySubmit = async (e) => {
    e.preventDefault();

    try {
      const newBattery = await addBatteryApi(newBatteryForm);
      if (newBattery) {
        dispatch(setBatteryDetails(newBattery)); 
      }

      setIsBatteryModalOpen(false);
      alert("Baterija uspešno dodata! (Battery successfully added!)");
    } catch (error) {
      console.error("Error adding battery:", error);
      alert("Greška pri dodavanju baterije: " + (error.response?.data?.detail || error.message));
    }
  };


  const handleDeleteBattery = async () => {
    if (!window.confirm("Da li ste sigurni da želite da obrišete bateriju? Ovo se ne može poništiti.")) {
      return;
    }

    const batteryId = battery?.battery_id;
    const systemId = solarSystem?.system_id;

    if (!batteryId || !systemId) {
        alert("Greška: Nema informacija o bateriji ili solarnom sistemu u stanju.");
        return;
    }

    try {
      await deleteBatteryApi(batteryId, systemId);
      dispatch(setBatteryDetails(null)); 

      alert("Baterija uspešno obrisana! (Battery successfully deleted!)");
    } catch (error) {
      console.error("Error deleting battery:", error);
      alert("Greška pri brisanju baterije: " + (error.response?.data?.detail || error.message));
    }
  };

  // --- Handlers for Adding/Deleting IoT Device (Unchanged) ---
  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewDeviceForm(prev => ({ 
        ...prev, 
        [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const handleAddDeviceSubmit = async (e) => {
    e.preventDefault();
    const payload = {
      device_name: newDeviceForm.device_name || 'Custom Device',
      device_type: newDeviceForm.device_type,
      base_consumption_watts: parseFloat(newDeviceForm.base_consumption_watts) || 0,
      priority_level: newDeviceForm.priority_level,
      current_status: 'off', 
      is_smart_device: newDeviceForm.is_smart_device,
    };
    try {
      const result = await addIotDevice(payload);
      const updatedDevices = result.devices || [
          ...iotDevices, 
          { ...payload, device_id: Date.now() } 
      ]; 
      dispatch(setIotDevices(updatedDevices)); 
      setIsModalOpen(false); 
      setNewDeviceForm({ 
          device_name: '', 
          device_type: IOT_DEVICE_TYPES[0] || 'Other', // Reset to 'Light'
          base_consumption_watts: 50, 
          priority_level: 'low', 
          is_smart_device: false 
      });
      alert("Uređaj uspešno dodat! (Device successfully added!)");
    } catch (error) {
      alert("Greška pri dodavanju uređaja: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteDevice = async (deviceId, deviceName) => {
    if (!window.confirm(`Da li ste sigurni da želite da obrišete uređaj: ${deviceName}?`)) {
      return;
    }
    try {
      const result = await deleteIotDevice(deviceId);
      const updatedDevices = result.devices || iotDevices.filter(d => d.device_id !== deviceId); 
      dispatch(setIotDevices(updatedDevices)); 
      alert("Uređaj uspešno obrisan! (Device successfully deleted!)");
    } catch (error) {
      alert("Greška pri brisanju uređaja: " + (error.response?.data?.detail || error.message));
    }
  };


  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4 sm:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* User Info */}
        <div className="bg-white p-6 rounded-2xl shadow-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            👤 My Profile
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <p><span className="font-semibold">Username:</span> {user.username}</p>
            <p><span className="font-semibold">Email:</span> {user.email}</p>
            <p><span className="font-semibold">Type:</span> {user.user_type}</p>
            <p><span className="font-semibold">House size:</span> {user.house_size_sqm} m²</p>
            <p><span className="font-semibold">Members:</span> {user.num_household_members}</p>
            <p><span className="font-semibold">Location:</span> {user.latitude}, {user.longitude}</p>
          </div>
        </div>

        {/* Solar System Info */}
        {solarSystem && (
        <div className="bg-white p-6 rounded-2xl shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">☀️ Solar System</h2>
            <div className="grid sm:grid-cols-2 gap-4">
            <p><span className="font-semibold">System Name:</span> {solarSystem.system_name}</p>
            <p><span className="font-semibold">Type:</span> {solarSystem.system_type}</p>
            <p><span className="font-semibold">Panel Wattage:</span> {solarSystem.total_panel_wattage_wp} Wp</p>
            <p><span className="font-semibold">Azimuth:</span> {solarSystem.azimuth_degrees}°</p>
            <p><span className="font-semibold">Tilt:</span> {solarSystem.tilt_degrees}°</p>
            <p><span className="font-semibold">Inverter:</span> {solarSystem.inverter_capacity_kw} kW</p>
            </div>
        </div>
        )}

        {/* Battery Info  */}
        <div className="bg-white p-6 rounded-2xl shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">🔋 Battery</h2>
            {battery ? (
                <button
                  onClick={handleDeleteBattery}
                  className="px-4 py-2 bg-red-600 text-white font-semibold rounded-lg shadow-md hover:bg-red-700 transition duration-150"
                >
                  🗑️ Delete Battery
                </button>
            ) : (
                <button
                  onClick={() => setIsBatteryModalOpen(true)}
                  className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700 transition duration-150"
                >
                  ➕ Add Battery
                </button>
            )}
          </div>
          {battery ? (
            <div className="grid sm:grid-cols-2 gap-4">
              <p><span className="font-semibold">Model:</span> {battery.model_name}</p>
              <p><span className="font-semibold">Capacity:</span> {battery.capacity_kwh} kWh</p>
              <p><span className="font-semibold">Charge:</span> {battery.current_charge_percentage}%</p>
              <p><span className="font-semibold">Efficiency:</span> {battery.efficiency * 100}%</p>
              <p><span className="font-semibold">Manufacturer:</span> {battery.manufacturer}</p>
            </div>
          ) : (
            <p className="text-gray-500 italic">Baterija nije dodata. Dodajte je da biste je koristili za automatizaciju.</p>
          )}
        </div>


        {/* IoT Devices */}
        <div className="bg-white p-6 rounded-2xl shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-800">
              📡 IoT Devices
            </h2>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition duration-150"
            >
              ➕ Add New IoT
            </button>
          </div>

          {iotDevices.length === 0 ? (
            <p className="text-gray-500 italic">Nema registrovanih IoT uređaja.</p>
          ) : (
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              {iotDevices.map((device, idx) => (
                <div
                  key={device.device_id || idx}
                  className="border p-4 rounded-xl shadow-sm bg-gray-50 flex flex-col justify-between"
                >
                  <div>
                    <h3 className="font-semibold text-lg">{device.device_name}</h3>
                    <p className="text-sm text-gray-500">{device.device_type}</p>
                    <p>⚡ {device.base_consumption_watts} W</p>
                    <p
                      className={`font-semibold ${
                          device.current_status === "on"
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                    >
                      {device.current_status?.toUpperCase()}
                    </p>
                    <p className="text-xs text-gray-600 mb-3">
                      Priority: {device.priority_level}
                    </p>
                  </div>
                  {/* Delete Button */}
                  <button
                    onClick={() => handleDeleteDevice(device.device_id, device.device_name)}
                    className="mt-2 text-sm text-red-600 hover:text-red-800 font-medium self-end transition duration-150"
                    title={`Delete ${device.device_name}`}
                  >
                    🗑️ Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* --- Add New IoT Modal (FIXED SIZE & GRID) --- */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50 p-4">
          {/* Apply a smaller max-w-md */}
          <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md"> 
            <h3 className="text-xl font-bold text-gray-800 mb-6">Dodaj Novi IoT Uređaj</h3>
            <form onSubmit={handleAddDeviceSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Device Name (Full width) */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Naziv Uređaja</label>
                  <input
                    type="text"
                    name="device_name"
                    value={newDeviceForm.device_name}
                    onChange={handleFormChange}
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>

                {/* Device Type (Half width) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tip Uređaja</label>
                  <select
                    name="device_type"
                    value={newDeviceForm.device_type}
                    onChange={handleFormChange}
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  >
                    {IOT_DEVICE_TYPES.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                {/* Base Consumption (Watts) (Half width) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Potrošnja (Watts)</label>
                  <input
                    type="number"
                    name="base_consumption_watts"
                    value={newDeviceForm.base_consumption_watts}
                    onChange={handleFormChange}
                    required
                    min="1"
                    step="any"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>

                {/* Priority Level (Half width) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nivo Prioriteta</label>
                  <select
                    name="priority_level"
                    value={newDeviceForm.priority_level}
                    onChange={handleFormChange}
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  >
                    {IOT_PRIORITY_LEVELS.map(level => (
                      <option key={level} value={level}>{level.charAt(0).toUpperCase() + level.slice(1)}</option>
                    ))}
                  </select>
                </div>

                {/* Is Smart Device Checkbox (Half width) */}
                <div className="flex items-center pt-2">
                  <input
                    id="is_smart_device"
                    name="is_smart_device"
                    type="checkbox"
                    checked={newDeviceForm.is_smart_device}
                    onChange={handleFormChange}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="is_smart_device" className="ml-2 block text-sm font-medium text-gray-700">
                    Pametan uređaj (Smart Device)
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-4  border-t pt-4 border-gray-100 mt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 transition duration-150"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white font-semibold rounded-md shadow-md hover:bg-green-700 transition duration-150"
                >
                  Add Device
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* --- Add New Battery Modal (FIXED SIZE & GRID) --- */}
      {isBatteryModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50 p-4">
          {/* Apply a smaller max-w-md */}
          <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md">
            <h3 className="text-xl font-bold text-gray-800 mb-6">Dodaj Bateriju</h3>
            <form onSubmit={handleAddBatterySubmit} className="space-y-4">
              
              {/* Full-width fields (Model Name, Manufacturer) */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Model Baterije</label>
                <input
                  type="text"
                  name="model_name"
                  value={newBatteryForm.model_name}
                  onChange={handleBatteryFormChange}
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Proizvođač</label>
                <input
                  type="text"
                  name="manufacturer"
                  value={newBatteryForm.manufacturer}
                  onChange={handleBatteryFormChange}
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                />
              </div>

              {/* Two-column grid for numerical fields */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                
                {/* Capacity (kWh) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Kapacitet (kWh)</label>
                  <input
                    type="number"
                    name="capacity_kwh"
                    value={newBatteryForm.capacity_kwh}
                    onChange={handleBatteryFormChange}
                    required
                    min="0.1"
                    step="0.1"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>

                {/* Efficiency (0.0 to 1.0) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Efikasnost (0.0 - 1.0)</label>
                  <input
                    type="number"
                    name="efficiency"
                    value={newBatteryForm.efficiency}
                    onChange={handleBatteryFormChange}
                    required
                    min="0.5"
                    max="1.0"
                    step="0.01"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>
                
                {/* Max Charge Rate (kW) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Maks. Stopa Punjenja (kW)</label>
                  <input
                    type="number"
                    name="max_charge_rate_kw"
                    value={newBatteryForm.max_charge_rate_kw}
                    onChange={handleBatteryFormChange}
                    required
                    min="0.1"
                    step="0.1"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>

                {/* Max Discharge Rate (kW) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Maks. Stopa Pražnjenja (kW)</label>
                  <input
                    type="number"
                    name="max_discharge_rate_kw"
                    value={newBatteryForm.max_discharge_rate_kw}
                    onChange={handleBatteryFormChange}
                    required
                    min="0.1"
                    step="0.1"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                  />
                </div>

              </div> {/* End of two-column grid */}

              <div className="flex justify-end space-x-4  border-t pt-4 border-gray-100 mt-4">
                <button
                  type="button"
                  onClick={() => setIsBatteryModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 transition duration-150"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white font-semibold rounded-md shadow-md hover:bg-green-700 transition duration-150"
                >
                  Add Battery
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}