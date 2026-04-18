# Sharding Application Fixes - April 18, 2026

## Issues Found & Fixed

### 1. **Patient Creation Not Working**
**Problem:** When adding a patient via `/add_member` endpoint, data wasn't being saved to shards.

**Root Cause:** The `add_member` endpoint in `admin_routes.py` was only logging the action and returning a stub response with `"member_id": "sharded_id"` instead of actually inserting data.

**Fix:** 
- Modified `add_member()` to actually insert member data into the local database
- Routes the member to the appropriate shard based on `member_type`:
  - **Patient**: Calls `sharded_db.insert_patient()`
  - **Doctor**: Calls `sharded_db.insert_doctor()`
  - **Staff**: Inserts directly using cursor
- Returns actual `member_id` from database

---

### 2. **Only 2 Medicines Showing (Expected More)**
**Problem:** The `/medicines` endpoint was returning hardcoded sample data with only 2 medicines instead of querying the database.

**Root Cause:** 
- The `get_medicines()` endpoint had hardcoded sample data
- Medicine data is replicated across all shards, but wasn't being queried

**Fix:**
- Created `get_all_medicines()` method in `ShardedDBLayer`
- Modified `/medicines` endpoint to call `sharded_db.get_all_medicines()`
- Now queries from shard 0 (medicines are replicated, so only need one shard)
- Returns all actual medicines from database

**Also Fixed:**
- `/medicines/<id>` now queries actual data instead of returning sample
- `/add_medicine` now actually inserts medicines into shard 0
- `/update_medicine` now actually updates medicines
- `/delete_medicine` now actually deletes medicines

---

### 3. **Appointments Only Showing Patient ID (No Names)**
**Problem:** Appointment list displayed only `patient_id` instead of patient name.

**Root Cause:** The `get_appointments()` endpoint wasn't joining with `patient` and `member` tables to fetch patient names.

**Fix:**
- Modified `/appointments` GET endpoint to JOIN with:
  - `patient` table (to link appointment to patient)
  - `member` table (to get patient name)
- Now returns: `patient_id`, `patient_name`, `appointment_date`, `appointment_time`, `doctor_id`, etc.
- Properly handles sharded queries (queries all 3 shards and aggregates results)

---

## Files Modified

1. **`app/routes/admin_routes.py`**
   - Fixed `add_member()` to actually create members and route to shards

2. **`app/routes/medicine_routes.py`**
   - Added import: `get_sharded_db_layer`
   - Fixed `get_medicines()` to query database
   - Fixed `get_medicine(<id>)` to query database
   - Fixed `add_medicine()` to insert into shard 0
   - Fixed `update_medicine()` to update in shard 0
   - Fixed `delete_medicine()` to delete from shard 0

3. **`app/routes/appointment_routes.py`**
   - Fixed `get_appointments()` to JOIN with patient & member tables for names

4. **`app/sharded_db.py`**
   - Added `get_all_medicines()` method to query medicines from all shards

---

## How It Works Now

### Patient Creation Flow
```
POST /add_member (with member_type="Patient")
  ↓
Validates input
  ↓
Inserts into local member & users tables
  ↓
Gets member_id from database
  ↓
Calls sharded_db.insert_patient()
  ↓
Routes to correct shard based on: shard_id = MD5(member_id) % 3
  ↓
Data saved to sharded table (e.g., shard_1_patient)
```

### Medicine Query Flow
```
GET /medicines
  ↓
Calls sharded_db.get_all_medicines()
  ↓
Queries shard 0: SELECT * FROM shard_0_medicine
  ↓
Returns all medicines (replicated across shards)
```

### Appointment Display Flow
```
GET /appointments
  ↓
Loops through all 3 shards
  ↓
For each shard, queries:
  SELECT a.*, m.name as patient_name
  FROM shard_X_appointment a
  LEFT JOIN shard_X_patient p ON a.patient_id = p.patient_id
  LEFT JOIN shard_X_member m ON p.member_id = m.member_id
  ↓
Aggregates results from all shards
  ↓
Returns appointments with patient names
```

---

## Testing

To verify the fixes work:

1. **Test Patient Creation:**
   ```bash
   POST http://localhost:5000/add_member
   {
     "name": "Test Patient",
     "age": 30,
     "email": "testpatient@test.com",
     "contact_no": "9000000001",
     "username": "testpat1",
     "password": "Pass1234",
     "member_type": "Patient",
     "role": "user",
     "gender": "Male",
     "address": "123 Test St",
     "blood_group": "O+"
   }
   ```
   ✓ Should return actual `member_id`
   ✓ Data should appear in database shards

2. **Test Medicines:**
   ```bash
   GET http://localhost:5000/medicines
   ```
   ✓ Should return 10+ medicines from database (not just 2)

3. **Test Appointments with Names:**
   ```bash
   GET http://localhost:5000/appointments
   ```
   ✓ Each appointment should show `patient_name` along with ID
   ✓ Results aggregated from all 3 shards

---

## Summary of Changes

| Issue | Cause | Solution | Status |
|-------|-------|----------|--------|
| Patient not added | Stub implementation | Real DB insert + shard routing | ✅ Fixed |
| Only 2 medicines | Hardcoded data | Query all from shards | ✅ Fixed |
| No patient names | Missing JOIN | Added patient & member JOINs | ✅ Fixed |

All endpoints now properly use the ShardedDBLayer for real data operations!
