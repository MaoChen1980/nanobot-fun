"""WeChat (personal) proxy - runs as a separate process, polls WeChat HTTP API and forwards messages to nanobot Hub via TCP."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import threading
from typing import Any

from loguru import logger

from nanobot.proxy.protocol import HubResponse


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WeChat proxy - polls WeChat API and forwards messages to Hub via TCP")
    parser.add_argument("--hub-url", required=True, help="Hub API base URL (ignored, TCP is used)")
    parser.add_argument("--hub-tcp-port", required=True, type=int, help="Hub TCP port for proxy connections")
    parser.add_argument("--channel", required=True, help="Channel name")
    parser.add_argument("--bot", required=True, help="Bot name")
    return parser.parse_args()


def _get_config() -> dict[str, Any]:
    config_str = os.environ.get("NANOBOT_PROXY_CONFIG", "{}")
    return json.loads(config_str)


class WeixinProxyChannel:
    def __init__(self, config: dict, hub_tcp_host: str, hub_tcp_port: int, channel: str, bot: str):
        self.config = config
        self.hub_tcp_host = hub_tcp_host
        self.hub_tcp_port = hub_tcp_port
        self.channel = channel
        self.bot = bot
        self._processed: dict[str, float] = {}
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._send_lock = threading.Lock()
        self._send_reply_fn: Any = None

    def _connect_tcp(self) -> None:
        self._conn_loop = asyncio.new_event_loop()
        self._conn_thread = threading.Thread(target=self._conn_loop.run_forever, daemon=True)
        self._conn_thread.start()

        async def do_connect() -> None:
            self._reader, self._writer = await asyncio.open_connection(
                self.hub_tcp_host, self.hub_tcp_port
            )
            logger.info("Connected to Hub via TCP at {}:{}", self.hub_tcp_host, self.hub_tcp_port)
            register_msg = {"type": "register", "channel": self.channel, "bot": self.bot, "pid": os.getpid()}
            self._writer.write((json.dumps(register_msg) + "\n").encode())
            await self._writer.drain()
            resp_line = await self._reader.readline()
            resp = json.loads(resp_line.decode())
            if resp.get("success"):
                logger.info("Registered with Hub via TCP")
            else:
                raise RuntimeError(f"TCP registration failed: {resp}")

        future = asyncio.run_coroutine_threadsafe(do_connect(), self._conn_loop)
        future.result()

    async def _do_send(self, msg: dict[str, Any]) -> HubResponse:
        msg["type"] = "message"
        self._writer.write((json.dumps(msg) + "\n").encode())
        await self._writer.drain()
        resp_line = await self._reader.readline()
        return HubResponse.from_dict(json.loads(resp_line.decode()))

    def _poll_loop(self) -> None:
        import httpx

        base_url = self.config.get("api_url", "https://ilinkai.weixin.qq.com")
        token = self.config.get("token", "")

        def fetch_updates():
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(
                        f"{base_url}/cgi-bin/getupdates",
                        params={"token": token, "_": int(time.time())},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception as e:
                logger.warning("WeChat getupdates error: {}", e)
            return None

        def send_reply(chat_id: str, content: str) -> None:
            try:
                import httpx
                with httpx.Client(timeout=30) as client:
                    client.post(
                        f"{base_url}/cgi-bin/sendmessage",
                        params={"token": token},
                        json={"chat_id": chat_id, "text": content},
                    )
            except Exception as e:
                logger.error("WeChat reply error: {}", e)

        self._send_reply_fn = send_reply

        while True:
            try:
                data = fetch_updates()
                if data:
                    for item in data.get("list", []):
                        msg_id = item.get("id", "")
                        now = time.time()
                        if msg_id in self._processed:
                            continue
                        self._processed[msg_id] = now
                        self._processed = {k: v for k, v in self._processed.items() if now - v < 300}

                        content = item.get("content", {}).get("text", "") or item.get("text", "")
                        sender_id = item.get("fromusername", "")
                        chat_id = item.get("chat_id", sender_id)

                        def forward(item=item, sender_id=sender_id, chat_id=chat_id, content=content, msg_id=msg_id):
                            try:
                                with self._send_lock:
                                    future = asyncio.run_coroutine_threadsafe(
                                        self._do_send({
                                            "channel": self.channel,
                                            "bot": self.bot,
                                            "sender_id": sender_id,
                                            "chat_id": chat_id,
                                            "content": content,
                                            "message_id": msg_id,
                                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        }),
                                        self._conn_loop,
                                    )
                                    response = future.result(timeout=120)

                                if response and response.success and response.content:
                                    self._send_reply_fn(chat_id, response.content)
                            except Exception as e:
                                logger.warning("WeChat forward error: {}", e)

                        t = threading.Thread(target=forward, daemon=True)
                        t.start()
            except Exception as e:
                logger.warning("WeChat poll error: {}", e)
            time.sleep(3)


def run_weixin_loop(
    config: dict, hub_tcp_host: str, hub_tcp_port: int, channel: str, bot: str,
    proxy_channel: WeixinProxyChannel,
) -> None:
    t = threading.Thread(target=proxy_channel._poll_loop, daemon=True)
    t.start()
    while True:
        time.sleep(5)


def main() -> None:
    args = _parse_args()
    config = _get_config()

    hub_tcp_host = "127.0.0.1"
    hub_tcp_port = args.hub_tcp_port
    channel = args.channel
    bot = args.bot

    logger.info("WeChat proxy starting for {}:{}", channel, bot)

    try:
        proxy_channel = WeixinProxyChannel(config, hub_tcp_host, hub_tcp_port, channel, bot)
        proxy_channel._connect_tcp()
        logger.info("Registered with Hub via TCP")
        run_weixin_loop(config, hub_tcp_host, hub_tcp_port, channel, bot, proxy_channel)
    except Exception as e:
        logger.error("Failed to start WeChat proxy: {}", e)
        sys.exit(1)


if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        logger.error("WeChat proxy crashed: {}", traceback.format_exc())
        sys.exit(1)
