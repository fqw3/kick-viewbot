import asyncio
import websockets
import json
import random
import tls_client
import traceback

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
client_token = "e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823"

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': user_agent,
    'sec-ch-ua': '"Chromium";v="137", "Google Chrome";v="137", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

def get_channel_id(channel_name):
    s = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    s.headers = headers
    r = s.get(f'https://kick.com/api/v2/channels/{channel_name}')
    return r.json()["id"] if r.status_code == 200 else None

def get_token():
    s = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    s.headers = headers
    s.get("https://kick.com")
    s.headers["X-CLIENT-TOKEN"] = client_token
    r = s.get('https://websockets.kick.com/viewer/v1/token')
    return r.json()["data"]["token"] if r.status_code == 200 else None

async def send_view(token, channel_id, i):
    try:
        x = 0
        async with websockets.connect(
            f"wss://websockets.kick.com/viewer/v1/connect?token={token}",
            additional_headers={
                "User-Agent": user_agent,
                "Origin": "https://kick.com",
                "Cookie": f"client_token={client_token}"
            }
        ) as ws:
            while True:
                x += 1
                if x % 2 == 0:
                    await ws.send(json.dumps({"type": "ping"}))
                    print(f"[{i}] sent ping")
                else:
                    await ws.send(json.dumps({
                        "type": "channel_handshake",
                        "data": {
                            "message": {"channelId": channel_id}
                        }
                    }))
                    print(f"[{i}] sent handshake")
                sleep = 12 + random.randint(1, 5)
                print(f"[{i}] sleeping for {sleep}s")
                await asyncio.sleep(sleep)
    except Exception:
        traceback.print_exc()

async def run(channel, total_views, threads):
    channel_id = get_channel_id(channel)
    sem = asyncio.Semaphore(threads)

    async def task(i):
        async with sem:
            token = get_token()
            if token:
                print(f"[{i}] Got token {token}")
                await send_view(token, channel_id, i)
            await asyncio.sleep(0.2)

    await asyncio.gather(*(task(i) for i in range(total_views)))


if __name__ == "__main__":
    channel = input("Channel: ").split("/")[-1]
    total_views = int(input("Views to send: "))
    threads = int(input("Threads to use: "))
    asyncio.run(run(channel, total_views, threads))
