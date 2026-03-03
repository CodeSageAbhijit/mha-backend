# 📋 Complete Backend API Endpoints Reference

## Backend Running: ✅ http://localhost:8080

---

## 🔐 Authentication Endpoints (`/api`)

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---|
| POST | `/register` | Register new user | ❌ No |
| POST | `/login` | User login | ❌ No |
| POST | `/logout` | User logout | ✅ Yes |
| POST | `/forgot-password` | Request password reset | ❌ No |
| GET | `/reset-password` | Password reset form | ❌ No |
| POST | `/reset-password` | Reset password | ❌ No |
| POST | `/token/refresh` | Refresh JWT token | ✅ Yes |

---

## 👥 User Management

### Patient Routes (`/api/patient`)
- `POST /` - Register patient
- `GET /{id}` - Get patient details
- `PUT /{id}` - Update patient info

### Doctor Routes (`/api/doctor`)
- `GET /` - List all doctors
- `GET /{id}` - Get doctor details
- `POST /` - Register doctor
- `PUT /{id}` - Update doctor info

### Counselor Routes (`/api/counselor`)
- `GET /` - List counselors
- `GET /history/{counselorId}` - Get counselor history
- `GET /sessions` - Get counselor sessions

### Admin Routes (`/api/admin`)
- `PUT /update-profile` - Update admin profile
- `GET /` - Admin dashboard
- `GET /users` - List all users

---

## 📅 Appointment Management

### Appointment Routes (`/api/appointment`)
- `GET /` - Get appointments
- `POST /` - Book appointment
- `PUT /{id}` - Reschedule appointment
- `DELETE /{id}` - Cancel appointment
- `GET /{id}` - Get appointment details

### Appointment Request Routes (`/api/appointment-request`)
- `GET /` - List appointment requests
- `POST /` - Create appointment request
- `PUT /{id}` - Update request
- `DELETE /{id}` - Cancel request

---

## 💬 Communication

### Chat/Messaging (`/socket.io`)
- Real-time chat via Socket.IO
- Connected to MongoDB for message storage
- Supports multiple participants

---

## 💳 Payment & Wallet

### Payment Routes (`/api/payment`)
- `POST /` - Create payment
- `GET /` - Get payments
- `PUT /{id}` - Update payment
- `DELETE /{id}` - Cancel payment

### Wallet Routes (`/api/wallet`)
- `GET /balance` - Get wallet balance
- `GET /transactions` - Get transaction history
- `POST /add-funds` - Add funds to wallet
- `POST /withdraw` - Withdraw from wallet

---

## ⭐ Reviews & Ratings

### Review Routes (`/api/review`)
- `GET /` - List reviews
- `POST /` - Create review
- `PUT /{id}` - Update review
- `DELETE /{id}` - Delete review
- `GET /doctor/{doctorId}` - Get reviews for doctor

---

## 🏥 Medical Records

### Prescription Routes (`/api/prescription`)
- `POST /` - Create prescription
- `GET /` - List prescriptions
- `PUT /{id}` - Update prescription
- `DELETE /{id}` - Delete prescription

### Medicine Routes (`/api/medicine`)
- `GET /` - List medicines
- `POST /` - Add medicine
- `PUT /{id}` - Update medicine
- `DELETE /{id}` - Delete medicine

### Assessment Routes (`/api/assessment`)
- `POST /` - Create assessment
- `GET /` - Get assessments
- `PUT /{id}` - Update assessment

---

## 🏥 Room & Video Management

### Room Routes (`/api/room`)
- `GET /` - List rooms
- `POST /` - Create room
- `GET /{id}` - Get room details
- `DELETE /{id}` - Delete room

### Call/Meet Routes (`/api/call` or `/api/meet`)
- `GET /` - Get call history
- `POST /` - Start call
- `PUT /{id}` - Update call status
- `DELETE /{id}` - End call

### Google Meet Routes (`/api/googlemeet`)
- Integration with Google Meet for video consultations

### Video Call History (`/api/video-call-history`)
- `GET /` - Get video call history
- `POST /` - Log video call
- `GET /{id}` - Get specific call details

---

## 💼 Department Routes

### Departments (`/api/department`)
- `GET /` - List departments
- `POST /` - Create department
- `PUT /{id}` - Update department
- `DELETE /{id}` - Delete department

---

## 📊 Availability Management

### Doctor Availability (`/api/doctor_availability`)
- `GET /` - Get doctor availability
- `POST /` - Set availability
- `PUT /{id}` - Update availability
- `DELETE /{id}` - Remove availability

### Counselor Availability (`/api/counselor_availability`)
- `GET /` - Get counselor availability
- `POST /` - Set availability
- `PUT /{id}` - Update availability
- `DELETE /{id}` - Remove availability

---

## 💰 Earnings & Reports

### Doctor Earnings (`/api/doctor/earnings`)
- `GET /` - Get doctor earnings
- `GET /monthly` - Get monthly earnings
- `GET /yearly` - Get yearly earnings

### Counselor Earnings (`/api/counselor/earnings`)
- `GET /` - Get counselor earnings
- `GET /monthly` - Get monthly earnings
- `GET /yearly` - Get yearly earnings

### Admin History (`/api/admin/history`)
- `GET /` - Get admin action history
- `GET /user/{userId}` - Get user's history
- `GET /date-range` - Get history for date range

### Doctor History (`/api/doctor/history`)
- `GET /` - Get doctor's action history

### Counselor History (`/api/counselor/history`)
- `GET /` - Get counselor's action history

---

## 📍 Address Management

### Address Routes (`/api/address`)
- `GET /` - Get addresses
- `POST /` - Add address
- `PUT /{id}` - Update address
- `DELETE /{id}` - Delete address

---

## 💊 Consultation Rates

### Consultation Rate Routes (`/api/consultation-rates`)
- `POST /{provider_type}/set` - Set consultation rate
- `GET /{provider_type}/rates/{provider_id}` - Get rates
- `GET /{provider_type}/list` - List all rates

---

## 🔑 Additional Routes

### Status Routes (`/api/status`)
- `GET /` - Get system status
- `GET /health` - Health check

### Return Response (`/api/response`)
- Standard response format validation

### Reset Password (`/api/reset-password`)
- Reset password functionality

### Google Authentication (`/api/google`)
- Google OAuth integration

---

## 🔐 Authentication Headers Required

For protected endpoints, include:
```
Authorization: Bearer <JWT_TOKEN>
```

### How to Get Token:
```bash
POST /api/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123",
  "role": "patient"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## 📝 Request Format

### Most Endpoints Accept:
```
Content-Type: application/json
```

### Special Cases:
- **Register**: `multipart/form-data` (supports file upload)
- **File Uploads**: `multipart/form-data`

---

## 🎯 Response Format

### Success Response (2xx):
```json
{
  "success": true,
  "status": 200,
  "message": "Success message",
  "data": { /* actual data */ }
}
```

### Error Response (4xx/5xx):
```json
{
  "success": false,
  "status": 400,
  "message": "Error message",
  "error": "Error type",
  "errors": [
    {
      "field": "fieldName",
      "message": "Field error",
      "type": "validation"
    }
  ]
}
```

---

## 🚀 Total API Routes: 33+ Routers with 100+ Endpoints

**Status**: ✅ All routers loaded and responding  
**Database**: ✅ MongoDB connected with 30+ collections  
**Real-time**: ✅ Socket.IO active for chat  
**Security**: ✅ JWT authentication, Rate limiting, CORS

---

Generated: 2025-01-08  
Last Updated: Backend Testing Phase  
Environment: Development (localhost:8080)
