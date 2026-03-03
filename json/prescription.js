const prescription = {
  // Patient details (link to patient profile)
  patientId: "PAT001",

  // Prescriber details (doctor or counselor)
  prescribedBy: {
    userId: "DOC1001",
    role: "doctor", // or "counselor"
  },

  // Prescription date (YYYY-MM-DD)
  date: "2025-08-22",

  // List of prescribed medicines
  medicines: [
    {
      medicineName: "Paracetamol",
      dosage: "500mg - twice a day",
      notes: "Take after meals",
    },
    {
      medicineName: "Amoxicillin",
      dosage: "250mg - thrice a day",
      notes: "Complete full course",
    },
  ],

  // Metadata
  createdBy: {
    userId: "DOC1001", // who created the prescription
    role: "",
  },
  updatedBy: {
    userId: "DOC1001", // last user who modified it
    role: "",
  },

  // Timestamps
  createdAt: "2025-08-22T10:30:00Z",
  updatedAt: "2025-08-22T10:45:00Z",
};

// 📌 Prescription API Endpoints
// Create a new prescription

// POST /api/prescriptions

// Get all prescriptions

// GET /api/prescriptions

// Get all prescriptions of a patient

// GET /api/prescriptions/patient/:patientId

// Get a specific prescription by ID

// GET /api/prescriptions/:id

// Update a prescription

// PUT /api/prescriptions/:id

// Delete a prescription

// DELETE /api/prescriptions/:id
