import React from "react";
import { useSelector } from "react-redux";

export default function MyProfile() {
  const user = useSelector((state) => state.auth.user);
  const battery = useSelector((state) => state.auth.battery);
  const solarSystem = useSelector((state) => state.auth.solarSystem);
  const iotDevices = useSelector((state) => state.auth.iotDevices || []);

  if (!user) {
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
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              ☀️ Solar System
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <p><span className="font-semibold">System Name:</span> {user.system_name}</p>
              <p><span className="font-semibold">Type:</span> {user.system_type}</p>
              <p><span className="font-semibold">Panel Wattage:</span> {user.total_panel_wattage_wp} Wp</p>
              <p><span className="font-semibold">Azimuth:</span> {user.azimuth_degrees}°</p>
              <p><span className="font-semibold">Tilt:</span> {user.tilt_degrees}°</p>
              <p><span className="font-semibold">Inverter:</span> {user.inverter_capacity_kw} kW</p>
            </div>
          </div>
        )}

        {/* Battery Info */}
        {battery && (
          <div className="bg-white p-6 rounded-2xl shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">🔋 Battery</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <p><span className="font-semibold">Model:</span> {user.model_name}</p>
              <p><span className="font-semibold">Capacity:</span> {user.capacity_kwh} kWh</p>
              <p><span className="font-semibold">Charge %:</span> {user.current_charge_percentage}%</p>
              <p><span className="font-semibold">Efficiency:</span> {user.efficiency * 100}%</p>
              <p><span className="font-semibold">Manufacturer:</span> {user.manufacturer}</p>
            </div>
          </div>
        )}

        {/* IoT Devices */}
        {iotDevices.length > 0 && (
          <div className="bg-white p-6 rounded-2xl shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              📡 IoT Devices
            </h2>
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              {iotDevices.map((device, idx) => (
                <div
                  key={idx}
                  className="border p-4 rounded-xl shadow-sm bg-gray-50"
                >
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
                    {device.current_status.toUpperCase()}
                  </p>
                  <p className="text-xs text-gray-600">
                    Priority: {device.priority_level}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
