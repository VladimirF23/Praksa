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