import requests, json, time, uuid, base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Load RSA private key
with open("ca/private/client.key", "rb") as f:
    PRIV = serialization.load_pem_private_key(f.read(), password=None)

IDENTITY = "OperatorClient"


def sign_payload(payload):
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode()

    signature = PRIV.sign(
        payload_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode(), payload_bytes

nonce_value = None

def send_command(command, params, reuse=False):
    global nonce_value

    if not reuse:
        nonce_value = str(uuid.uuid4())

    payload = {
        "command": command,
        "params": params,
        "timestamp": time.time(),

        #---------SCENARIO - 4 Timestamp Attack (FAIL)-------------
        #"timestamp": time.time() -200, #Scenario 4

        "nonce": nonce_value
    }

    
    signature_b64, payload_bytes = sign_payload(payload)

    #--------------SCENARIO - 6 (Correct Signature, Wrong Payload (FAIL))----------------

    #signature_b64, payload_bytes = sign_payload(payload)
    #payload["command"] = "STOP"


    packet = {
        "identity": IDENTITY,
        "payload": payload,
        "signature": signature_b64
        

    }
        #----------SCENARIO -2 Invalid Signature (FAIL)-----------
    #packet["signature"] = packet["signature"][:-4] + "ABCD"

        

    print("\nSending packet:")
    print(packet)

    try:
        res = requests.post("http://127.0.0.1:8002/command", json=packet)
        print("RAW Response:", res.text)
        return res.json()
    except Exception as e:
        print("Client error:", e)
        return None


if __name__ == "__main__":
    #-------------SCENARIO 1 Valid Command Execution (PASS)---------
    send_command("MOVE", {"axis": 1, "angle": 25}, reuse =False) #Scenario 1

    #-----------SCENARIO 3 Replay Attack (FAIL)-------------
    #send_command("MOVE", {"axis": 1, "angle": 25}, reuse=True)  # second replay
   
   #-----SCENARIO 5 : Unauthorized Command via RBAC (FAIL)----------
    #send_command("SHUTDOWN", {}) #Scenario 5

      #-------------SCENARIO 7 InValid Command Execution (FAIL)---------
    #send_command("ROTATE", {"axis": 1, "angle": 25}, reuse =False) #Scenario 7