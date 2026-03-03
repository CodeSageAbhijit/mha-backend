// Dashborad Showing APIs

// PAtient Visit history

const patientVisitHistory = [
  {
    doctor: "",
    date: "2023-10-01",
    department: "Psychiatry",
    fee: "500",
    status: "completed",
    reports: {
      clinicalReports: "https://example.com/reports/clinical-report.pdf",
      dentistReports: "https://example.com/reports/dentist-report.pdf",
      glucoseReports: "https://example.com/reports/glucose-report.pdf",
      x_ray: "https://example.com/reports/x-ray-report.pdf",
      ultrasound: "https://example.com/reports/ultrasound-report.pdf",
      hypothermiaReports: "https://example.com/reports/hypothermia-report.pdf",
      dischargeReports: "https://example.com/reports/discharge-report.pdf",
      diabetesReports: "https://example.com/reports/diabetes-report.pdf",
    },
  },
];

// todays tasks

const todaysTasks = {
  date: "2025-07-24",
  userId: "USER1234",
  tasks: [
    {
      id: "task1",
      title: "Early wake-up",
      completed: false,
    },
    {
      id: "task2",
      title: "Regular Morning Walk",
      completed: false,
    },
    {
      id: "task3",
      title: "Dry Bread Breakfast Only",
      completed: false,
    },
    {
      id: "task4",
      title: "Drink 2.5 l of water",
      completed: false,
    },
  ],
};

// Activity timeline

const activityTimeline = {
  userId: "USER1234",
  timeline: [
    {
      id: "act1",
      title: "Uploaded stress test report",
      timestamp: "2025-07-24T09:30:00Z",
      relativeTime: "1 hour ago",
    },
    {
      id: "act2",
      title: "Sent new prescription for anxiety (Zoloft)",
      timestamp: "2025-07-24T03:45:00Z",
      relativeTime: "Today - 9:15 AM",
    },
    {
      id: "act3",
      title: "Completed yoga session",
      timestamp: "2025-07-23T10:30:00Z",
      relativeTime: "Yesterday - 4:00 PM",
    },
    {
      id: "act4",
      title: "Counseling session completed",
      timestamp: "2025-05-10T08:30:00Z",
      relativeTime: "May 10, 2025 - 2:00 PM",
    },
  ],
};

// Doctor data

const doc_data = [
  {
    id: "doc002",
    fullName: "Dr. Rajesh Kumar",
    gender: "Male",
    qualification: "MBBS, MD (Psychiatry)",
    specialization: "Clinical Psychiatry",
    experienceYears: 12,
    shortBio:
      "Board-certified psychiatrist with over 12 years of clinical experience in treating mood disorders and anxiety.",
    profilePhoto: "https://example.com/uploads/rajesh-doctor.jpg",
    languages: ["Hindi", "Marathi", "English"],
    location: "AIIMS Delhi",
    rate: 12, //per min
    ratings: 5, // out of five
    status: "available",
    totalSessions: 1234, //total sessions conducted
  },
  {
    id: "doc003",
    fullName: "Dr. Riya Sharma",
    gender: "Female",
    qualification: "M.Phil. (Clinical Psychology)",
    specialization: "Child Psychology",
    experienceYears: 7,
    shortBio:
      "Helps children manage ADHD and social behavior with modern therapy methods.",
    profilePhoto: null,
    languages: ["English", "Hindi"],
    location: "Mumbai",
    rate: 0,
    ratings: 4.8,
    status: "available",
    totalSessions: 123,
  },
];

// Saved Doctors of users

const savedDoc = [
  {
    id: "",
    userId: "",
    doctorId: "",
  },
];

// Counseller data

const Counseller_data = [
  {
    id: "coun002",
    fullName: "Dr. Rajesh Kumar",
    gender: "Male",
    qualification: "MBBS, MD (Psychiatry)",
    specialization: "Clinical Psychiatry",
    experienceYears: 12,
    shortBio:
      "Board-certified psychiatrist with over 12 years of clinical experience in treating mood disorders and anxiety.",
    profilePhoto: "https://example.com/uploads/rajesh-doctor.jpg",
    languages: ["Hindi", "Marathi", "English"],
    location: "AIIMS Delhi",
    rate: 12, //per min
    ratings: 5, // out of five
    status: "available",
    totalSessions: 1234, //total sessions conducted
  },
  {
    id: "coun003",
    fullName: "Dr. Riya Sharma",
    gender: "Female",
    qualification: "M.Phil. (Clinical Psychology)",
    specialization: "Child Psychology",
    experienceYears: 7,
    shortBio:
      "Helps children manage ADHD and social behavior with modern therapy methods.",
    profilePhoto: null,
    languages: ["English", "Hindi"],
    location: "Mumbai",
    rate: 0,
    ratings: 4.8,
    status: "available",
    totalSessions: 123,
  },
];

// Saved Counseller of users

const savedCounseller = [
  {
    id: "",
    userId: "",
    doctorId: "",
  },
];

// Meditation

const meditation = [
  {
    id: 1,
    title: "Journey to Rest",
    author: "Dr. Eric López",
    imageUrl: "https://example.com/images/journey-to-rest.jpg",
    category: ["Sleep", "Calm"],
    audioUrl: "",
    videoUrl: "",
  },
  {
    id: 2,
    title: "Musical Journey",
    author: "Sarah Melody",
    imageUrl: "https://example.com/images/musical-journey.jpg",
    category: ["Music", "Sleep"],
    audioUrl: "",
    videoUrl: "",
  },
];

// ### 🔹 1. **Patient Basic Info**

// **📍 Endpoint:** `GET /api/patient/:id/info`

```json
{
  "name": "Emma Astrid",
  "phone": "+91 6353226589",
  "gender": "Female",
  "dob": "12/11/1994",
  "nationality": "India",
  "patientNumber": "MB-1437A",
  "age": 31,
  "language": ["English", "Hindi"]
}
```// **📍 Endpoint:** `GET /api/patient/:id/documents` // ### 🔹 2. **Latest Documents** // --- // > ✅ Returns basic personal and demographic information for the patient.

```json
[ 
  {
    "title": "Check up result 2023",
    "url": "/uploads/checkup_2023.pdf",
    "date": "2023-11-12"
  },
  {
    "title": "Medical Summary",
    "url": "/uploads/summary.pdf",
    "date": "2023-09-15"
  },
  {
    "title": "Lab check up result",
    "url": "/uploads/lab_report.pdf",
    "date": "2023-10-10"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/health-analysis` // ### 🔹 3. **Health Analysis (Pie Chart)** // --- // > 📄 Lists recent reports or documents uploaded for the patient.

```json
[
  { "label": "Anxiety", "value": 40, "color": "#FFA500" },
  { "label": "Depression", "value": 30, "color": "#FF6347" },
  { "label": "Sleep Issues", "value": 20, "color": "#00BFFF" },
  { "label": "Stress", "value": 10, "color": "#90EE90" }
]
```// **📍 Endpoint:** `GET /api/patient/:id/appointments` // ### 🔹 4. **Appointment History** // --- // > 📊 Mental health category distribution shown in pie chart format.

```json
[
  {
    "date": "10 April 2025",
    "doctor": "Dr. Sashi",
    "status": "Completed"
  },
  {
    "date": "09 March 2025",
    "doctor": "Dr. Aman",
    "status": "Cancelled"
  },
  {
    "date": "05 March 2025",
    "doctor": "Dr. Kiran",
    "status": "Completed"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/chat-history` // ### 🔹 5. **Chat History** // --- // > 📅 Lists past appointments with doctors and their status.

```json
[
  {
    "date": "07 April 2025",
    "summary": "Feeling stressed at work"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/video-calls` // ### 🔹 6. **Video Call Recordings** // --- // > 💬 Returns summaries of past chat sessions with counselors.

```json
[
  {
    "date": "08 April 2025",
    "topic": "Counseling Session",
    "url": "/videos/session_0804.mp4"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/reviews` // ### 🔹 7. **Patient Reviews** // --- // > 📹 Video call logs with links for playback (if stored).

```json
[
  {
    "date": "06 April 2025",
    "text": "Feeling better"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/assessments` // ### 🔹 8. **Assessment Results** // --- // > 🗨️ Patient feedback or status updates after a session.

```json
[
  {
    "assessment": "Mental Health Check",
    "score": "Moderate Depression"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/prescriptions` // ### 🔹 9. **Prescription List** // --- // > 🧠 Displays outcome of psychological or self-assessment forms.

```json
[
  {
    "medicineName": "Sertraline",
    "dosage": "50 mg",
    "frequency": "Once Daily",
    "duration": "2 Months",
    "instructions": "After breakfast"
  },
  {
    "medicineName": "Clonazepam",
    "dosage": "0.5 mg",
    "frequency": "At bedtime",
    "duration": "1 Month",
    "instructions": "Only if required"
  },
  {
    "medicineName": "Vitamin D3",
    "dosage": "2000 IU",
    "frequency": "Once Daily",
    "duration": "3 Months",
    "instructions": "Morning with food"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/timeline` // ### 🔹 10. **Activity Timeline** // --- // > 💊 Medicines currently prescribed to the patient.

```json
[
  {
    "type": "appointment",
    "date": "10 April 2025",
    "description": "Appointment with Dr. Sashi"
  },
  {
    "type": "video_call",
    "date": "08 April 2025",
    "description": "Video Call - Counseling Session"
  },
  {
    "type": "chat",
    "date": "07 April 2025",
    "description": "Chat - 'Feeling stressed at work'"
  },
  {
    "type": "review",
    "date": "06 April 2025",
    "description": "Review - 'Feeling better'"
  }
]
```// **📍 Endpoint:** `GET /api/patient/:id/suggestions` // ### 🔹 11. **Counseling Suggestions** // --- // > 📍 Activity log to visually show patient’s interaction timeline.

```json
[
  {
    "title": "Cognitive Therapy Recommended",
    "frequency": "Weekly"
  },
  {
    "title": "Weekly Mood Check-Ins",
    "frequency": "Weekly"
  },
  {
    "title": "Stress Meditation (15 mins/day)",
    "frequency": "Daily"
  }
]
```; // --- // > 💡 Recommendations based on the patient’s health progress and feedback.
