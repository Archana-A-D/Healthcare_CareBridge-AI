import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

export const uploadDischargeSummary = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post(
    "/discharge-summaries/upload/",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );

  return response.data;
};

export const getDischargeSummary = async (summaryId) => {
  const response = await apiClient.get(
    `/discharge-summaries/${summaryId}/`
  );

  return response.data;
};

export const askQuestion = async (summaryId, question) => {
  const response = await apiClient.post(
    `/discharge-summaries/${summaryId}/ask/`,
    {
      question
    }
  );

  return response.data;
};