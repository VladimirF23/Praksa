import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";
import kuca from "./kuca.png";
import "./pulse.css"; // pulse animation

export default function LiveMetering() {
  const [status, setStatus] = useState("connecting");
  const [liveData, setLiveData] = useState(null);
  const [logMessages, setLogMessages] = useState([]);
  const [debugVisible, setDebugVisible] = useState(false); // 👈 toggle state


  const addLog = (message) => {
    console.log(message);
    setLogMessages((prevLogs) => [
      ...prevLogs,
      `[${new Date().toLocaleTimeString()}] ${message}`,
    ]);
  };

  useEffect(() => {
    addLog("Attempting to connect to WebSocket...");

    const socket = io("https://solartrack.local", {
      path: "/socket.io",
      withCredentials: true,
      transports: ["websocket", "polling"],
    });

    socket.on("connect", () => {
      addLog("✅ Connection successful. Socket ID: " + socket.id);
      setStatus("connected");
    });

    socket.on("connect_error", (err) => {
      addLog("❌ Connection error: " + err.message);
      setStatus("error");
    });

    socket.on("disconnect", (reason) => {
      addLog("❌ Disconnected. Reason: " + reason);
      setStatus("disconnected");
    });

    socket.on("live_metering_data", (payload) => {
      addLog("📡 Live data received: " + JSON.stringify(payload));
      setLiveData(payload);
    });

    return () => {
      addLog("Cleaning up and disconnecting socket...");
      socket.disconnect();
    };
  }, []);

  return (
    <div
      className="relative min-h-screen bg-gray-100 text-gray-800 font-sans"
      style={{
        backgroundImage: `url(${kuca})`,
        backgroundSize: "contain",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
      }}
    >
      {/* Sun/Moon icon */}
    {liveData && (
    <div className="flex items-center gap-2 bg-white/80 px-3 py-1 rounded-full shadow absolute top-4 right-10">
      {liveData.is_day ? "☀️" : "🌙"} 
      <span>{liveData.current_temperature_c}°C</span>
    </div>
      )}
            {/* 🐛 Debug toggle button */}
      <button
        onClick={() => setDebugVisible((prev) => !prev)}
        className="absolute top-4 left-4 z-50 bg-yellow-300 hover:bg-yellow-400 px-2 py-1 rounded-full shadow-md text-xl"
        title="Toggle Debug Panel"
      >
        🐛
      </button>

      {/* Debug Panel */}
      {debugVisible && (
        <div className="absolute top-14 left-4 bg-white/90 p-4 rounded shadow-lg max-w-sm z-40">
          <h2 className="text-lg font-bold">Live Metering Debugger</h2>
          <p>
            Status:{" "}
            <span
              className={`font-semibold ${
                status === "connected"
                  ? "text-green-500"
                  : status === "connecting"
                  ? "text-yellow-500"
                  : "text-red-500"
              }`}
            >
              {status}
            </span>
          </p>
          <div className="mt-2 max-h-40 overflow-y-auto text-sm font-mono">
            {logMessages.map((log, i) => (
              <p key={i}>{log}</p>
            ))}
          </div>
        </div>
      )}

      {liveData && (
        <>
          {/* Solar Production bubble */}
          <div
            className={`absolute flex flex-col items-center justify-center border-[6px] border-green-500 bg-white text-xs font-bold text-gray-900 shadow-lg ${
              liveData.solar_production_kw > 0 ? "pulse" : ""
            }`}
            style={{
              top: "10%",
              left: "45%",
              width: "200px",
              height: "200px",
              borderRadius: "50%",
              textAlign: "center",
            }}
          >
            <span className="block text-xl">{liveData.solar_production_kw} kW</span>
            <span className="block text-[10px]">Solar Production</span>

          </div>

          {/* Household Consumption bubble */}
          <div
            className={`absolute flex flex-col items-center justify-center border-[4px] border-blue-500 bg-white text-xs font-bold text-gray-900 shadow-lg ${
              liveData.household_consumption_kw > 0 ? "pulse" : ""
            }`}
            style={{
              top: "80%", // adjust to match house position
              left: "47%",
              width: "140px",
              height: "140px",
              borderRadius: "50%",
              textAlign: "center",
              boxShadow: "0px 0px 15px rgba(0, 128, 255, 0.5)",
            }}
          >
            <span className="text-2xl">🏠</span>
            <span className="text-sm">House Consumption</span>
            <span className="text-lg">{liveData.household_consumption_kw} kW</span>
          </div>

          {/* Battery Charge */}
          <div
            className={`absolute top-[50%] left-[78%] px-3 py-2 rounded-lg text-sm font-bold shadow-lg border
              ${liveData.battery_charge_percentage > 50
                ? "bg-green-500/90 text-white border-green-700"
                : liveData.battery_charge_percentage > 20
                ? "bg-yellow-400/90 text-black border-yellow-600"
                : "bg-red-500/90 text-white border-red-700"
              }`}
          >
            🔋 {liveData.battery_charge_percentage}%
          </div>

          {/* Battery Flow */}
          <div
            className={`absolute top-[58%] left-[78%] px-3 py-2 rounded-lg text-sm font-bold shadow-lg border
              ${liveData.battery_flow_kw > 0
                ? "bg-purple-400/90 text-black border-purple-600"
                : "bg-gray-300 text-black border-gray-500"
              }`}
          >
            🔄 {liveData.battery_flow_kw} kW
          </div>

          {/* Grid Contribution bubble */}
          <div
            className={`absolute flex flex-col items-center justify-center border-[4px] border-orange-500 bg-white text-xs font-bold text-gray-900 shadow-lg ${
              liveData.grid_contribution_kw > 0 ? "pulse" : ""
            }`}
            style={{
              top: "25%",
              left: "20%",
              width: "140px",
              height: "140px",
              borderRadius: "50%",
              textAlign: "center",
              boxShadow: "0px 0px 15px rgba(255, 165, 0, 0.5)",
            }}
          >
            <span className="text-2xl">⚡</span>
            <span className="text-sm">Grid Contribution</span>
            <span className="text-lg">{liveData.grid_contribution_kw} kW</span>
          </div>



          {/* Timestamp */}
          <div className="absolute bottom-4 right-4 bg-gray-800/80 text-white text-xs px-3 py-1 rounded">
            Last update: {new Date(liveData.timestamp).toLocaleString()}
          </div>

          {/* Legend */}
          <div className="absolute top-20 right-4 bg-white/90 border border-gray-300 rounded-lg shadow-lg p-4 text-sm max-w-xs">
            <h3 className="font-bold text-gray-800 mb-2">Legend</h3>
            <ul className="space-y-1 text-gray-700">
              <li>
                <span className="font-bold text-orange-500">⚡ Grid Contribution</span>  
                <br />
                Positive → Importing power from grid  
                <br />
                Negative → Exporting power to grid
              </li>
              <li>
                <span className="font-bold text-green-500">🔋 Battery %</span> → Charge level
              </li>
              <li>
                <span className="font-bold text-purple-500">🔄 Battery Flow</span> → Positive means charging, negative means discharging
              </li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
