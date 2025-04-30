class Player:

    def __init__(self, money, name=""):
        self.__stack_ = money
        self.__name_ = name
        self.__hand_ = []

    def take_card(self, card):
        self.__hand_.append(card)

    def get_stack_amount(self):
        return self.__stack_

    def change_card(self, card, index):
        temp_card = card
        card = self.__hand_[index]
        self.__hand_[index] = temp_card
        return card

    def get_player_hand(self):
        return tuple(self.__hand_)

    def cards_to_str(self):
        return ', '.join(str(card) for card in self.__hand_)
