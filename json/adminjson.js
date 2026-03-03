// ---

// ## 🔐 AUTH

// ### ✅ POST `/api/auth/login` – Login

```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "username": "admin",
    "role": ["admin", "user", "counselor", "doctor"],
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
``` // ### ✅ POST `/api/auth/register` – Register
```json
{
  "status": 201,
  "message": "User registered successfully",
  "data": {
    "fullName": "Admin User",
    "role": ["admin", "user", "counselor", "doctor"],
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "phoneNumber": "1234567890",
    "gender": ["male", "female", "other"],
    "dob": "1990-01-01",
    "terms_conditions": true
  }
}
``` // * ### ✅ DELETE `/api/assessments/:id` // * ### ✅ PUT `/api/assessments/:id` // * ### ✅ GET `/api/assessments/:id` // * ### ✅ POST `/api/assessments` // ## 📋 ASSESSMENTS // ---
```json
{
  "status": 201,
  "message": "Assessment created",
  "data": {
    "id": "assessment123",
    "disease": ["Depression", "Anxiety", "Stress"],
    "age_group": "18-25",
    "question": "What is your current mood?",
    "options": ["Happy", "Sad", "Neutral"]
  }
}
``` // * ### ✅ DELETE `/api/patients/:id` // * ### ✅ PUT `/api/patients/:id` // * ### ✅ GET `/api/patients/:id` // * ### ✅ POST `/api/patients` // ## 🧑 PATIENTS // ---
```json
{
  "status": 200,
  "message": "Patient fetched successfully",
  "data": {
    "firstName": "John",
    "lastName": "Doe",
    "dob": "1995-05-20",
    "gender": "male",
    "age": 30,
    "mobileNumber": "9876543210",
    "email": "john@example.com",
    "address": "123 Main Street",
    "maritalStatus": "single",
    "blood_group": "O+",
    "picture": "https://example.com/patient.jpg"
  }
}
``` // * ### ✅ DELETE `/api/doctors/:id` // * ### ✅ PUT `/api/doctors/:id` // * ### ✅ GET `/api/doctors/:id` // * ### ✅ POST `/api/doctors` // ## 🧑‍⚕️ DOCTORS // ---
```json
{
  "status": 200,
  "message": "Doctor fetched successfully",
  "data": {
    "firstName": "Jane",
    "lastName": "Smith",
    "username": "jane.smith",
    "email": "jane@example.com",
    "dob": "1985-10-01",
    "mobileNumber": "1234567890",
    "education": "MBBS",
    "designation": "Psychiatrist",
    "department": "Mental Health",
    "gender": "female",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "postalCode": "10001",
    "specialization": ["Psychiatry"],
    "experience": "5 years",
    "joiningDate": "2023-10-01",
    "picture": "https://example.com/doctor.jpg"
  }
}
``` // * ### ✅ DELETE `/api/departments/:id` // * ### ✅ PUT `/api/departments/:id` // * ### ✅ GET `/api/departments/:id` // * ### ✅ POST `/api/departments` // ## 🏥 DEPARTMENTS // ---
```json
{
  "status": 201,
  "message": "Department created",
  "data": {
    "department": "Psychiatry",
    "departmentHead": "Dr. Jane Smith",
    "description": "Deals with mental health issues",
    "status": "active"
  }
}
``` // * ### ✅ DELETE `/api/counseling/:id` // * ### ✅ PUT `/api/counseling/:id` // * ### ✅ GET `/api/counseling/:id` // * ### ✅ POST `/api/counseling` // ## 📆 COUNSELING / APPOINTMENTS // ---
```json
{
  "status": 201,
  "message": "Counseling session booked",
  "data": {
    "patientName": "John Doe",
    "counsellor": "Jane Smith",
    "date": "2023-10-01",
    "time": "10:00 AM",
    "sessionType": "Initial",
    "mode": "Online",
    "notes": "First consultation",
    "status": "scheduled",
    "payment": "Paid",
    "rating": 5
  }
}
``` // * ### ✅ DELETE `/api/payments/:id` // * ### ✅ PUT `/api/payments/:id` // * ### ✅ GET `/api/payments/:id` // * ### ✅ POST `/api/payments` // ## 💳 PAYMENTS // ---
```json
{
  "status": 201,
  "message": "Payment recorded successfully",
  "data": {
    "admissionID": "ADM12345",
    "sessionType": "Therapy",
    "patient": "John Doe",
    "counsellor": "Dr. Jane Smith",
    "status": "paid",
    "tax": 0.05,
    "discount": 0.1,
    "amount": 100,
    "date": "2023-10-01"
  }
}
``` // * ### ✅ DELETE `/api/notifications/:id` // * ### ✅ PUT `/api/notifications/:id` // * ### ✅ GET `/api/notifications` // * ### ✅ POST `/api/notifications` // ## 🔔 NOTIFICATIONS // ---
```json
{
  "status": 200,
  "message": "Notifications fetched successfully",
  "data": [
    {
      "id": "notif_1",
      "title": "You have new order!",
      "description": "Are you going to meet me tonight?",
      "time": "9 hours ago",
      "type": "info",
      "userId": "user_101",
      "username": "john_doe",
      "role": "patient"
    },
    ...
  ]
}
``` // ## ❌ ERROR RESPONSE FORMAT (Standard) // ---
```json
{
  "status": 400,
  "message": "Validation error",
  "error": {
    "code": "FIELD_MISSING",
    "details": "Field 'email' is required"
  }
}
``` // ## ✅ ENUM REFERENCES // ---
```ts
// Gender Enum
enum Gender {
  "male",
  "female",
  "other"
}

// Role Enum
enum Role {
  "admin",
  "user",
  "doctor",
  "counselor"
}

// Appointment Status Enum
enum AppointmentStatus {
  "scheduled",
  "pending",
  "completed",
  "cancelled"
}

// Payment Status Enum
enum PaymentStatus {
  "Paid",
  "Pending",
  "Unpaid"
}

// Notification Type Enum
enum NotificationType {
  "info",
  "success",
  "danger",
  "warning"
}
```;

// Dashboard

// API - GET DashBoard Statitics
const dashStatics = {
  statistics: [
    {
      label: "Total Patients",
      value: 56,
      change: "+25% Increased",
    },
    {
      label: "Daily Active Patients",
      value: 15,
      change: "+15% Increased",
    },
    {
      label: "Daily Less Active Patients",
      value: 23,
      change: "-4% Decreased",
    },
    {
      label: "Total Doctors",
      value: 75,
      change: "+10% Increased",
    },
    {
      label: "Daily Active Doctors",
      value: 35,
      change: "+7% Increased",
    },
    {
      label: "Daily Less Active Doctors",
      value: 40,
      change: "-12% Decreased",
    },
    {
      label: "Total Consultations",
      value: 31,
      change: "+6% Increased",
    },
    {
      label: "Daily Active Counsellors",
      value: 21,
      change: "+8% Increased",
    },
    {
      label: "Daily Less Active Counsellors",
      value: 10,
      change: "-2% Decreased",
    },
    {
      label: "Total Earnings",
      value: "₹34,500",
      change: "+5% Increased",
    },
    {
      label: "Repeated Patients",
      value: 23,
      change: "+12% Increased",
    },
  ],
};

// API - GET => Patients INfo for Graph
const dash = {
  patients: {
    // info for charts show
  },
  patientsByDepartment: [
    {
      department: "Psychiatry",
      patients: 45,
    },
    {
      department: "Psychology",
      patients: 38,
    },
    {
      department: "Neurology",
      patients: 30,
    },
  ],
  earningsByDepartment: [
    {
      department: "Psychiatry",
      percentage: 50,
    },
    {
      department: "Psychology",
      percentage: 30,
    },
    {
      department: "Neurology",
      percentage: 20,
    },
  ],
};
