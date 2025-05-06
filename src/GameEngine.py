from typing import List, Tuple
import random
from Card import Card
from Deck import Deck
from Player import Player
import exceptions


class GameEngine:
    def __init__(self, players: List[Player], deck: Deck, small_blind: int = 25, big_blind: int = 50):
        self.players = players
        self.deck = deck
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.current_bet = 0

    def play_round(self) -> None:
        for player in self.players:
            player.folded = False
            player.current_bet = 0

        #1. Pobiera blindy
        self._post_blinds()

        #2. Rozdaje karty
        self.deck.shuffle()
        self.deck.deal(self.players, 5)

        #3. Rundę zakładów
        self._handle_betting_round()

        #4. Wymianę kart
        active_players = [p for p in self.players if not p.folded]
        self._handle_card_exchange(active_players)

        #5. Showdown i przyznanie puli
        winner = self._showdown()
        pot_amount = self.pot
        current_stack = winner.get_stack_amount()
        winner.set_stack_amount(current_stack + pot_amount)
        self.pot = 0
        print(f"Zwycięzca: {winner.get_name()}, otrzymuje {pot_amount} żetonów")

    def _post_blinds(self):
        if len(self.players) >= 2:
            self.pot += self.players[0].pay(self.small_blind)
            self.pot += self.players[1].pay(self.big_blind)
            self.current_bet = self.big_blind

    def _handle_betting_round(self):
        active_players = [p for p in self.players if not p.folded]
        last_raiser = -1
        index = 0
        iterations = 0

        while True:
            player = active_players[index]

            print(f"\n=== Tura gracza: {player.get_name()} ===")
            print(f"Żetony w puli: {self.pot}")
            print(f"Aktualna stawka: {self.current_bet}")

            if player.folded:
                print(f"{player.get_name()} spasował")
                index = (index + 1) % len(active_players)
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
            print(f"Twoje żetony: {player.get_stack_amount()}")
            print("Twoje karty:", player.cards_to_str())

            while True:
                action = input("Wybierz akcję (fold/call/raise): ").strip().lower()
                if action in {"fold", "call", "raise"}:
                    return action
                print("Nieprawidłowa akcja. Dopuszczalne opcje: fold/call/raise")
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
                if player.is_human():
                    print("\nTwoje karty:", player.cards_to_str())
                    indices = list(
                        map(int, input("Podaj indeksy kart do wymiany (0-4, oddzielone spacjami): ").split()))
                else:
                    hand_ranks = [card.rank for card in player.get_player_hand()]
                    bad_cards = [i for i, rank in enumerate(hand_ranks) if rank < 8]
                    indices = random.sample(bad_cards, min(len(bad_cards), random.randint(0, 2)))

                for idx in indices:
                    new_card = self.deck.draw()
                    old_card = player.change_card(new_card, idx)
                    self.deck.discard_to_bottom(old_card)

            except (ValueError, IndexError) as e:
                print(f"Invalid exchange: {e}. No cards changed.")

    def _exchange_cards(self, hand: List[Card], indices: List[int]) -> List[Card]:
        if any(not 0 <= idx < 5 for idx in indices):
            raise IndexError("Nieprawidłowy indeks karty (dopuszczalne 0-4)")

        new_hand = hand.copy()
        for idx in sorted(indices, reverse=True):
            old_card = new_hand.pop(idx)
            self.deck.discard_to_bottom(old_card)
            new_hand.insert(idx, self.deck.draw())
        return new_hand

    def _showdown(self) -> Player:
        active_players = [p for p in self.players if not p.folded]
        if not active_players:
            raise exceptions.GameError("Brak aktywnych graczy w showdown")

        if len(active_players) == 1:
            return active_players[0]

        rankings = [(self._evaluate_hand(p.get_player_hand()), p) for p in active_players]
        rankings.sort(reverse=True, key=lambda x: x[0])
        return rankings[0][1]

    @staticmethod
    def _evaluate_hand(hand: List[Card]) -> Tuple[int, List[int]]:
        ranks = sorted([c.rank for c in hand], reverse=True)
        suits = [c.suit for c in hand]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        count_values = sorted(rank_counts.values(), reverse=True)
        unique_ranks = sorted(rank_counts.keys(), reverse=True)

        flush = len(set(suits)) == 1

        straight = False
        if len(unique_ranks) == 5:
            if ranks[0] - ranks[-1] == 4:
                straight = True
            elif set(ranks) == {14, 2, 3, 4, 5}:
                straight = True
                ranks = [5, 4, 3, 2, 1]

        if straight and flush:
            return (8, [ranks[0]])
        if 4 in count_values:
            four_rank = [r for r, count in rank_counts.items() if count == 4][0]
            kicker = [r for r in ranks if r != four_rank][0]
            return (7, [four_rank, kicker])
        if 3 in count_values and 2 in count_values:
            three_rank = [r for r, count in rank_counts.items() if count == 3][0]
            pair_rank = [r for r, count in rank_counts.items() if count == 2][0]
            return (6, [three_rank, pair_rank])
        if flush:
            return (5, ranks)
        if straight:
            return (4, [ranks[0]])
        if 3 in count_values:
            three_rank = [r for r, count in rank_counts.items() if count == 3][0]
            kickers = sorted([r for r in ranks if r != three_rank], reverse=True)
            return (3, [three_rank] + kickers)
        if count_values.count(2) == 2:
            pairs = sorted([r for r, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [r for r in ranks if r not in pairs][0]
            return (2, pairs + [kicker])
        if 2 in count_values:
            pair_rank = [r for r, count in rank_counts.items() if count == 2][0]
            kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
            return (1, [pair_rank] + kickers)
        return (0, ranks)