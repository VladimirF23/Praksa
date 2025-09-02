import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";
import kuca from "./kuca.png";
import "./pulse.css"; // pulse animation
import { useSelector,useDispatch } from "react-redux";
import { updateIotDeviceState  } from "../api/iotApi";
import { toggleIotDevice,setIotDevices } from "../features/authorization/authSlice"; 


export default function LiveMetering() {
  const [status, setStatus] = useState("connecting");
  const [liveData, setLiveData] = useState(null);
  const [logMessages, setLogMessages] = useState([]);
  const [debugVisible, setDebugVisible] = useState(false); //  toggle state
  const dispatch = useDispatch();

  const [notification, setNotification] = useState({ visible: false, message: "" });



  const iotDevices = useSelector((state) => state.auth.iotDevices || []);


const toggleDevice = async (device) => {
  try {
    const newStatus = device.current_status === "on" ? "off" : "on"; // flip state
    
    await updateIotDeviceState(device.device_id, newStatus); // send "on"/"off"

    // update Redux state
    dispatch(toggleIotDevice({ deviceId: device.device_id, status: newStatus }));
  } catch (err) {
    console.error("Failed to toggle device", err);
  }
};


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

      if (payload.iot_devices_data) {
      // overwrite Redux with fresh device states from backend
      dispatch(setIotDevices(payload.iot_devices_data));
      }

      //alarm za IoT da se pogase svi kojini nisi critical priority i upaljeni su

      // Proveri da li postoji signal za isključivanje svih uređaja, bice None ako nema potrebe za gasenje ili ako korisnik nema IoT uredjaje ili bateriju
      if (payload.alarm_user) {
        addLog("Server je zatrazio iskljucivanje svih IoT uredjaja.");
        
        setNotification({
        visible: true,
        message: "All non-critical IoT devices will be turned off to conserve energy. 🔋"
        });

        // Automatically hide the notification after a few seconds
        setTimeout(() => {
        setNotification({ visible: false, message: "" });
        }, 5000); // 5000 milliseconds = 5 seconds

        // iotDevices.forEach(device => {
        //   if (device.current_status === "on" && device.priority_level !== "critical") {
        //     dispatch(toggleIotDevice({ deviceId: device.device_id, status: "off" }));         //u Redux-u da updejtujemo posto sam na backendu vec updejtovao
        //     addLog(`Device ${device.device_name} turned off due to not being critical priority.`);
        //   }
        // });
      }



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

      {notification.visible && (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-xl z-[100] transition-all duration-300 animate-slide-down">
        {notification.message}
    </div>
)}
      {/* Sun/Moon icon */}
    {liveData && (
    <div className="flex items-center gap-2 bg-white/80 px-3 py-1 rounded-full shadow absolute top-4 right-7">
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

          {/* Battery Loss */}
          <div
            className={`absolute top-[66%] left-[78%] px-3 py-2 rounded-lg text-sm font-bold shadow-lg border
              ${liveData.battery_loss_kw > 0
                ? "bg-red-400/90 text-black border-red-600"
                : "bg-gray-300 text-black border-gray-500"
              }`}
          >
            ⚠️ Battery Loss: {liveData.battery_loss_kw} kW
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
          <div className="absolute bottom-3 right-4 bg-gray-800/80 text-white text-xs px-3 py-1 rounded">
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
              <li>
                <span className="font-bold text-red-500">⚠️ Battery Loss</span> → Energy lost due to battery inefficiency (heat, conversion losses)
              </li>
            </ul>
          </div>




          {/* IoT Devices iz redux-a vadi IoT od korisnika*/}
          <div className="absolute bottom-[-250px] left-0 w-full bg-white/90 border-t border-gray-300 shadow-lg p-4">
            <h3 className="font-bold text-gray-800 mb-3">IoT Devices</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {iotDevices.map((device, index) => (
                <div
                  key={index}
                  className="p-4 border rounded-lg shadow-sm bg-white flex flex-col justify-between"
                >
                  <div>
                    <h4 className="text-lg font-semibold">{device.device_name}</h4>
                    <p className="text-sm text-gray-500">{device.device_type}</p>
                    <p className="text-sm">
                      Power: {device.base_consumption_watts} W
                    </p>
                    <p
                      className={`mt-1 font-bold ${
                        device.current_status === "on"
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {device.current_status.toUpperCase()}
                    </p>
                      {/* Priority Level */}
                      <p
                        className={`text-sm mt-1 font-medium ${
                          device.priority_level === "critical"
                            ? "text-red-700"
                            : device.priority_level === "medium"
                            ? "text-yellow-600"
                            : device.priority_level === "low"
                            ? "text-green-600"
                            : "text-gray-500"
                        }`}
                      >
                        Priority: {device.priority_level.replace("_", " ").toUpperCase()}
                      </p>
                  </div>
                  {device.is_smart_device && (
                    <button
                      onClick={() => toggleDevice(device)}
                      className={`mt-3 py-1 px-3 rounded ${
                        device.current_status === "on"
                          ? "bg-red-500 hover:bg-red-600 text-white"
                          : "bg-green-500 hover:bg-green-600 text-white"
                      }`}
                    >
                      {device.current_status === "on" ? "Turn Off" : "Turn On"}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      

    </div>
  );
}
