// Doctors Registration or counseller
// ### ✅ POST `/api/auth/register` – Register
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
  "language":["hindi","marathi","english"]
}
``` // ### ✅ POST `/api/auth/register` – Register // User register //
```json
{
  "status": 201,
  "message": "User registered successfully",
  "data": {
    "fullName": "rohan chougule",
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
```;

// ### ✅ POST `/api/auth/login` – login // User,admin,doctor,counsellor //
```json
{
  "status": 201,
  "message": "User logged",
  "data": {
    "username":"username123",
    "role": ["admin", "user", "counselor", "doctor"],
    "password": "admin123",
    "terms_conditions": true
  }
}
```;
