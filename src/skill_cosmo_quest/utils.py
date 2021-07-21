from typing import Dict, List, Optional


def set_response(
    response, text_and_tts=None, text=None, tts=None, buttons=None, speak_text=True
) -> None:
    if text_and_tts is not None:
        text = text_and_tts[0]
        tts = text_and_tts[1]

    if (tts is None) and speak_text:
        tts = text

    if text is not None:
        response["response"]["text"] = text

    if tts is not None:
        """
        response["response"]["tts_type"] = "ssml"
        response["response"][
            "ssml"
        ] = f'<?xml version="1.0" encoding="UTF-8"?><speak version="1.1" xmlns:mailru="http://vc.go.mail.ru" lang="ru">\n{tts}\n</speak>'
        """
        response["response"]["tts"] = tts

    if buttons is not None:
        response["response"]["buttons"] = buttons


def is_button_request(request):
    return request["request"]["type"] == "ButtonPressed"


def get_button_info(request) -> Dict:
    return request["request"]["payload"]


def get_request_text(request) -> Optional[str]:
    if request["request"]["type"] == "SimpleUtterance":
        return request["request"]["command"]
    elif is_button_request(request):
        return get_button_info(request)["text"]
    else:
        return None


NOT_LETTERS = [",", ".", "!", "?"]


def prepare_phrase(phrase) -> str:
    result = ""
    for symbol in phrase:
        if symbol not in NOT_LETTERS:
            result += symbol
    return result.replace("ё", "е").lower()


def prepare_phrases_list(prepare_list) -> List[str]:
    result = []
    for phrase in prepare_list:
        result.append(prepare_phrase(phrase))
    return result


def get_prepared_text(request) -> Optional[str]:
    result = None
    result = request["request"].get("command", None)
    if result is None:
        if request["request"]["type"] == "SimpleUtterance":
            result = request["request"].get("command", None)
        elif is_button_request(request):
            result = get_button_info(request)["text"]

    if result is not None:
        result = prepare_phrase(result)
    return result
