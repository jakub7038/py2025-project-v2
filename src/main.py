from Deck import Deck
from Player import Player
from GameEngine import GameEngine

if __name__ == "__main__":
    deck = Deck()
    players = [
        Player(1000, "Gracz 1"),
        Player(1000, "Bot 1"),
        Player(1000, "Bot 2")
    ]
    game = GameEngine(players, deck)
    game.play_round()