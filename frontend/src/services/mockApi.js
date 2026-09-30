import dischargeSummary from "../mocks/dischargeSummary.json";

// Simulates loading the discharge summary from the backend
export const getDischargeSummary = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(dischargeSummary);
    }, 500);
  });
};

// Simulates uploading a discharge summary
export const uploadDischargeSummary = async (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        summaryId: dischargeSummary.id,
        fileName: file?.name || "discharge-summary.pdf",
        message: "Discharge summary uploaded successfully."
      });
    }, 1000);
  });
};

// Simulates asking a question about the discharge summary
export const askQuestion = async (question) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const lowerQuestion = question.toLowerCase();

      if (lowerQuestion.includes("medicine")) {
        resolve({
          answer: "The discharge summary mentions 3 medicines.",
          sources: [
            {
              page: 2,
              section: "Medications"
            }
          ]
        });
        return;
      }

      if (lowerQuestion.includes("follow")) {
        resolve({
          answer: "The follow-up is scheduled for 4 October 2024.",
          sources: [
            {
              page: 3,
              section: "Follow-up"
            }
          ]
        });
        return;
      }

      resolve({
        answer:
          "I could not find a specific answer to that question in the uploaded discharge summary.",
        sources: []
      });
    }, 800);
  });
};
