import random

from src.Card import Card


class Deck():
    def __init__(self, *args):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['s', 'h', 'd', 'c']
        self.cards = [Card(rank, suit) for suit in suits for rank in ranks]

    def __str__(self):
        return ', '.join(str(card) for card in self.cards)

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, players, num_cards=5):
        for player in players:
            for _ in range(num_cards):
                card = self.cards.pop()
                player.take_card(card)
