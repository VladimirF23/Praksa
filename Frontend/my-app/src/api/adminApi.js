// src/api/adminApi.js
import axiosInstance from "./axiosInstance";

// Fetch all users (admin only)
export const fetchAllUsers = async () => {
  const response = await axiosInstance.get("/api/auth/admin_getUsers");
  return response.data.users;
};

// Update approval status
export const updateUserApproval = async (systemId, approvedStatus) => {
  const response = await axiosInstance.put("/api/auth/admin_updateApproval", {
    system_id: systemId,
    approved: approvedStatus,
  });
  return response.data;
};
