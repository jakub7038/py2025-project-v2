import json
import os
from typing import List

from ..card import Card
from ..player import Player
from ..deck import Deck

class SessionManager:
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_next_game_id(self) -> int:
        existing_ids = []

        for filename in os.listdir(self.data_dir):
            if filename.startswith("session_") and filename.endswith(".json"):
                try:
                    num_part = filename[len("session_"):-len(".json")]
                    existing_ids.append(int(num_part))
                except ValueError:
                    continue

        return max(existing_ids, default=0) + 1

    def save_session(self, session: dict) -> None:
        game_id = session.get("game_id")

        if not game_id:
            game_id = self._get_next_game_id()
            session["game_id"] = game_id

        serializable_session = {
            "game_id": game_id,
            "players": [player.to_dict() for player in session.get("players", [])],
            "deck": session.get("deck").to_dict() if session.get("deck") else {},
        }

        filename = os.path.join(self.data_dir, f"session_{game_id}.json")

        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(serializable_session, file, indent=2)
        except IOError as e:
            print(f"Błąd zapisu pliku: {e}")
            raise

    def load_session(self, game_id: str) -> dict:
        filename = os.path.join(self.data_dir, f"session_{game_id}.json")
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Convert dicts back to objects
            players = [Player.from_dict(pdata) for pdata in data.get("players", [])]
            deck = Deck.from_dict(data.get("deck", {}))

            return {
                "game_id": data.get("game_id"),
                "players": players,
                "deck": deck,
            }

        except FileNotFoundError:
            print(f"Sesji nie ma: {filename}")
            raise
        except json.JSONDecodeError:
            print(f"Json jest niepoprawny: {filename}")
            raise