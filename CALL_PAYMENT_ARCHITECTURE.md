# Call Payment Architecture & Implementation Status

## ✅ BACKEND INFRASTRUCTURE EXISTS

### 1. **Consultation Rate System** 
📁 `app/services/consultation_rate_routes.py`
- **Endpoint**: POST `/api/consultation-rates/{provider_type}/set`
- **Supports**:
  - `voiceCallRate` - Per-minute voice call rate
  - `videoCallRate` - Per-minute video call rate  
  - `inPerson15Min` - 15-minute in-person rate
  - `inPerson30Min` - 30-minute in-person rate
  - `inPerson60Min` - 60-minute in-person rate
- **Provider Types**: `doctor`, `counselor` (extensible to more roles)
- **Collections**: 
  - `doctor_call_rates`
  - `counselor_call_rates`

### 2. **Call Infrastructure**
📁 `app/services/call_service_routes.py`
- **Endpoint**: POST `/calls/initiate`
- **Features**:
  - Call session creation with unique `sessionId`
  - Zego token generation for video/audio
  - Socket.IO call notification to callee
  - Call record storage with status tracking (initiated → accepted → completed)
  - Duration tracking field: `durationSec`
- **Limitations**: No charging/wallet deduction logic yet

### 3. **Chat Charging Model** (Reference Implementation)
📁 `app/services/chat_routes.py` (Lines 681-745)
- Shows HOW charging is implemented in app
- **Pattern**:
  ```
  1. Check if charge needed
  2. Get user's current wallet balance
  3. Verify sufficient balance (prevents charging)
  4. Deduct from wallet: wallet.balance -= charge_amount
  5. Calculate commission split (app vs. provider)
  6. Update provider earnings
  7. Emit Socket.IO notification: "chat_message_charged"
  ```

### 4. **Wallet System**
📁 `app/services/wallet_routes.py`
- GET `/wallet/balance` - Get current balance
- POST `/wallet/recharge_wallet` - Add money
- POST `/wallet/withdraw` - Withdraw money
- Wallet collection stores: `userId`, `balance`, `transactions[]`

---

## ❌ WHAT'S MISSING - Call Charging System

### **Gap 1: Call End & Charging Logic**
❌ No endpoint to end call and apply charges
- Missing: `PUT /calls/{sessionId}/end` or `POST /calls/{sessionId}/complete`
- Missing: Charge calculation logic (duration × per-min-rate)
- Missing: Wallet deduction on call end
- Missing: Commission split calculation

### **Gap 2: Pre-Call Balance Check**
❌ Call initiation doesn't verify wallet balance
- Currently: Calls allowed even if balance = 0
- Needed: Before accepting call, check if balance > (1 min charge)
- Needed: Return error if insufficient balance

### **Gap 3: Role Mapping**
❌ Role-based pricing needs configuration
- Currently: Only `doctor` and `counselor` rates defined
- Needed: List of all roles: doctor, counselor, healer, therapist, etc.
- Needed: Admin panel to configure/update rates per role

### **Gap 4: Call Charging Rules**
❌ No definition of how charges apply:
- When to start charging? (On call accept or on call start?)
- How to handle minimum call time?
- Rounding rules for partial minutes?
- Who handles the first free minute?

---

## 📋 REQUIRED INFORMATION FROM USER

**Q1: What is the complete list of roles and their per-minute rates?**
```
Example:
- doctor: ₹50/min (audio), ₹75/min (video)
- counselor: ₹25/min (audio), ₹40/min (video)
- healer: ₹30/min (audio), ₹50/min (video)
- therapist: ₹60/min (audio), ₹80/min (video)
```

**Q2: When should charging start?**
- [ ] When call is initiated (caller connects)?
- [ ] When call is accepted (callee connects)?
- [ ] When callee picks up (first media)?

**Q3: Minimum call duration?**
- [ ] Charge even for 1-second calls?
- [ ] Minimum 1 minute charge?
- [ ] Free first minute?

**Q4: Commission split?**
- [ ] What % goes to platform vs. provider?
- Example: User pays ₹50, platform keeps 20% (₹10), provider gets 80% (₹40)?

---

## 🔄 IMPLEMENTATION ROADMAP

### Phase 1: Backend Call Charging (Needs Implementation)
1. ✅ Consultation rates already exist (doctors/counselors can set rates)
2. ❌ Create `PUT /calls/{sessionId}/end` endpoint:
   - Accept: `durationSec`, `callType`
   - Get caller's role and rate
   - Calculate charge
   - Deduct from caller's wallet
   - Store charge in call record
   - Return charge details

3. ❌ Update `POST /calls/initiate` to check balance:
   - Get provider's rates
   - Check if caller has minimum balance for 1 min
   - Reject if insufficient

### Phase 2: Flutter UI Implementation (Needs Code)
1. ❌ Create **Video Call Screen**:
   - ZegoCloud integration using CallService
   - Timer showing call duration
   - Balance deduction display (updates every minute)
   - Accept/Reject buttons
   - End Call button

2. ❌ Create **Audio Call Screen**:
   - Similar to video but without ZegoCloud view
   - Duration timer
   - Accept/Reject
   - End Call

3. ❌ Update CallService:
   - Add `getCallRates(providerId, providerType)` - Get per-min rates
   - Add `endCall(sessionId, durationSec, callType)` - Trigger charging

4. ❌ Add In-Call Logic:
   - Every minute: Deduct (rate × 1 min) from wallet
   - Show running total charged
   - If balance drops to 0: Auto-end call

---

## 📊 DATABASE SCHEMA (Already Exists)

### Call Record
```json
{
  "_id": ObjectId,
  "sessionId": "uuid",
  "callerId": "patient_123",
  "calleeId": "doctor_456",
  "callType": "video|audio",
  "status": "initiated|accepted|completed|rejected",
  "durationSec": 0,
  "appointmentId": "optional",
  "createdAt": timestamp,
  "updatedAt": timestamp,
  "callerRole": "patient",
  "calleeRole": "doctor",
  "zego": { "appId": "425094433" }
  
  // ❌ MISSING FIELDS:
  // "chargeAmount": 0,
  // "chargePerMin": 50,
  // "commissionAmount": 0,
  // "providerEarnings": 0,
  // "acceptedAt": timestamp,
  // "completedAt": timestamp
}
```

### Doctor Call Rates (Already Exists)
```json
{
  "_id": ObjectId,
  "doctorId": "doctor_456",
  "voiceCallRate": 50,      // ₹/min
  "videoCallRate": 75,      // ₹/min
  "inPerson15Min": 300,
  "inPerson30Min": 600,
  "inPerson60Min": 1000,
  "updatedAt": timestamp
}
```

---

## 🎯 NEXT STEPS

**User Must Provide**:
1. Final list of roles and pricing
2. Charging rule preferences (when to start, minimum time, etc.)
3. Commission split percentage

**Then Backend Team Must Implement**:
1. Call end + charging endpoint
2. Pre-call balance validation
3. Role pricing configuration management

**Then Flutter Team Implements**:
1. Video call screen with ZegoCloud
2. Audio call screen
3. Timer + running balance display
4. Integration with CallService

