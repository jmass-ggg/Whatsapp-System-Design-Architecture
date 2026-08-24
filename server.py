import asyncio
import json
import requests
import websockets

connection_handler={}

async def handler(websocket): 
    username=None
    try:
        username=await websocket.recv()
        if username in connection_handler:
            websocket.send(
                json.dumps({
                    "type":"error",
                    "message":"User already exists"
                })
            )
            await websocket.close()
            return
        connection_handler[username]=websocket
        print(f"{username} Online")
        print("Online user :- ",list(connection_handler))
        await websocket.send(
            json.dumps(
                {
                    "type": "connected",
                    "message": f"Welcome {username}"
                }
            )
        )
        async for raw_message in websocket:
            data=json.loads(raw_message)
            print("raw message :- ",data)
            receiver=data["receiver"]
            message=data["message"]
            receiver_socket=connection_handler.get(receiver)
            if receiver_socket is None:
                await websocket.send(
                    json.dumps(
                        {
                            "type":"error",
                            "message": f"{username} is Offline"
                        }
                    )
                )
                continue
            await receiver_socket.send(
                json.dumps({
                    "type":"message",
                    "sender":username,
                    "receiver":receiver,
                    "message":message
                    
            })
            )
            await websocket.send(
                json.dumps(
                    {
                    "type":"sent",
                    "receiver":receiver,
                    "message":message
                }
                )
            )
            
    except websockets.exceptions.ConnectionClosed:

        print(f"{username} disconnected")

    except Exception as e:
        print("Error is :- ",e)
        
        
async def main():

    async with websockets.serve(
        handler,
        "localhost",
        8000
    ):

        print("WebSocket server running on ws://localhost:8000")

        await asyncio.Future()


asyncio.run(main())
