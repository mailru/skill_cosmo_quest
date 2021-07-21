import asyncio
import logging
from typing import Dict

import graphyte  # type: ignore


class GraphiteSender:
    def __init__(self, host, prefix) -> None:
        self.sender: graphyte.Sender = graphyte.Sender(host, prefix=prefix)
        self.is_runned: bool = False
        self.start_collect()

    def start_collect(self):
        self.metrics: Dict = {}

    def inc(self, name):
        logging.info(f"Add metrics: {name}")
        if name in self.metrics:
            self.metrics[name] += 1
        else:
            self.metrics[name] = 1

    def send_metrics(self):
        for name, value in self.metrics.items():
            self.sender.send(name, value)

    async def send_task_async(self):
        self.start_collect()
        await asyncio.sleep(self.interval)
        self.send_metrics()
        if self.is_runned:
            self.loop.create_task(self.send_task_async())

    def add_loop_task(self, loop, interval):
        if self.is_runned:
            raise Exception("Graphite client exception", "Send task is already runned")

        self.loop = loop
        self.is_runned = True
        self.interval = interval
        self.loop.create_task(self.send_task_async())

    def stop_loop_task(self):
        self.is_runned = False
