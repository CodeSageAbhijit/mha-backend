# Role System Update - Inourah Mental Health

## New Role Structure

### Professional Roles (Salary-Based, No Commission)
1. **psychiatrist** - Can prescribe medicine, heal users
2. **mentor** - Can heal/support users (like counselor)
3. **counselor** - Can heal/support users (similar to mentor)
4. **business_coach** - Has business knowledge, acts as mentor, can heal/support
5. **buddy** - Support and healing only (like counselor)

### User Roles (Existing)
- **patient** (aka "user") - End user seeking help
- **admin** - Super admin with full access
- **superadmin** - Super admin with full access

## Changes Made

### Backend Changes
- ✅ Updated register_routes.py to accept new roles
- ✅ Created collections for new professional types
- ✅ Created default pricing configuration
- ✅ Updated consultation rate routes to hide salary info
- ✅ Added privacy controls to hide user contact details

### Flutter Changes
- ✅ Updated User model to support role types
- ✅ Created Professional model for unified UI
- ✅ Updated dashboards to hide contact details
- ✅ Added role-based permissions for features

## Default Per-Minute Rates (Admin/Superadmin Can Modify)

```
Psychiatrist:
  - Voice Call: ₹100/min
  - Video Call: ₹150/min

Mentor/Counselor:
  - Voice Call: ₹50/min
  - Video Call: ₹75/min

Business Coach:
  - Voice Call: ₹75/min
  - Video Call: ₹100/min

Buddy:
  - Voice Call: ₹30/min
  - Video Call: ₹50/min
```

## Key Features
- Only psychiatrist can prescribe medicine
- All professionals are salary-based (no commission shown)
- Wallet is visible but salary/commission not mentioned
- User contact details hidden from all professionals
- Previous prescription/session history shown only to psychiatrist
- Admin/Superadmin can configure rates via API
