from typing import List

from Card import Card
from Deck import Deck
from Player import Player

class InvalidActionError(Exception):
    #???
    pass

class InsufficientFundsError(Exception):
    #???
    pass


class GameEngine:
    def __init__(self, players: List[Player], deck: Deck,
                 small_blind: int = 25, big_blind: int = 50):
        """Inicjalizuje graczy, talię, blindy i pulę."""
        self.__players = players
        self.__deck = deck
        self.__small_blind = small_blind
        self.__big_blind = big_blind
        self.__pot = 0
        self.__current_bet = 0


    def play_round(self) -> None:
        """Przeprowadza jedną rundę:
           1. Pobiera blindy
           2. Rozdaje karty
           3. Rundę zakładów
           4. Wymianę kart
           5. Showdown i przyznanie puli
        """
        self.__pot = 0
        self.__current_bet = 0

        #1. Pobiera blindy
        self.__players[0].set_stack_amount(self.__players[0].get_stack_amount() - self.__small_blind)
        self.__players[1].set_stack_amount(self.__players[1].get_stack_amount() - self.__big_blind)
        self.__pot += self.__small_blind + self.__big_blind

        #2. Rozdaje karty
        self.__deck.shuffle()
        self.__deck.deal(self.__players)

        for player in self.__players:
            print(f"{player.get_name()} - Twoje karty: {player.cards_to_str()}")

        #3. Rundę zakładów
        for player in self.__players:
            action = self.__prompt_bet(player, self.__current_bet)
            if action == "raise":
                raise_amount = 100
                self.__current_bet = self.__current_bet + raise_amount
                self.__pot += raise_amount


        #4. Wymianę kart
        for player in self.__players:
            indices_to_exchange = [0, 1]
            player.hand = self.__exchange_cards(player.hand, indices_to_exchange)

        #5. Showdown i przyznanie puli
        winner = self.showdown()
        winner.set_stack_amount( winner.get_stack_amount() + self.__pot)
        print(f"Zwycięzca: {winner.get_name()}, otrzymuje {self.__pot} żetonów.")

    def __prompt_bet(self, player: Player, current_bet: int) -> str:
        """Pobiera akcję od gracza (check/call/raise/fold)."""
        while True:
            try:
                action = input(f"{player.get_name()}, Twój zakład: (check/call/raise/fold): ").strip().lower()
                if action not in ["check", "call", "raise", "fold"]:
                    raise InvalidActionError("Nieprawidłowa akcja!")

                # Obsługuje raise
                if action == "raise":
                    raise_amount = int(input(f"Podaj kwotę podbicia (minimalne podbicie to {current_bet}): "))
                    if raise_amount < current_bet:
                        print(f"Minimalne podbicie to {current_bet}!")
                        continue
                    if raise_amount > player.get_stack_amount():
                        raise InsufficientFundsError("Nie masz wystarczająco żetonów!")
                    return action, raise_amount

                return action, 0

            except ValueError:
                print("Nieprawidłowa kwota! Spróbuj ponownie.")
            except InvalidActionError as e:
                print(e)
            except InsufficientFundsError as e:
                print(e)


    def __exchange_cards(self, hand, indices):
        """Wymienia karty na podstawie podanych indeksów."""
        if any(idx < 0 or idx >= 5 for idx in indices):
            raise IndexError("Indeks karty jest poza dozwolonym zakresem (0-4).")

        new_cards = [self.__deck.cards.pop() for _ in indices]  # pobiera nowe karty z talii
        for idx in sorted(indices, reverse=True):  # usuwamy stare karty
            hand.pop(idx)
        hand.extend(new_cards)  # dodajemy nowe karty
        return hand

    def showdown(self) -> Player:
        """Porównuje układy pozostałych graczy i zwraca zwycięzcę."""

        winner = self.__players[0]# TODO : prawdziwy showdown
        return winner


        #rozgrywka konsolowa, pobiera akcje od gracza przez konsolę, test rozgrywki
        #

