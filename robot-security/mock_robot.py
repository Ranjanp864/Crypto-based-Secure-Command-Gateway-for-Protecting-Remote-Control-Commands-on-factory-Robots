from fastapi import FastAPI, Request
import uvicorn
import time

app = FastAPI()

@app.post("/execute")
async def execute_command(req: Request):
    data = await req.json()
    print("\n[MRS] Received command:", data)

    # Simulate robot execution
    result = {
        "executed": True,
        "received_command": data.get("command"),
        "details": data,
        "timestamp": time.time()
    }

    return result


if __name__ == "__main__":
    uvicorn.run("mock_robot:app", host="127.0.0.1", port=8001)
