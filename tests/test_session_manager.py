import unittest
import os
import shutil

from src.fileops.session_manager import SessionManager
from src.card import Card
from src.player import Player
from src.deck import Deck

class TestSessionManager(unittest.TestCase):
    TEST_DIR = "/data"

    def test_save_and_load_session(self):
        players = [
            Player(1000, "Alice", True),
            Player(800, "BotBob", False)
        ]
        players[0].set_hand([Card("A", "s"), Card("K", "d"), Card("5", "h"), Card("2", "c"), Card("9", "s")])
        players[1].set_hand([Card("J", "h"), Card("Q", "h"), Card("7", "c"), Card("8", "s"), Card("3", "d")])

        deck = Deck()
        deck.cards = [Card("4", "h"), Card("6", "c")]

        session_data = {
            "players": players,
            "deck": deck
        }

        manager = SessionManager(data_dir=self.TEST_DIR)
        manager.save_session(session_data)
        game_id = session_data["game_id"]

        loaded_session = manager.load_session(str(game_id))
        loaded_players = loaded_session["players"]
        loaded_deck = loaded_session["deck"]

        self.assertEqual(len(loaded_players), 2)
        self.assertEqual(loaded_players[0].get_name(), "Alice")
        self.assertEqual(loaded_players[1].get_name(), "BotBob")

        self.assertEqual(len(loaded_players[0].get_hand()), 5)
        self.assertEqual(len(loaded_players[1].get_hand()), 5)

        self.assertEqual(len(loaded_deck.cards), 2)
        self.assertEqual(loaded_deck.cards[0].rank, "4")
        self.assertEqual(loaded_deck.cards[0].suit, "h")

if __name__ == "__main__":
    unittest.main()