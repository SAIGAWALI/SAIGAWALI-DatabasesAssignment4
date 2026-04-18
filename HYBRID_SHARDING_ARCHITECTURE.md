# Hybrid Sharding Architecture - Assignment 4

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│        Flask Website (localhost:5000)               │
└─────────────────────────────────────────────────────┘
         ↙            ↓            ↖
    
┌──────────────────────────┐  ┌────────────────────────────────────┐
│  LOCAL DATABASE          │  │  REMOTE SHARDED DATABASE           │
│  (localhost:3306)        │  │  (10.0.116.184)                    │
├──────────────────────────┤  ├────────────────────────────────────┤
│ Authentication Layer     │  │ Distributed Data Layer             │
│  - users (login)         │  │                                    │
│  - member (base info)    │  │ Shard 0 (3307):                   │
│  - audit_log             │  │  - shard_0_member                 │
│                          │  │  - shard_0_patient                │
│                          │  │  - shard_0_doctor                 │
│ ❌ NOT queried for       │  │  - shard_0_appointment            │
│    patient/doctor/       │  │  - shard_0_users (backup)         │
│    appointment data      │  │  - shard_0_medicine (replicated)  │
│                          │  │  - shard_0_inventory              │
│                          │  │                                    │
│                          │  │ Shard 1 (3308):                   │
│                          │  │  - shard_1_member                 │
│                          │  │  - shard_1_patient                │
│                          │  │  - shard_1_doctor                 │
│                          │  │  - shard_1_appointment            │
│                          │  │  - shard_1_users (backup)         │
│                          │  │  - shard_1_medicine (replicated)  │
│                          │  │  - shard_1_inventory              │
│                          │  │                                    │
│                          │  │ Shard 2 (3309):                   │
│                          │  │  - shard_2_member                 │
│                          │  │  - shard_2_patient                │
│                          │  │  - shard_2_doctor                 │
│                          │  │  - shard_2_appointment            │
│                          │  │  - shard_2_users (backup)         │
│                          │  │  - shard_2_medicine (replicated)  │
│                          │  │  - shard_2_inventory              │
└──────────────────────────┘  └────────────────────────────────────┘
```

---

## Route Mapping: Which Database Gets Queried

### **Authentication Routes** (`auth_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `POST /login` | User authentication | **LOCAL** | Checks username/password in LOCAL users table |
| `GET /isAuth` | Verify token | **LOCAL** | Token already contains member info from login |
| `GET /audit_logs` | View audit logs | **LOCAL** | Audit logs stored in local audit_log table |

### **Member Routes** (`member_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `GET /portfolio/<id>` | Get member info | **LOCAL** | Basic info from local member table |

### **Admin Routes** (`admin_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `POST /add_member` | Create member | **LOCAL + REMOTE** | Insert member/users to LOCAL, then route patient/doctor/staff data to REMOTE SHARD |
| `DELETE /member/<id>` | Delete member | **LOCAL + REMOTE** | Delete from LOCAL DB, then delete from corresponding REMOTE SHARD |
| `GET /members` | List all members | **REMOTE** | Aggregates from all 3 shards |

### **Patient Routes** (`patient_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `GET /doctors` | List all doctors | **REMOTE** | Queries all 3 shards, aggregates results |
| `GET /my_appointments` | Patient's appointments | **REMOTE** | Queries patient's assigned shard |

### **Appointment Routes** (`appointment_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `GET /appointments` | List all appointments | **REMOTE** | Queries all 3 shards with JOINs for patient names |
| `GET /appointments/<id>` | Get single appointment | **REMOTE** | Calculates shard from patient_member_id, queries that shard |
| `POST /add_appointment` | Create appointment | **REMOTE** | Routes to shard based on patient's member_id |
| `DELETE /appointment/<id>` | Delete appointment | **REMOTE** | Deletes from appropriate shard |

### **Medicine Routes** (`medicine_routes.py`)
| Endpoint | Operation | DB Used | Details |
|----------|-----------|---------|---------|
| `GET /medicines` | List all medicines | **REMOTE** | Medicines replicated on all shards, queries shard 0 |
| `GET /medicines/<id>` | Get single medicine | **REMOTE** | Queries shard 0 (replicated table) |
| `POST /add_medicine` | Add medicine | **REMOTE** | Inserts to shard 0 (replicated across all) |
| `PUT /update_medicine/<id>` | Update medicine | **REMOTE** | Updates on shard 0 (replicated) |
| `DELETE /medicine/<id>` | Delete medicine | **REMOTE** | Deletes from shard 0 (replicated) |

---

## Data Flow Examples

### **Example 1: User Login**
```
POST /login (user: doctor1, password: doc123)
    ↓
auth_routes.py:login()
    ↓
Query LOCAL DB: SELECT * FROM users WHERE username='doctor1'
    ↓
Verify password hash with bcrypt
    ↓
Generate JWT token (contains member_id, member_type)
    ↓
Return token ✅
```

### **Example 2: Create Patient**
```
POST /add_member (name: John, age: 30, member_type: Patient)
    ↓
admin_routes.py:add_member()
    ↓
Step 1: Insert to LOCAL DB
  - INSERT INTO member (name, age, ...) → member_id = 101
  - INSERT INTO users (member_id=101, ...)
    ↓
Step 2: Route to REMOTE SHARD
  - Calculate shard_id = MD5(101) % 3 = 2
  - Connect to 10.0.116.184:3309 (Shard 2)
  - INSERT INTO shard_2_member (member_id=101, name=John, ...)
  - INSERT INTO shard_2_patient (member_id=101, blood_group=...)
    ↓
Data exists in BOTH places:
  - LOCAL DB: member, users records
  - SHARD 2: shard_2_member, shard_2_patient ✅
```

### **Example 3: Query All Patients**
```
GET /members
    ↓
admin_routes.py:list_members()
    ↓
sharded_db.get_all_members()
    ↓
Loop through all 3 shards:
  - Query 10.0.116.184:3307 → shard_0_member
  - Query 10.0.116.184:3308 → shard_1_member
  - Query 10.0.116.184:3309 → shard_2_member
    ↓
Aggregate & sort results
    ↓
Return combined list ✅
```

### **Example 4: Get Patient Appointments**
```
GET /appointments?date=2026-04-18
    ↓
appointment_routes.py:get_appointments()
    ↓
For each shard in [0, 1, 2]:
  - Connect to 10.0.116.184:330X
  - Query: SELECT a.*, m.name FROM shard_X_appointment a
           JOIN shard_X_patient p ON a.patient_id = p.patient_id
           JOIN shard_X_member m ON p.member_id = m.member_id
           WHERE appointment_date = '2026-04-18'
    ↓
Aggregate results from all shards
    ↓
Return with patient names ✅
```

---

## Database Connections Required

### **LOCAL Database** (localhost:3306)
```
Host: localhost
Port: 3306
User: root (or your local user)
Password: (your password)
Database: dms_db

Tables:
  - member (base info, used for auth & RBAC)
  - users (credentials, used for login)
  - audit_log (action tracking)
```

### **REMOTE SHARDS** (10.0.116.184)
```
Host: 10.0.116.184
Username: The_Boys
Password: password@123
Database: The_Boys

Shard 0: Port 3307
Shard 1: Port 3308
Shard 2: Port 3309
```

---

## Shard Key & Routing Logic

**Shard Key:** `member_id`

**Hash Function:**
```python
shard_id = MD5(member_id) % 3
```

**Example Routing:**
- `member_id=1` → MD5("1") % 3 = **Shard 0** (10.0.116.184:3307)
- `member_id=2` → MD5("2") % 3 = **Shard 1** (10.0.116.184:3308)
- `member_id=3` → MD5("3") % 3 = **Shard 2** (10.0.116.184:3309)
- `member_id=4` → MD5("4") % 3 = **Shard 1** (10.0.116.184:3308)

---

## Consistency Model

### **LOCAL DB (Strong Consistency)**
- User credentials & roles
- Audit logs
- Base member info
- All changes immediately visible

### **REMOTE SHARDS (Eventual Consistency)**
- Patient/Doctor/Appointment data
- Multi-shard queries may see slightly stale data
- Single-shard queries are consistent
- Replication across shards takes time

---

## Failover Behavior

| Scenario | Behavior |
|----------|----------|
| **Shard 0 Down** | ❌ Can't access data routed to Shard 0 (33% of members) ✅ Shards 1 & 2 still accessible |
| **Shard 1 & 2 Down** | ✅ Shard 0 still accessible (33% of data) ❌ 66% of data unavailable |
| **LOCAL DB Down** | ❌ ❌ Can't login at all (auth broken) |
| **All Shards Down** | ✅ Can still login (local DB) ❌ Can't query patient/doctor data |

---

## Summary

This HYBRID approach provides:
✅ **Security**: Credentials stored securely in isolated local DB  
✅ **Scalability**: Transactional data distributed across 3 remote shards  
✅ **Simplicity**: Auth layer doesn't require shard routing  
✅ **Redundancy**: Member data exists in both local (for reference) and shards (for distribution)  
✅ **Production-Ready**: Realistic architecture used by many companies
