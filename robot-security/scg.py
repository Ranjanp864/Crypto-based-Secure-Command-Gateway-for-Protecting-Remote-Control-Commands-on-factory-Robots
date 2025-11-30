from fastapi import FastAPI, Request
import uvicorn, json, base64, time, requests

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

app = FastAPI()

# Load trusted client public key
with open("client_pub.pem", "rb") as f:
    CLIENT_PUB = serialization.load_pem_public_key(f.read())

# Nonce storage
used_nonces = set()

# RBAC policy
ALLOWED_COMMANDS = {
    "OperatorClient": ["MOVE", "STOP", "SET_SPEED"]
}


# ----------------------------------------------------------------------------------------
# RSA Signature Verification
# ----------------------------------------------------------------------------------------
def verify_signature(payload_bytes, signature_b64):
    try:
        signature = base64.b64decode(signature_b64)

        CLIENT_PUB.verify(
            signature,
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("Signature verification failed:", e)
        return False


# ----------------------------------------------------------------------------------------
# Command Handler
# ----------------------------------------------------------------------------------------
@app.post("/command")
async def command_handler(req: Request):

    print("\n===== Incoming Request =====")

    # --- JSON Parsing ---
    try:
        data = await req.json()
        print("Raw received:", data)
    except Exception as e:
        print("JSON parse error:", e)
        return {"status": "rejected", "reason": "Invalid JSON"}

    # -----------------------------------------------------------------
    # Extract fields
    # -----------------------------------------------------------------
    identity = data.get("identity")
    payload = data.get("payload")
    signature = data.get("signature")

    if not identity or not payload or not signature:
        return {"status": "rejected", "reason": "Missing fields"}

    # Canonical JSON for signing
    try:
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
    except:
        return {"status": "rejected", "reason": "Bad payload"}

    # -----------------------------------------------------------------
    # 1) Signature Verification
    # -----------------------------------------------------------------
    if not verify_signature(payload_bytes, signature):
        return {"status": "rejected", "reason": "Invalid Signature"}

    # -----------------------------------------------------------------
    # 2) Timestamp Freshness Check
    # -----------------------------------------------------------------
    if abs(time.time() - payload["timestamp"]) > 60:
        return {"status": "rejected", "reason": "Stale Timestamp"}

    # -----------------------------------------------------------------
    # 3) Nonce Check (Replay Protection)
    # -----------------------------------------------------------------
    nonce = payload["nonce"]
    if nonce in used_nonces:
        print("Replay detected: nonce already used")
        return {"status": "rejected", "reason": "Replay Detected"}

    used_nonces.add(nonce)

    # -----------------------------------------------------------------
    # 4) RBAC Check & Whitelisting
    # -----------------------------------------------------------------
    command = payload.get("command")
    allowed_cmds = ALLOWED_COMMANDS.get(identity, [])

    print("Identity:", identity)
    print("Command:", command)
    print("Allowed Commands:", allowed_cmds)

    if command not in allowed_cmds:
        return {"status": "rejected", "reason": "Not Authorized"}

    # -----------------------------------------------------------------
    # 5) Forward Validated Command to Mock Robot
    # -----------------------------------------------------------------
    try:
        robot_res = requests.post("http://localhost:8001/execute", json=payload)
        robot_res_json = robot_res.json()
    except Exception as e:
        print("MRS connection error:", e)
        return {"status": "rejected", "reason": "Robot Server Unreachable"}

    # -----------------------------------------------------------------
    # 6) Audit Logging
    # -----------------------------------------------------------------
    audit_entry = {
        "payload": payload,
        "result": robot_res_json,
        "timestamp": time.time()
    }

    with open("audit.log", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")

    # -----------------------------------------------------------------
    # 7) Success Response
    # -----------------------------------------------------------------
    print("Command accepted and forwarded.")
    return {
        "status": "executed",
        "robot_response": robot_res_json
    }


# ----------------------------------------------------------------------------------------
# Run Server
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    #uvicorn.run("scg:app", host="127.0.0.1", port=8002)
    uvicorn.run("scg:app", host="127.0.0.1", port=8002, workers=1)

