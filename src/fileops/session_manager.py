import json
import os
from datetime import datetime
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
        if not session.get("completed_round", False):
            raise ValueError("Zapis sesji możliwy tylko po zakończonej rundzie.")

        game_id = session.get("game_id")
        if not game_id:
            game_id = self._get_next_game_id()
            session["game_id"] = game_id

        self._save_game_state(session, game_id)
        self._append_hand_history(session, game_id)

    def _save_game_state(self, session: dict, game_id: int) -> None:
        serializable_state = {
            "game_id": game_id,
            "players": [player.to_dict() for player in session.get("players", [])],
            "deck": session.get("deck").to_dict() if session.get("deck") else {},
        }

        filename = os.path.join(self.data_dir, f"session_{game_id}.json")
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(serializable_state, file, indent=2)
        except IOError as e:
            print(f"Błąd zapisu pliku: {e}")
            raise

    def _append_hand_history(self, session: dict, game_id: int) -> None:
        log_entry = {
            "game_id": str(game_id),
            "timestamp": datetime.now().isoformat(),
            "stage": session.get("stage", "unknown"),
            "players": [
                {"id": idx + 1, "name": player.get_name(), "stack": player.get_stack_amount()}
                for idx, player in enumerate(session.get("players", []))
            ],
            "deck": [f"{card.rank}{card.suit}" for card in session.get("deck").cards],
            "hands": {
                str(idx + 1): [f"{card.rank}{card.suit}" for card in player.get_hand()]
                for idx, player in enumerate(session.get("players", []))
            },
            "bets": session.get("bets", []),
            "current_player": session.get("current_player"),
            "pot": session.get("pot", 0)
        }

        filename = os.path.join(self.data_dir, f"session_{game_id}_log.jsonl")
        try:
            with open(filename, 'a', encoding='utf-8') as log_file:
                log_file.write(json.dumps(log_entry) + '\n')
        except IOError as e:
            print(f"Błąd zapisu logu: {e}")
            raise

    def load_session(self, game_id: str) -> dict:
        filename = os.path.join(self.data_dir, f"session_{game_id}.json")
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
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

    def save_config(self, config: dict) -> None:
        config_path = os.path.join(self.data_dir, "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Błąd zapisu konfiguracji: {e}")
            raise

    def load_config(self) -> dict:
        config_path = os.path.join(self.data_dir, "config.json")
        default_config = {
            "starting_stack": 100,
            "small_blind": 25,
            "big_blind": 50,
            "difficulty": "normal"
        }

        if not os.path.exists(config_path):
            return default_config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Błąd odczytu konfiguracji, używam domyślnej: {e}")
            return default_config
