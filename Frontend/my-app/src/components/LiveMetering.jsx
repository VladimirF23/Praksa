import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";

export default function LiveMetering() {
   const [status, setStatus] = useState("connecting");
  const [liveData, setLiveData] = useState(null);
  const [logMessages, setLogMessages] = useState([]);

  // Helper function to append new logs without losing old ones
  const addLog = (message) => {
    console.log(message);
    setLogMessages((prevLogs) => [...prevLogs, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  useEffect(() => {
    addLog("Attempting to connect to WebSocket...");

    const socket = io("https://solartrack.local", {
      path: '/socket.io',
      withCredentials: true,
      transports: ['websocket', 'polling']
    });

    // Check for a successful connection event
    socket.on("connect", () => {
      addLog("✅ Connection successful. Socket ID: " + socket.id);
      setStatus("connected");
    });

    // Listen for connection errors
    socket.on("connect_error", (err) => {
      addLog("❌ Connection error: " + err.message);
      setStatus("error");
    });

    // Listen for disconnection events
    socket.on("disconnect", (reason) => {
      addLog("❌ Disconnected. Reason: " + reason);
      setStatus("disconnected");
    });

    // Listen for the live data from the server
    socket.on("live_metering_data", (payload) => {
      addLog("📡 Live data received: " + JSON.stringify(payload));
      setLiveData(payload);
    });

    // Clean up the socket connection on component unmount
    return () => {
      addLog("Cleaning up and disconnecting socket...");
      socket.disconnect();
    };
  }, []);

  return (
    <div className="p-8 bg-gray-100 min-h-screen text-gray-800 font-sans">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-xl shadow-lg">
        <h2 className="text-3xl font-bold mb-4 text-center text-indigo-600">Live Metering Debugger</h2>
        <div className="mb-6 text-center">
          <p className="text-xl">
            Connection Status: <span className={`font-semibold ${status === "connected" ? "text-green-500" : status === "connecting" ? "text-yellow-500" : "text-red-500"}`}>{status}</span>
          </p>
        </div>
        <div className="bg-gray-200 p-4 rounded-lg overflow-y-auto max-h-60 mb-6">
          <h3 className="text-lg font-semibold mb-2 text-indigo-600">Client Logs</h3>
          {logMessages.map((log, index) => (
            <p key={index} className="text-sm font-mono text-gray-700">{log}</p>
          ))}
        </div>
        {liveData ? (
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-300">
            <h3 className="text-xl font-bold text-indigo-600 mb-4">Live Data</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <p className="text-gray-700"><strong>Time:</strong> {new Date(liveData.timestamp).toLocaleString()}</p>
              <p className="text-gray-700"><strong>Solar Production:</strong> {liveData.solar_production_kw} kW</p>
              <p className="text-gray-700"><strong>Household Consumption:</strong> {liveData.household_consumption_kw} kW</p>
              <p className="text-gray-700"><strong>Battery Charge:</strong> {liveData.battery_charge_percentage} %</p>
              <p className="text-gray-700"><strong>Grid Contribution:</strong> {liveData.grid_contribution_kw} kW</p>
              <p className="text-gray-700"><strong>Temperature:</strong> {liveData.current_temperature_c} °C</p>
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-500 italic">No live data yet...</p>
        )}
      </div>
    </div>
  );
}
