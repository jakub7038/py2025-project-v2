import random

from src.card import Card


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

    def draw(self):
        if not self.cards:
            raise ValueError("Deck is empty")
        return self.cards.pop(0)

    def discard_to_bottom(self, card):
        self.cards.append(card)

    def to_dict(self):
        return {
            "cards": [card.to_dict() for card in self.cards]
        }

    @classmethod
    def from_dict(cls, data):
        deck = cls()
        deck.cards = [Card.from_dict(c) for c in data["cards"]]
        return deck