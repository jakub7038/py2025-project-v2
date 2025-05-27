from typing import List
import random
from src.card import Card
from src.deck import Deck
from src.player import Player
from src.exceptions import InvalidActionError, InsufficientFundsError, GameError
from src.utils import evaluate_hand, ranks_to_int, hand_rank_names


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
        winner = self.showdown()
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
            player.last_action = None
        self.deck = Deck()
        self.pot = 0
        self.current_bet = 0

    def _post_blinds(self):
        blinds = []
        for player in self.players:
            blind = random.choice([self.small_blind, self.big_blind])
            money = player.pay(blind)
            self.pot += money
            player.current_bet = blind
            blinds.append(blind)
        self.current_bet = max(blinds) if blinds else 0

    def betting_round(self):
        active = [p for p in self.players if not p.folded]
        if len(active) < 2:
            print("Za mało graczy, aby kontynuować")
            return

        for p in active:
            p.last_action = None

        current_pos = 0
        while True:
            active = [p for p in self.players if not p.folded]
            if len(active) < 2:
                print("Pozostał tylko jeden gracz, kończę rundę")
                return

            cycle_complete = True
            start_pos = current_pos

            for i in range(len(active)):
                pos = (start_pos + i) % len(active)
                player = active[pos]
                current_bet = self.current_bet - player.current_bet

                try:
                    action = self.prompt_bet(player, current_bet)
                    player.last_action = action
                    print(f"{player.get_name()} wybrał akcję {action}")

                    if action == 'fold':
                        player.folded = True
                        if len([p for p in self.players if not p.folded]) == 1:
                            winner = next(p for p in self.players if not p.folded)
                            print(f"{winner.get_name()} wygrywa domyślnie")
                            return

                    elif action == 'call':
                        if current_bet > 0:
                            self.pot += player.pay(current_bet)
                            player.current_bet += current_bet
                            print(f"Spłacono {current_bet}, łączny zakład: {player.current_bet}")
                        else:
                            print("Nic do wyrównania")
                    elif action == 'check':
                        if current_bet > 0:
                            raise InvalidActionError("Nie można czekać przy istniejącym zakładzie")
                        print("Czekam")

                    elif action == 'raise':
                        raise_amt = self._get_raise_amount(current_bet)
                        total = current_bet + raise_amt
                        self.pot += player.pay(total)
                        player.current_bet += total
                        self.current_bet = player.current_bet
                        print(f"Podbito do {self.current_bet}")

                        cycle_complete = False
                        current_pos = (pos + 1) % len(active)
                        break

                except (InsufficientFundsError, InvalidActionError) as e:
                    print(f"{e}, traktowane jako spasowanie")
                    player.folded = True

            if cycle_complete:
                unmatched = any(p.current_bet != self.current_bet for p in active)
                all_checked = all(p.last_action == 'check' for p in active)
                if not unmatched or all_checked:
                    print("Runda zakładów zakończona")
                    return

            # Reset for next cycle if a raise occurred
            if not cycle_complete:
                continue

    def _get_raise_amount(self, current_bet):
        while True:
            try:
                amount = int(input("Kwota podbicia: "))
            except ValueError:
                print("Nieprawidłowa liczba, spróbuj ponownie.")
                continue

            min_raise = max(self.big_blind, current_bet + 1)
            if amount < min_raise:
                print(f"Minimalne podbicie to {min_raise}")
                continue

            return amount


    def prompt_bet(self, player: Player, current_bet: int) -> str:
        if player.is_human():
            print(f"\nAktualna stawka: {self.current_bet}, Do wyrównania: {current_bet}")
            print(f"{player.get_name()} żetony: {player.get_stack_amount()}")
            print(f"{player.get_name()} karty:", player.cards_to_str())

            while True:
                action = input(f"{player.get_name()} wybierz akcję (fold/check/call/raise): ").lower()
                if action == "check":
                    if current_bet == 0:
                        return "check"
                    print("Nie możesz czekać - musisz wyrównać!")
                elif action == "call":
                    if current_bet > 0:
                        return "call"
                    print("Nie możesz wyrównać przy zerowej stawce!")
                elif action == "raise":
                    return "raise"
                elif action == "fold":
                    return "fold"
                else:
                    print("Nieprawidłowa akcja. Dopuszczalne opcje: fold, check, call, raise.")
        else:
            return self._bot_decide_action(player, current_bet)

    def _bot_decide_action(self, player: Player, current_bet: int) -> str:
        if current_bet == 0:
            return "check" if random.random() < 0.7 else "raise"

        choices = []
        if player.get_stack_amount() >= current_bet:
            choices.extend(["call"] * 5)
            choices.extend(["fold"] * 3)
        if player.get_stack_amount() >= current_bet + self.big_blind:
            choices.extend(["raise"] * 2)

        return random.choice(choices) if choices else "fold"

    def _handle_card_exchange(self, players: List[Player]):
        for player in players:
            try:
                print(f"\n{player.get_name()} Twoje karty:", player.cards_to_str())

                if player.is_human():
                    indices = list(
                        map(int, input("Podaj indeksy kart do wymiany (0-4, oddzielone spacjami): ").split()))
                else:
                    hand_ranks = [card.rank for card in player.get_player_hand()]
                    numeric_ranks = ranks_to_int(hand_ranks)
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

    def showdown(self) -> Player:
        active_players = [p for p in self.players if not p.folded]
        if not active_players:
            raise GameError("Brak aktywnych graczy w showdown")

        print("\n--- SHOWDOWN ---")
        rankings = []

        for player in active_players:
            hand = player.get_player_hand()
            rank_value, tiebreakers = evaluate_hand(hand)
            hand_name = hand_rank_names[rank_value]
            card_strs = [str(card) for card in hand]

            print(f"{player.get_name():<15} | {hand_name:<17} | {' '.join(card_strs)}")

            rankings.append((rank_value, tiebreakers, player))

        rankings.sort(reverse=True, key=lambda x: (x[0], x[1]))

        winning_player = rankings[0][2]
        return winning_player