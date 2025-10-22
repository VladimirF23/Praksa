import React, { useEffect, useState } from "react";
import { fetchAllUsers, updateUserApproval } from "../api/adminApi";

const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const data = await fetchAllUsers();
        setUsers(data);
      } catch (err) {
        console.error("Error fetching users:", err);
      } finally {
        setLoading(false);
      }
    };
    loadUsers();
  }, []);

  const handleApprovalToggle = async (user) => {
    if (!user.solar_system) {
      console.warn("User has no solar system");
      return;
    }

    const newStatus = user.solar_system.approved === 1 ? 0 : 1;
    setUpdating(true);

    try {
      await updateUserApproval(user.solar_system.system_id, newStatus);
      console.log(
        `System for ${user.username} ${
          newStatus ? "approved ✅" : "disapproved ❌"
        }`
      );

      setUsers((prev) =>
        prev.map((u) =>
          u.user_id === user.user_id
            ? {
                ...u,
                solar_system: { ...u.solar_system, approved: newStatus },
              }
            : u
        )
      );
    } catch (err) {
      console.error("Error updating approval:", err);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="p-6 text-gray-200">Loading users...</div>;

  return (
    <div className="p-6 text-gray-100 bg-gray-900 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-center text-teal-400">
        🌞 Admin Dashboard
      </h1>

      {users.map((user) => {
        const approved = user.solar_system?.approved === 1;
        const isExpanded = expanded === user.user_id;

        return (
          <div
            key={user.user_id}
            className="bg-gray-800 rounded-2xl shadow-lg mb-5 border border-gray-700 overflow-hidden transition-all"
          >
            {/* Header */}
            <div
              className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-750"
              onClick={() =>
                setExpanded(isExpanded ? null : user.user_id)
              }
            >
              <div>
                <h2 className="text-xl font-semibold text-white">
                  {user.username}
                </h2>
                <p className="text-gray-400 text-sm">{user.email}</p>
              </div>
              <div className="flex items-center gap-3">
                {user.solar_system ? (
                  <>
                    <span
                      className={`text-sm font-medium ${
                        approved ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {approved ? "Approved ✅" : "Pending ❌"}
                    </span>
                    <button
                      disabled={updating}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApprovalToggle(user);
                      }}
                      className={`px-4 py-1 rounded-md text-sm font-medium ${
                        approved
                          ? "bg-red-600 hover:bg-red-700"
                          : "bg-green-600 hover:bg-green-700"
                      } disabled:opacity-60`}
                    >
                      {approved ? "Disapprove" : "Approve"}
                    </button>
                  </>
                ) : (
                  <span className="text-gray-400 text-sm">No System</span>
                )}
              </div>
            </div>

            {/* Expandable Content */}
            {isExpanded && (
              <div className="p-5 bg-gray-850 border-t border-gray-700">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* User Info */}
                  <div>
                    <h3 className="text-teal-400 font-semibold mb-2">
                      👤 User Info
                    </h3>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>📧 Email: {user.email}</li>
                      <li>🏠 House Size: {user.house_size_sqm} m²</li>
                      <li>👨‍👩‍👧 Members: {user.num_household_members}</li>
                      <li>🌍 Location: {user.latitude}, {user.longitude}</li>
                      <li>🕒 Registered: {new Date(user.registration_date * 1000).toLocaleString()}</li>
                    </ul>
                  </div>

                  {/* Solar System */}
                  {user.solar_system && (
                    <div>
                      <h3 className="text-teal-400 font-semibold mb-2">
                        ⚡ Solar System
                      </h3>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li>🏷️ Name: {user.solar_system.system_name}</li>
                        <li>🔋 Type: {user.solar_system.system_type}</li>
                        <li>
                          ☀️ Panels: {user.solar_system.total_panel_wattage_wp} Wp
                        </li>
                        <li>
                          ⚙️ Inverter: {user.solar_system.inverter_capacity_kw} kW
                        </li>
                        <li>
                          📉 Base Load: {user.solar_system.base_consumption_kw} kW
                        </li>
                        <li>
                          📐 Tilt: {user.solar_system.tilt_degrees}°
                        </li>
                        <li>
                          🧭 Azimuth: {user.solar_system.azimuth_degrees}°
                        </li>
                      </ul>

                      {/* Battery */}
                      {user.solar_system.battery && (
                        <div className="mt-3">
                          <h4 className="text-yellow-400 font-semibold">
                            🔋 Battery
                          </h4>
                          <ul className="text-sm text-gray-300 space-y-1">
                            <li>
                              🏷️ {user.solar_system.battery.model_name} (
                              {user.solar_system.battery.manufacturer})
                            </li>
                            <li>
                              ⚡ Capacity: {user.solar_system.battery.capacity_kwh} kWh
                            </li>
                            <li>
                              🔋 Current Charge: {user.solar_system.battery.current_charge_percentage}%
                            </li>
                            <li>
                              💡 Efficiency: {Math.round(user.solar_system.battery.efficiency * 100)}%
                            </li>
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* IoT Devices */}
                <div className="mt-6">
                  <h3 className="text-teal-400 font-semibold mb-2">
                    📡 IoT Devices ({user.iot_devices.length})
                  </h3>
                  {user.iot_devices.length > 0 ? (
                    <table className="min-w-full text-sm bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                      <thead className="bg-gray-700 text-gray-200">
                        <tr>
                          <th className="px-3 py-2 text-left">Device</th>
                          <th className="px-3 py-2 text-left">Type</th>
                          <th className="px-3 py-2 text-center">Status</th>
                          <th className="px-3 py-2 text-center">Power (W)</th>
                          <th className="px-3 py-2 text-center">Priority</th>
                        </tr>
                      </thead>
                      <tbody>
                        {user.iot_devices.map((device) => (
                          <tr
                            key={device.device_id}
                            className="border-t border-gray-700 hover:bg-gray-750"
                          >
                            <td className="px-3 py-2">{device.device_name}</td>
                            <td className="px-3 py-2">{device.device_type}</td>
                            <td
                              className={`px-3 py-2 text-center ${
                                device.current_status === "on"
                                  ? "text-green-400"
                                  : "text-red-400"
                              }`}
                            >
                              {device.current_status.toUpperCase()}
                            </td>
                            <td className="px-3 py-2 text-center">
                              {device.base_consumption_watts}
                            </td>
                            <td className="px-3 py-2 text-center capitalize">
                              {device.priority_level}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-gray-400 text-sm">
                      No IoT devices connected.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AdminPage;
