```
{
  "role": "Doctor",
  "fullName": "Dr. Rajesh Kumar",
  "email": "rajesh.kumar@example.com",
  "password": "********",
  "phoneNumber": "9876543210",
  "gender": "Male",
  "dateOfBirth": "1985-03-15",
  "qualification": "MBBS, MD (Psychiatry)",
  "specialization": "Clinical Psychiatry",
  "experienceYears": 12,
  "licenseNumber": "DL-MED-56789",
  "shortBio": "Board-certified psychiatrist with over 12 years of clinical experience in treating mood disorders and anxiety.",
  "consultationMode": ["Both", "Online", "In-person"],
  "profilePhoto": "https://example.com/uploads/rajesh-doctor.jpg",
  "termsAccepted": true
}
``` // ### 🔸 JSON Format: // ## ✅ 1. ToDo // --
```json
{
  "id": "todo_001",
  "patientName": "John Doe",
  "taskDate": "2023-10-01",
  "taskName": "Follow-up"
}
```// --- // | DELETE | `/api/todos/:id` | Delete task     | // | PUT    | `/api/todos/:id` | Update task     | // | POST   | `/api/todos`     | Create new task | // | GET    | `/api/todos/:id` | Get task by ID  | // | GET    | `/api/todos`     | Get all tasks   | // | ------ | ---------------- | --------------- | // | Method | Endpoint         | Description     | // ### 🔸 Endpoints:

// ## ✅ 2. Patient

// ### 🔸 JSON Format:

```json
{
  "id": "patient_001",
  "name": "John",
  "age": 30, 
  "gender": "",
  "bloodGroup": "A+",
  "diagnosis": "",
  "lastVisit": "2023-10-01",
  "status": "active",
  "picture": "https://example.com/patient.jpg",
  "address": "",
  "mobileNumber": "9876543210",
  "email": ""
}
```// --- // | DELETE | `/api/patients/:id` | Delete patient         | // | PUT    | `/api/patients/:id` | Update patient details | // | POST   | `/api/patients`     | Create new patient     | // | GET    | `/api/patients/:id` | Get patient by ID      | // | GET    | `/api/patients`     | Get all patients       | // | ------ | ------------------- | ---------------------- | // | Method | Endpoint            | Description            | // ### 🔸 Endpoints:

// ## ✅ 3. Prescription

// ### 🔸 JSON Format:

```json
{
  "id": "presc_001",
  "patientName": "John Doe",
  "doctorName": "Dr. Jane Smith",
  "medicineName": "Paracetamol",
  "dosage": "500mg",
  "notes": "Take after meals",
  "frequency": "Twice a day",
  "date": "2023-10-01"
}
```// --- // | DELETE | `/api/prescriptions/:id` | Delete prescription    | // | PUT    | `/api/prescriptions/:id` | Update prescription    | // | POST   | `/api/prescriptions`     | Create prescription    | // | GET    | `/api/prescriptions/:id` | Get prescription by ID | // | GET    | `/api/prescriptions`     | Get all prescriptions  | // | ------ | ------------------------ | ---------------------- | // | Method | Endpoint                 | Description            | // ### 🔸 Endpoints:

// ## ✅ 4. Chat

// ### 🔸 JSON Format:

```json
{
  "id": "chat_001",
  "patientName": "John Doe",
  "doctorName": "Dr. Jane Smith",
  "chatHistory": [
    {
      "messageId": "msg_001",
      "senderId": "user123",
      "receiverId": "doctor456",
      "message": "Hello, I need help with my mental health.",
      "timestamp": "2023-10-01T10:00:00Z",
      "status": ["sent", "delivered", "read"]
    }
  ]
}
```// --- // | DELETE | `/api/chats/:id` | Delete chat record         | // | PUT    | `/api/chats/:id` | Update chat history        | // | POST   | `/api/chats`     | Create new chat record     | // | GET    | `/api/chats/:id` | Get single chat by ID      | // | GET    | `/api/chats`     | Get all chat conversations | // | ------ | ---------------- | -------------------------- | // | Method | Endpoint         | Description                | // ### 🔸 Endpoints:

// ## ✅ 5. Earnings

// ### 🔸 JSON Format:

```json
{
  "id": "earn_001",
  "patient": "John Doe",
  "duration": "1 hour",
  "rate": "₹100",
  "total": "₹600",
  "commission": "₹60",
  "netPayout": "₹540",
  "status": "paid",
  "date": "2023-10-01"
}
```; // ### 🔸 Endpoints:

// | Method | Endpoint            | Description            |
// | ------ | ------------------- | ---------------------- |
// | GET    | `/api/earnings`     | Get all earnings       |
// | GET    | `/api/earnings/:id` | Get earnings by ID     |
// | POST   | `/api/earnings`     | Create earnings record |
// | PUT    | `/api/earnings/:id` | Update earnings        |
// | DELETE | `/api/earnings/:id` | Delete earnings record |
