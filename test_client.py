"""Quick WebSocket test client for DrishtiStream."""
import asyncio
import json
import websockets

async def test():
    print("Connecting to ws://localhost:8000/ws/stream...")
    async with websockets.connect("ws://localhost:8000/ws/stream") as ws:
        print("Connected! Receiving frames...\n")
        for i in range(5):
            msg = json.loads(await ws.recv())
            print(f"Frame {msg['frame_id']:>5} | "
                  f"timestamp: {msg['timestamp']:.3f} | "
                  f"fps: {msg['fps']} | "
                  f"image size: {len(msg['image']):>6} chars")
        print("\n✓ WebSocket streaming verified!")

if __name__ == "__main__":
    asyncio.run(test())
