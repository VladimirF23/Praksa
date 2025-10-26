import axiosInstance from "../api/axiosInstance";

export const addBatteryApi = async (batteryData) => {
     // API call returns the newly added battery object
    const response = await axiosInstance.post('/api/battery/add', batteryData);
    return response.data.battery; // EXPECTING: { ..., battery: { model_name: '...', ... } }
};

export const deleteBatteryApi = async (batteryId, systemId) => { // MODIFIED to accept IDs
      // API call returns success status, we dispatch null
    const response = await axiosInstance.post('/api/battery/delete', {
        battery_id: batteryId,
        solar_system_id: systemId // Include both IDs in the request body
    });
    return response.data; // EXPECTING: { message: "Battery deleted" }
};