import asyncio
import csv
import json
import logging
import os
import pathlib
import zlib
from typing import Optional

import aiohttp
from aiokafka import AIOKafkaProducer


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
LOGGER = logging.getLogger("producer")


API_URL = os.getenv("API_URL", "https://example.com/latest_dispatch.csv")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "nem_dispatch")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))
CRC_CHECKPOINT_PATH = pathlib.Path(os.getenv("CRC_CHECKPOINT_PATH", "/tmp/dispatch_crc"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


async def fetch_csv(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.read()


def load_crc(path: pathlib.Path) -> Optional[int]:
    try:
        return int(path.read_text().strip())
    except FileNotFoundError:
        return None
    except ValueError:
        return None


def save_crc(path: pathlib.Path, crc: int) -> None:
    path.write_text(str(crc))


async def produce_records(producer: AIOKafkaProducer, topic: str, data: bytes) -> int:
    text = data.decode("utf-8")
    reader = csv.DictReader(text.splitlines())
    count = 0
    for row in reader:
        await producer.send_and_wait(topic, json.dumps(row).encode("utf-8"))
        count += 1
    return count


async def run() -> None:
    session = aiohttp.ClientSession()
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    last_crc = load_crc(CRC_CHECKPOINT_PATH)
    backoff = 5
    try:
        while True:
            try:
                data = await fetch_csv(session, API_URL)
                crc = zlib.crc32(data)
                if crc == last_crc:
                    LOGGER.info("No new data available")
                else:
                    records = await produce_records(producer, KAFKA_TOPIC, data)
                    LOGGER.info("Produced %s records", records)
                    last_crc = crc
                    save_crc(CRC_CHECKPOINT_PATH, crc)
                backoff = 5
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Error in fetch/produce loop: %s", exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)
                continue
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await producer.stop()
        await session.close()


if __name__ == "__main__":
    asyncio.run(run())
