import asyncio
import configparser
import logging
import os
import os.path
import random
import traceback
from pathlib import Path
from typing import Dict, Optional

from aiohttp import web

from . import audios, graphite_statistics, phrases, quest, sessions, utils

logging.basicConfig(level=logging.DEBUG)
logging.info("Start cosmo_quest_skill")

PACKAGE_DIR = Path(__file__).parent

config_paths = [
    Path("/config/skill_config.cfg"),
    PACKAGE_DIR.parent.parent / "skill_config.cfg",
]

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
is_found: bool = False
for config_path in config_paths:
    if config_path.exists():
        config.read(config_path)
        is_found = True
        break

if not is_found:
    raise Exception(f"Config not found in {config_paths}")


HOST_IP = config.get("main", "host")
HOST_PORT = int(config.get("main", "port"))
SESSION_LIFE_TIME_SEC = int(config.get("main", "session_life_time_sec"))
AUDIO_FILES_PATH = config.get("main", "audio_files_path")

GRAPHITE_HOST = config.get("graphite", "host")
GRAPHITE_PREFIX = config.get("graphite", "prefix")
GRAPHITE_INTERVAL = int(config.get("graphite", "interval"))

graphite_sender = graphite_statistics.GraphiteSender(GRAPHITE_HOST, GRAPHITE_PREFIX)

STATE_HELLO = 0
STATE_QUEST = 1
STATE_QUEST_COMPLETED = 2
STATE_HAVE_SAVED_QEUSTION = 3


async def marusya_cosmo_quest(request_data) -> web.Response:
    global graphite_sender
    clear_session = False
    request = await request_data.json()
    logging.info(f"Request: \n {request}\n\n")

    response = {}
    response["version"] = request["version"]
    response["session"] = request["session"]
    response["response"] = {"end_session": False}
    user_session = sessions.get_session(request["session"]["user_id"])

    if request["session"]["new"]:
        if "current_state" in user_session.info and (
            user_session.info["current_state"] == STATE_QUEST
            or user_session.info["current_state"] == STATE_HAVE_SAVED_QEUSTION
        ):
            utils.set_response(
                response,
                text_and_tts=random.choice(phrases.HAVE_SAVED_PHRASES),
                buttons=phrases.HAVE_SAVED_BUTTONS,
            )
            user_session.info["current_state"] = STATE_HAVE_SAVED_QEUSTION
        else:
            utils.set_response(
                response,
                text_and_tts=random.choice(phrases.HELLO_PHRASES),
                buttons=phrases.HELLO_BUTTONS,
            )
            user_session.info["current_state"] = STATE_HELLO
            user_session.info["user_vars"] = {}
            user_session.info["user_vars"]["callsign"] = "DEFAULT"
            graphite_sender.inc("quest_start")
            print("save hello")
    else:
        prepared_text: Optional[str] = utils.get_prepared_text(request)

        error_response = False
        if prepared_text is not None:
            if prepared_text in phrases.STOP_PHRASES:
                utils.set_response(
                    response, text_and_tts=random.choice(phrases.GOODBYE_PHRASES)
                )

                response["response"]["end_session"] = True
            else:
                try:
                    play_audio: bool = True
                    current_state: int = user_session.info["current_state"]
                    current_stage: Optional[quest.Stage] = None

                    # Start message answer
                    if (
                        current_state == STATE_HELLO
                        or current_state == STATE_QUEST_COMPLETED
                    ):
                        if prepared_text not in phrases.NOT_EXIT_PHRASES:
                            utils.set_response(
                                response,
                                text_and_tts=random.choice(phrases.GOODBYE_PHRASES),
                            )
                            clear_session = True
                            response["response"]["end_session"] = True
                        else:
                            current_stage = quest.get_root_stage()
                            user_session.info["current_state"] = STATE_QUEST
                    elif current_state == STATE_HAVE_SAVED_QEUSTION:
                        if prepared_text in phrases.HAVE_SAVED_ANSWERS_NEW:
                            current_stage = quest.get_root_stage()
                            user_session.info["current_state"] = STATE_QUEST
                        elif prepared_text in phrases.HAVE_SAVED_ANSWERS_EXIT:
                            utils.set_response(
                                response,
                                text_and_tts=random.choice(phrases.GOODBYE_PHRASES),
                            )
                            response["response"]["end_session"] = True
                        else:
                            current_stage = quest.get_stage_by_id(
                                user_session.info["current_stage"]
                            )
                            user_session.info["current_state"] = STATE_QUEST
                    else:
                        if prepared_text in phrases.SIMPLE_REPEAT_PHRASES:
                            current_stage = quest.get_stage_by_id(
                                user_session.info["current_stage"]
                            )
                            play_audio = False
                        elif prepared_text in phrases.FULL_REPEAT_PHRASES:
                            current_stage = quest.get_stage_by_id(
                                user_session.info["current_stage"]
                            )
                        else:
                            transition = quest.get_stage_by_id(
                                user_session.info["current_stage"]
                            ).get_transition(prepared_text)

                            if transition is not None:
                                current_stage = transition.get_dest_stage()
                                transition.on_go(prepared_text, user_session.info)
                            else:
                                current_stage = None

                    if not response["response"]["end_session"]:
                        response_text_and_tts = [[], ""]

                        if current_stage is not None:
                            current_stage_strong: quest.Stage = current_stage
                            current_stage_strong.add_response_text_and_tts(
                                response_text_and_tts,
                                user_session.info["user_vars"],
                                play_audio,
                            )

                            # Переходим в следующее состояние, если текущее не требует ввода пользователя
                            while (
                                current_stage_strong.is_unconditional()
                                and not current_stage_strong.is_end()
                            ):
                                transition = current_stage_strong.get_transition()
                                current_stage = transition.get_dest_stage()
                                transition.on_go(None, user_session.info)
                                if current_stage is not None:
                                    current_stage_strong = current_stage
                                else:
                                    raise ValueError(
                                        "The next stage of non and stage was None"
                                    )

                                current_stage_strong.add_response_text_and_tts(
                                    response_text_and_tts,
                                    user_session.info["user_vars"],
                                    play_audio,
                                )

                            buttons = current_stage_strong.buttons

                            if current_stage_strong.is_end():
                                """
                                response_text_and_tts[
                                    0
                                ] += f"\n{phrases.QUEST_COMPLETE_PHRASE[0]}"
                                response_text_and_tts[1] += (
                                    "\n" + phrases.QUEST_COMPLETE_PHRASE[1]
                                )
                                """
                                buttons = phrases.EXIT_QUESTION_BUTTONS
                                user_session.info[
                                    "current_state"
                                ] = STATE_QUEST_COMPLETED

                                clear_session = True
                                response["response"]["end_session"] = True
                                graphite_sender.inc("all_complete")

                            utils.set_response(
                                response,
                                text_and_tts=(
                                    response_text_and_tts[0],
                                    response_text_and_tts[1],
                                ),
                                buttons=buttons,
                            )

                            user_session.info["current_stage"] = current_stage_strong.id
                        else:
                            error_response = True

                except Exception:
                    traceback.print_exc()
                    error_response = True
                    clear_session = True
        else:
            error_response = True

        if error_response:
            utils.set_response(
                response,
                text="Простите, я не могу ответить на ваш запрос",
                tts="Простите, я не могу ответить на ваш запрос",
            )
            response["response"]["end_session"] = True

        # if response["response"]["end_session"]:
        #    user_session.remove()

    print(f"Current info: {user_session.info}")

    if clear_session:
        user_session.remove()
    else:
        user_session.update()
    logging.info(f"Response: \n {response}\n\n")
    return web.json_response(response)


async def get_main(request_data) -> web.StreamResponse:
    graphite_sender.inc("query_get")
    return web.json_response({"status": "OK", "tag": "2"})


async def get_readiness_probe(request_data) -> web.StreamResponse:
    return web.json_response(healthz())


async def get_liveness_probe(request_data) -> web.StreamResponse:
    return web.json_response(healthz())


async def get_startup_probe(request_data) -> web.StreamResponse:
    return web.json_response(healthz())


def healthz() -> Dict:
    return {"status": "OK"}


def init_app(loop) -> web.Application:
    app = web.Application(loop=loop, client_max_size=100000000)
    app.router.add_post("/skill_cosmo_quest", marusya_cosmo_quest)
    app.router.add_post("/", marusya_cosmo_quest)
    app.router.add_get("/", get_main)
    app.router.add_get("/skill_cosmo_quest", get_main)
    app.router.add_get("/readiness_probe", get_readiness_probe)
    app.router.add_get("/liveness_probe", get_liveness_probe)
    app.router.add_get("/startup_probe", get_startup_probe)

    return app


loop = asyncio.get_event_loop()
app = init_app(loop)
quest.init()
audios.init(AUDIO_FILES_PATH)


if __name__ == "__main__":
    try:
        graphite_sender.add_loop_task(loop, GRAPHITE_INTERVAL)
        web.run_app(app, host=HOST_IP, port=HOST_PORT)
    except web.GracefulExit:
        print("server was stopped")
