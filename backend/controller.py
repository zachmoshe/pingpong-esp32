import asyncio
from contextlib import asynccontextmanager
import enum
import logging 
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoomState:
    def __init__(self, notifier=None):
        self.is_free = True
        self.last_state_change_time = time.time()
        self.notifier = notifier

    def __str__(self):
        return f"[{self.state} at {self.last_state_change_time:.3f}  (time now - {time.time():.3f}, diff - {time.time() - self.last_state_change_time:.3f}s)]"

    def asdict(self):
        return {"state": self.state, "last_state_change_time": self.last_state_change_time}

    @property
    def state(self):
        return "free" if self.is_free else "taken"

    async def take(self):
        self.is_free = False
        self.last_state_change_time = time.time()
        await self.notifier.notify(self)

    async def free(self):
        self.is_free = True
        self.last_state_change_time = time.time()
        await self.notifier.notify(self)



class Controller:

    def __init__(self, cfg, notifier):
        self.cfg = cfg
        self.time_without_event_to_declare_idle_secs = cfg["time_without_event_to_declare_idle_secs"]
        self.notifier = notifier
        self.room_state = RoomState(notifier=self.notifier)
        self.free_room_task = None
        print(self.room_state)

    async def handle_event(self, event):
        event_type = event.get("type")
        if event_type is None:
            raise ValueError("Illegal event. No `type`")

        if event_type == "bounce-detected":
            await self.handle_room_taken_indication(event)
        else: 
            raise ValueError(f"Unknown event type: {event_type}")

    def start_countdown_to_free_room(self):
        if self.free_room_task is not None:
            self.free_room_task.cancel()
        self.free_room_task = asyncio.create_task(self._countdown_to_free_room())

    async def _countdown_to_free_room(self):
        await asyncio.sleep(self.time_without_event_to_declare_idle_secs)
        logger.info(f"Countdown to free room completed. Freeing room.")
        await self.room_state.free()

    async def handle_room_taken_indication(self, event):
        logger.info(f"Room taken indication received: {event}")
        await self.room_state.take()
        self.start_countdown_to_free_room()

    def get_room_state(self):
        return self.room_state.asdict() 