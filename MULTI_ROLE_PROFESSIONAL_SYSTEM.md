# 🏥 Multi-Role Professional System - Backend Setup Complete

## Database Configuration
✅ **Using: MongoDB** (Not SQLite)
- Collections already configured in `/app/database/mongo.py`
- All role-based collections ready for use

## New Entities Added

### 1. **Psychiatrist** (Existing - Medical Professional)
- Can prescribe medications
- Medical degree required
- Highest consultation fee

### 2. **Mentor** (New - Personal Coach)
- Career and personal growth coaching
- Experience-based qualifications
- Moderate consultation fee (₹500)
- Handles: Career, personal growth, confidence, relationships

### 3. **Business Coach** (New - Business Expert)
- Startup and business guidance
- Specialized business expertise
- Higher consultation fee (₹1000)
- Handles: Startup, scaling, marketing, sales, finance

### 4. **Buddy** (New - Support Companion)
- Peer support and companionship
- Lower consultation fee (₹200)
- Handles: Loneliness, motivation, social support

## MongoDB Collections

```
mental_health
├── psychiatrists
├── mentors
├── business_coaches
├── buddies
├── appointments
├── chats
├── rooms
└── ... (other existing collections)
```

## Schema Files Created

1. **`app/models/mentor_schema.py`**
   - MentorBase, MentorCreate, MentorUpdate, MentorResponse

2. **`app/models/business_coach_schema.py`**
   - BusinessCoachBase, BusinessCoachCreate, BusinessCoachUpdate, BusinessCoachResponse

3. **`app/models/buddy_schema.py`**
   - BuddyBase, BuddyCreate, BuddyUpdate, BuddyResponse

## New API Endpoints

### Base: `/api/professionals`

### 1. **Get All Professionals**
```
GET /api/professionals/all
Query Parameters:
  - role: psychiatrist | mentor | business_coach | buddy (optional)
  - status: online | offline | emergency (optional)
  - problem_type: love_problems | marriage_problems | breakup | etc. (optional)
  - skip: pagination (default: 0)
  - limit: pagination (default: 10)

Response:
{
  "success": true,
  "message": "All professionals retrieved",
  "professionals": {
    "psychiatrist": {
      "label": "Psychiatrists (Medical professionals)",
      "count": 5,
      "data": [...]
    },
    "mentor": {
      "label": "Mentors (Personal coaches)",
      "count": 10,
      "data": [...]
    },
    ...
  }
}
```

### 2. **Get Professionals by Status**
```
GET /api/professionals/by-status/{status}
Path Parameters:
  - status: online | offline | emergency

Query Parameters:
  - role: (optional) filter by specific role
  - skip: pagination
  - limit: pagination

Status Mapping:
  - online → availability: "available"
  - offline → availability: "offline"
  - emergency → availability: "emergency"
```

### 3. **Get Professionals by Problem Type**
```
GET /api/professionals/by-problem/{problem_type}
Path Parameters:
  - problem_type: love_problems, marriage_problems, breakup, divorce, business, career, depression, anxiety, etc.

Query Parameters:
  - role: (optional)
  - status: (optional)
  - skip: pagination
  - limit: pagination
```

### 4. **Get Professional Statistics**
```
GET /api/professionals/stats/summary

Response:
{
  "success": true,
  "stats": {
    "psychiatrist": {
      "total": 50,
      "online": 15,
      "offline": 30,
      "emergency": 5
    },
    "mentor": {
      "total": 100,
      "online": 40,
      "offline": 55,
      "emergency": 5
    },
    ...
  }
}
```

## Availability Status

Each professional has a status indicator:

| Status | Color | Meaning |
|--------|-------|---------|
| **Online** | 🟢 Green | Available for consultation now |
| **Offline** | ⚫ Gray | Not currently available |
| **Emergency** | 🔴 Red | In emergency mode (limited availability) |

## Problem Categories Supported

- Love Problems
- Marriage Problems
- Breakup Problems
- Divorce Problems
- Business Problems
- Career Issues
- Depression
- Anxiety
- Relationship Issues
- Family Problems

## Updated Role Enum

```python
class RoleEnum(CaseInsensitiveEnum):
    doctor = "doctor"
    psychiatrist = "psychiatrist"
    counselor = "counselor"
    mentor = "mentor"
    business_coach = "business_coach"
    buddy = "buddy"
    user = "user"
    admin = "admin"
```

## How to Use in Flutter

### 1. **Fetch All Professionals by Role**
```dart
// Get all psychiatrists
GET /api/professionals/all?role=psychiatrist

// Get all mentors
GET /api/professionals/all?role=mentor

// Get all business coaches
GET /api/professionals/all?role=business_coach

// Get all buddies
GET /api/professionals/all?role=buddy
```

### 2. **Fetch by Status**
```dart
// Get all online professionals
GET /api/professionals/by-status/online

// Get all psychiatrists who are online
GET /api/professionals/by-status/online?role=psychiatrist

// Get mentors in emergency mode
GET /api/professionals/by-status/emergency?role=mentor
```

### 3. **Fetch by Problem Type**
```dart
// Get all professionals handling breakup problems
GET /api/professionals/by-problem/breakup

// Get mentors for career issues
GET /api/professionals/by-problem/career_issues?role=mentor

// Get business coaches for business problems and filter online
GET /api/professionals/by-problem/business_problems?role=business_coach&status=online
```

## Integration Steps

1. ✅ Added new roles to RoleEnum
2. ✅ Created schema files for Mentor, BusinessCoach, and Buddy
3. ✅ Created MongoDB collections in mongo.py
4. ✅ Created professionals_routes.py with unified API endpoints
5. ✅ Added router to main.py

## Next Steps

1. **Flutter Frontend Updates:**
   - Update psychiatrist_search_screen.dart to fetch from `/api/professionals/all?role=psychiatrist`
   - Create unified professional search that shows all roles
   - Add role filters and status indicators

2. **Test the Endpoints:**
   - Use Postman to test all new endpoints
   - Verify status indicators work correctly
   - Test problem type filtering

3. **Add Professional Registration:**
   - Create registration endpoints for Mentor, BusinessCoach, Buddy roles
   - Add validation for each role type

## Testing API Endpoints

```bash
# Get all professionals
curl http://localhost:8000/api/professionals/all

# Get only psychiatrists
curl http://localhost:8000/api/professionals/all?role=psychiatrist

# Get online professionals
curl http://localhost:8000/api/professionals/by-status/online

# Get professionals handling breakup problems
curl http://localhost:8000/api/professionals/by-problem/breakup

# Get statistics
curl http://localhost:8000/api/professionals/stats/summary
```

---

**Status:** ✅ Backend ready for multi-role professional system
**Database:** MongoDB
**API Version:** 1.0
