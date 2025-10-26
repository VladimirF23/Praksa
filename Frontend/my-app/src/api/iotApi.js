// iotApi.js
import axiosInstance from './axiosInstance';

// Update IoT device state
export const updateIotDeviceState = async (deviceId, isActive) => {
    try {
        const response = await axiosInstance.post('/api/iot/update-state', {
            device_id: deviceId,
            is_active: isActive
        });
        return response.data; // { message: "Device state updated successfully" }
    } catch (error) {
        console.error("DEBUG iotApi: Failed to update device state", error.response?.data || error.message);
        throw error;
    }
};

export const updateIotDevicePriority = async (deviceId, newPriority) => {
    try {
        const response = await axiosInstance.post('/api/iot/update-priority', {
            device_id: deviceId,
            new_priority: newPriority // new parameter
        });
        return response.data; // { message: "Device priority updated successfully" }
    } catch (error) {
        console.error("DEBUG iotApi: Failed to update device priority", error.response?.data || error.message);
        throw error;
    }
};


export const addIotDevice = async (deviceData) => {
    try {
        // deviceData should be a single object conforming to the API structure
        const response = await axiosInstance.post('/api/iot/add', deviceData);
        // Expecting the backend to return the newly added device or an updated list
        return response.data; // e.g., { message: "Device added successfully", new_device: {...} } or { devices: [...] }
    } catch (error) {
        console.error("DEBUG iotApi: Failed to add new device", error.response?.data || error.message);
        throw error;
    }
};

// Function to delete an existing IoT device
export const deleteIotDevice = async (deviceId) => {
    try {
        const response = await axiosInstance.post('/api/iot/delete', {
            device_id: deviceId
        });
        // Expecting the backend to return an updated list of devices
        return response.data; // e.g., { message: "Device deleted successfully", devices: [...] }
    } catch (error) {
        console.error("DEBUG iotApi: Failed to delete device", error.response?.data || error.message);
        throw error;
    }
};