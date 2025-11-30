#  Secure Command Gateway for Industrial Robot Protection
### A Cryptography-Based Framework to Prevent Unauthorized Remote Control Commands

This project implements a **software-only security layer** that protects industrial robots from unauthorized remote command execution. It uses strong cryptographic techniques to validate every command sent by an operator before forwarding it to the robot.

---

##  Features
- RSA Digital Signature Verification  
- Timestamp Freshness Validation  
- Nonce-Based Replay Protection  
- Role-Based Access Control (RBAC)  
- Secure Command Forwarding to Robot  
- Simulation of All Major Robot-Attack Scenarios  
- Fully Functional on Windows PowerShell

---

##  Project Structure

```
robot-security/
│
├── scg.py
├── client.py
├── mock_robot.py
├── client_pub.pem
├── audit.log
│
└── ca/
     ├── private/
     │     ├── ca.key
     │     ├── scg.key
     │     └── client.key
     ├── csr/
     └── certs/
           ├── ca.crt
           ├── scg.crt
           └── client.crt
```

---

## 1. Installation (Windows)

### Install Python dependencies:
```bash
pip install fastapi uvicorn cryptography requests
```

### Install OpenSSL  
Download: https://slproweb.com/products/Win32OpenSSL.html  
Choose **Win64 OpenSSL v3.x Full** and check:
Add OpenSSL to PATH

---

## 2. Certificate Authority (CA) Setup

Navigate to CA folder:
```powershell
cd D:\robot-security\ca
```

### 2.1 Generate Root CA
```powershell
openssl genrsa -out private\ca.key 4096
openssl req -x509 -new -nodes -key private\ca.key -sha256 -days 3650 -subj "/CN=Local-CA" -out certs\ca.crt
```

### 2.2 Generate SCG Certificates
```powershell
openssl genrsa -out private\scg.key 2048
openssl req -new -key private\scg.key -out csr\scg.csr -subj "/CN=SCG"
openssl x509 -req -in csr\scg.csr -CA certs\ca.crt -CAkey private\ca.key -CAcreateserial -out certs\scg.crt -days 825 -sha256
```

### 2.3 Generate Client Certificates
```powershell
openssl genrsa -out private\client.key 2048
openssl req -new -key private\client.key -out csr\client.csr -subj "/CN=OperatorClient"
openssl x509 -req -in csr\client.csr -CA certs\ca.crt -CAkey private\ca.key -CAcreateserial -out certs\client.crt -days 365 -sha256
```

### 2.4 Extract Client Public Key
```powershell
openssl x509 -in certs\client.crt -pubkey -noout > ..\client_pub.pem
```

---

## 3. Running the System

Open **three separate PowerShell terminals**.

### Terminal 1 – Mock Robot Server
```powershell
cd D:\robot-security
python mock_robot.py
```

Expected:
```
Uvicorn running on http://127.0.0.1:8001
```

### Terminal 2 – Secure Command Gateway (SCG)
```powershell
cd D:\robot-security
python scg.py
```

Expected:
```
Uvicorn running on http://127.0.0.1:8002
```

### Terminal 3 – Client
```powershell
cd D:\robot-security
python client.py
```

Expected:
```
RAW Response: {"status":"executed", ...}
```

---

# 4. Testing Security Scenarios

## 4.1 Valid Command (PASS)
Run:
```powershell
python client.py
```
Expected: Command accepted & executed.

---

## 4.2 Invalid Signature Attack (FAIL)
Modify in `client.py`:
```python
packet["signature"] = packet["signature"][:-4] + "ABCD"
```
Expected: `"Invalid Signature"`

---

## 4.3 Replay Attack (FAIL)
In `client.py`:
```python
last_packet = None
send_command("MOVE", {...}, reuse=False)
send_command("MOVE", {...}, reuse=True)
```
Expected: `"Replay Detected"`

---

## 4.4 Stale Timestamp Attack (FAIL)
Modify:
```python
"timestamp": time.time() - 200
```
Expected: `"Stale Timestamp"`

---

## 4.5 Unauthorized Command (RBAC Violation) (FAIL)
```python
send_command("SHUTDOWN", {})
```
Expected: `"Not Authorized"`

---

## 4.6 Payload Tampering Attack (FAIL)
```python
signature_b64, payload_bytes = sign_payload(payload)
payload["command"] = "STOP"
```
Expected: `"Invalid Signature"`

---

# 5. Test Case Summary

| Test Case | Scenario                       | Expected Outcome        | Result |
|-----------|-------------------------------|--------------------------|--------|
| TC-01     | Valid Signed Command          | Accept & Execute         | PASS   |
| TC-02     | Invalid Signature             | Reject                   | PASS   |
| TC-03     | Replay Attack                 | Reject                   | PASS   |
| TC-04     | Stale Timestamp               | Reject                   | PASS   |
| TC-05     | Unauthorized RBAC Command     | Reject                   | PASS   |
| TC-06     | Payload Tampering             | Reject                   | PASS   |

---

# Troubleshooting

| Issue | Solution |
|-------|----------|
| `openssl not recognized` | Add OpenSSL `bin/` to PATH |
| `client_pub.pem empty` | Re-run extraction command |
| Replay not detected | Ensure SCG runs with single worker |
| JSONDecodeError | SCG crashed → check logs |
| Port already in use | Change ports in scg.py or mock_robot.py |

---

# Summary

This project demonstrates how cryptographic techniques secure industrial robots from unauthorized access. Using RSA signatures, freshness verification, replay prevention, and RBAC enforcement, the Secure Command Gateway ensures that only trusted and verified operator commands are executed.

---

#  License
This project is intended for academic and research use only.
