from typing import List
import random
from card import Card
from deck import Deck
from player import Player
import exceptions
import utils
#TODO: check issue with betting that is never 0 because of blinds

class GameEngine:
    def __init__(self, players: List[Player], deck: Deck, small_blind: int = 25, big_blind: int = 50):
        self.players = players
        self.deck = deck
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.current_bet = 0

    def play_round(self) -> None:
        self._reset_round()

        #1. Pobiera blindy
        self._post_blinds()

        #2. Rozdaje karty
        self.deck.shuffle()
        self.deck.deal(self.players, 5)

        #3. Rundę zakładów
        self.betting_round()

        #4. Wymianę kart
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) > 1:
            self._handle_card_exchange(active_players)

        #5. Showdown i przyznanie puli
        winner = self._showdown()
        pot_amount = self.pot
        current_stack = winner.get_stack_amount()
        winner.set_stack_amount(current_stack + pot_amount)
        self.pot = 0
        print(f"Zwycięzca: {winner.get_name()}, otrzymuje {pot_amount} żetonów")

    def _reset_round(self):
        for player in self.players:
            player.folded = False
            player.current_bet = 0
            player.reset_hand()
        self.deck = Deck()
        self.pot = 0
        self.current_bet = 0

    def _post_blinds(self):
        for player in self.players:
            blind = random.choice([self.small_blind, self.big_blind])
            money = player.pay(blind)
            self.pot += money
            self.current_bet += player.pay(blind)

    def betting_round(self):
        active_players = [p for p in self.players if not p.folded]
        last_raiser = -1
        index = 0
        iterations = 0

        while True:
            player = active_players[index]
            player.validate_hand()
            print(f"\n=== Tura gracza: {player.get_name()} ===")
            print(f"Żetony w puli: {self.pot}")
            print(f"Aktualna stawka: {self.current_bet}")

            if player.folded:
                print(f"{player.get_name()} spasował")
                index = (index + 1) % len(active_players)
                for card in player.get_player_hand():
                    self.deck.discard_to_bottom(card)
                player.set_hand([])
                continue

            required = self.current_bet - player.current_bet
            try:
                action = self._prompt_bet(player, required)

                if action == "fold":
                    print(f"{player.get_name()} spasował")
                    player.folded = True

                elif action == "call":
                    print(f"{player.get_name()} wyrównuje stawkę {required}")
                    self.pot += player.pay(required)
                    player.current_bet += required

                elif action == "raise":
                    raise_amount = max(required + self.big_blind, self.big_blind)
                    print(f"{player.get_name()} podbija o {raise_amount}")
                    self.pot += player.pay(raise_amount)
                    player.current_bet += raise_amount
                    self.current_bet = player.current_bet
                    last_raiser = index
                    iterations = 0

            except exceptions.InsufficientFundsError:
                print(f"{player.get_name()} nie ma środków - pas")
                player.folded = True

            active_players = [p for p in active_players if not p.folded]

            if len(active_players) < 2:
                break

            if index == last_raiser and iterations > 0:
                break

            index = (index + 1) % len(active_players)
            iterations += 1

    def _prompt_bet(self, player: Player, required: int) -> str:
        if player.is_human():
            print(f"\nAktualna stawka: {self.current_bet}, Do wyrównania: {required}")
            print(f"{player.get_name()} żetony: {player.get_stack_amount()}")
            print(f"{player.get_name()} karty:", player.cards_to_str())

            while True:
                action = input(f"{player.get_name()} wybierz akcję (fold/check/call/raise): ")
                if action in  {"fold", "raise"}:
                    return action
                elif action == "check":
                    if self.current_bet == 0:
                        return "check"
                    else:
                        print("Nie możesz czekać, gdy ktoś już postawił!")

                elif action == "call":
                    if self.current_bet > 0:
                        return "call"
                    else:
                        print("Nie możesz wyrównać  gdy stawka wynosi 0!")

                else:
                    print("Nieprawidłowa akcja. Dopuszczalne opcje: fold, check, call, raise.")
        else:
            return self._bot_decide_action(player, required)

    def _bot_decide_action(self, player: Player, required: int) -> str:
        if required == 0:
            return "check"

        choices = []
        if player.get_stack_amount() >= required:
            choices.extend(["call"] * 5)
            choices.extend(["fold"] * 3)
        if player.get_stack_amount() >= required + self.big_blind:
            choices.extend(["raise"] * 2)

        if not choices:
            return "fold"

        return random.choice(choices)

    def _handle_card_exchange(self, players: List[Player]):
        for player in players:
            try:
                print(f"\n{player.get_name()} Twoje karty:", player.cards_to_str())

                if player.is_human():
                    indices = list(
                        map(int, input("Podaj indeksy kart do wymiany (0-4, oddzielone spacjami): ").split()))
                else:
                    hand_ranks = [card.rank for card in player.get_player_hand()]
                    numeric_ranks = utils.ranks_to_int(hand_ranks)
                    ex_cards = [i for i, rank in enumerate(numeric_ranks) if rank < 8]
                    indices = random.sample(ex_cards, min(len(ex_cards), random.randint(0, 2)))

                exchanged_cards = self.exchange_cards(player.get_hand(), indices)

                player.set_hand(exchanged_cards)

            except (ValueError, IndexError) as e:
                print(f"Niedozwolona wymiana: {e}. Nie wymieniono żadnych kart.")

    def exchange_cards(self, hand: List[Card], indices: List[int]) -> List[Card]:
        new_hand = hand[:]
        old_cards = []

        for idx in indices:
            old_card = new_hand[idx]
            new_card = self.deck.draw()
            new_hand[idx] = new_card
            old_cards.append(old_card)

        for old_card in old_cards:
            self.deck.discard_to_bottom(old_card)

        return new_hand

    def _showdown(self) -> Player:
        active_players = [p for p in self.players if not p.folded]
        if not active_players:
            raise exceptions.GameError("Brak aktywnych graczy w showdown")

        if len(active_players) == 1:
            return active_players[0]

        rankings = [(utils.evaluate_hand(p.get_player_hand()), p) for p in active_players]
        rankings.sort(reverse=True, key=lambda x: x[0])
        return rankings[0][1]