class Player:
    def __init__(self, money, name=""):
        self.__stack_ = money
        self.__name_ = name
        self.__hand_ = []

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
        return old_card

    def get_player_hand(self):
        return tuple(self.__hand_)

    def cards_to_str(self):
        return ', '.join(str(card) for card in self.__hand_)
