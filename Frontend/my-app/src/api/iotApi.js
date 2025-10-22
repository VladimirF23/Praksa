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