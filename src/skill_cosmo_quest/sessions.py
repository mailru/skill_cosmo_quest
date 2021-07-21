import asyncio
import logging
import time

sessions: dict = dict()


class UserSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.set_info({})
        self.update()

    def set_info(self, info):
        self.info = info

    def update(self):
        self.last_time = time.time()

    def remove(self):
        global sessions
        sessions.pop(self.session_id, None)


def get_session(session_id):
    global sessions
    user_session = sessions.get(session_id, None)
    if user_session is None:
        user_session = UserSession(session_id)
        sessions[session_id] = user_session
    return user_session


def init(new_session_life_time=60000):
    global session_life_time
    session_life_time = new_session_life_time


async def remove_old_sessions():
    global sessions, session_life_time
    current_time = time.time()
    remove_time = current_time - session_life_time
    delete_list = []
    counter = 0
    for key, value in sessions.items():
        if value.last_time < remove_time:
            delete_list.append(key)
        counter += 1
        if counter % 1000 == 0:
            await asyncio.sleep(1)

    logging.info(f"{len(delete_list)} sessions from {counter} for remove")

    for delete_session in delete_list:
        del sessions[delete_session]
        logging.info(f"Session timeout: {delete_session}")


event_loop = None


async def task_async():
    global session_life_time, event_loop
    await remove_old_sessions()
    await asyncio.sleep(session_life_time)
    event_loop.create_task(task_async())


def add_loop_task(loop):
    global event_loop
    event_loop = loop
    loop.create_task(task_async())
