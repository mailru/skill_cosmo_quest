from typing import Dict, List


class ButtonsMenuBuilder:
    def __init__(self, state_name=None, buttons=None) -> None:
        self.state_name: str = state_name
        self.buttons: List[Dict] = []
        if buttons is not None:
            for button in buttons:
                self.add_button(**button)

    def add_button(self, text, callback_data={}) -> None:
        payload = {
            "state": self.state_name,
            "text": text,
            "callback_data": callback_data,
        }
        self.buttons.append({"title": text, "payload": payload})

    def get_to_send(self):
        if len(self.buttons) == 0:
            return None

        return self.buttons
