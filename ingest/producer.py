import asyncio
import csv
import io
import logging
import os
import pathlib
import zlib
from typing import Optional


import aiohttp
from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TOPIC_NAME = os.getenv("KAFKA_TOPIC", "nem_dispatch")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))
BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost/data.csv")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:9092")


async def fetch_csv(session: aiohttp.ClientSession, url: str) -> bytes:
    retries = 3
    backoff = 1
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()
        except Exception as exc:  # pragma: no cover - logging
            logger.warning("Fetch attempt %s failed: %s", attempt, exc)
            if attempt == retries:
                raise
            await asyncio.sleep(backoff)
            backoff *= 2


def compute_crc(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


async def send_records(producer: AIOKafkaProducer, topic: str, data: bytes) -> None:
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        record = ",".join(
            [
                row["trading_interval"],
                row["unit_id"],
                row["generated_mw"],
                row["fuel_type"],
            ]
        )
        await producer.send_and_wait(topic, record.encode("utf-8"))
    logger.info("Sent %d records", reader.line_num - 1)


async def main() -> None:
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()
    session = aiohttp.ClientSession()
    last_crc: int | None = None
    try:
        while True:
            try:
                data = await fetch_csv(session, BASE_API_URL)
            except Exception as exc:  # pragma: no cover - logging
                logger.error("Failed to fetch CSV: %s", exc)
                await asyncio.sleep(POLL_INTERVAL)
                continue
            crc = compute_crc(data)
            if crc == last_crc:
                logger.info("No new data; skipping send")
            else:
                await send_records(producer, TOPIC_NAME, data)
                last_crc = crc
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        await session.close()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
