from exceptions import InsufficientFundsError, InvalidHandError

class Player:
    def __init__(self, money, name="", is_human = False):
        self.__stack_ = money
        self.__name_ = name
        self.__hand_ = []
        self.__is_human_ = is_human
        self.folded = False
        self.current_bet = 0
        self.last_action = None

    def take_card(self, card):
        self.__hand_.append(card)

    def get_stack_amount(self):
        return self.__stack_

    def set_stack_amount(self, amount):
        self.__stack_ = amount

    def get_name(self):
        return self.__name_

    def set_name(self, name):
        self.__name_ = name

    def get_hand(self):
        return self.__hand_

    def change_card(self, card, idx):
        old_card = self.__hand_[idx]
        self.__hand_[idx] = card
        self.validate_hand()
        return old_card

    def get_player_hand(self):
        return tuple(self.__hand_)

    def cards_to_str(self):
        return ', '.join(str(card) for card in self.__hand_)

    def pay(self, amount):
        if self.__stack_ < amount:
            raise InsufficientFundsError()
        self.__stack_ -= amount
        return amount

    def is_human(self):
        return self.__is_human_

    def set_hand(self, hand):
        self.__hand_ = hand

    def reset_hand(self):
        self.__hand_ = []
        self.current_bet = 0

    def set_last_action(self, action):
        self.last_action = action

    def validate_hand(self):
        if len(self.__hand_) != 5:
            raise InvalidHandError("renka nie ma 5 kart.")

        seen_cards = set()
        for card in self.__hand_:
            if card in seen_cards:
                raise InvalidHandError(f"Duplikat karty: {card}")
            seen_cards.add(card)