from typing import List
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

    def play_round(self) -> None:
        for player in self.players:
            player.folded = False

        #1. Pobiera blindy
        for player in self.players:
            self.pot += player.pay(self.small_blind)
            self.pot += player.pay(self.big_blind) # kto ma brać blindy??

        #2. Rozdaje karty
        self.deck.shuffle()
        self.deck.deal(self.players, 5)

        #3. Rundę zakładów
        current_bet = self.big_blind * len(self.players)  # Nowa logika stawek
        active_players = [p for p in self.players if not p.folded]
        self.handle_betting_round(active_players, current_bet)

        #4. Wymianę kart
        for player in active_players:
            if player.folded:
                continue
            try:
                if player.is_human():
                    print("Twoje karty:", player.cards_to_str())
                    indices = list(map(int, input("Podaj indeksy do wymiany (0-4 oddzielone spacją): ").split()))
                else:
                    indices = random.sample(range(5), random.randint(0, 2))

                new_hand = self.exchange_cards(list(player.get_player_hand()), indices)
                for i, idx in enumerate(indices):
                    player.change_card(new_hand[idx], idx)
            except (ValueError, IndexError) as e:
                print(f"Błąd: {e}. Pomijanie wymiany kart.")

        #5. Showdown i przyznanie puli
        winner = self.showdown()

        current_stack = winner.__dict__.get('_Player__stack_', 0)
        winner.__dict__['_Player__stack_'] = current_stack + self.pot

        winner_name = winner.__dict__.get('_Player__name_', 'Unknown Player')
        print(f"Zwycięzca: {winner_name}, otrzymuje {self.pot} żetonów")

    def handle_betting_round(self, players: List[Player], current_bet: int):
        for player in players:
            if player.folded:
                continue
            try:
                action = self.prompt_bet(player, current_bet)
                if action == "fold":
                    player.folded = True
                elif action == "call":
                    player.pay(current_bet)
                    self.pot += current_bet
                elif action == "raise":
                    new_bet = current_bet + 10
                    player.pay(new_bet)
                    self.pot += new_bet
                    current_bet = new_bet
            except (exceptions.InvalidActionError, exceptions.InsufficientFundsError):
                player.folded = True

    def prompt_bet(self, player: Player, current_bet: int) -> str:
        try:
            if player.is_human():
                print(f"Aktualna stawka: {current_bet}")
                print("Twoje żetony:", player.get_stack_amount())
                action = input("Wybierz akcję (check/call/raise/fold): ").lower().strip()
                if action not in {"check", "call", "raise", "fold"}:
                    raise exceptions.InvalidActionError("Nieprawidłowa akcja")
                return action
            else:
                return random.choice(["call", "fold", "check"])
        except Exception as e:
            raise exceptions.InvalidActionError(f"Błąd akcji: {str(e)}")

    def exchange_cards(self, hand: List[Card], indices: List[int]) -> List[Card]:
        if any(idx < 0 or idx >= 5 for idx in indices):
            raise IndexError("Nieprawidłowy indeks karty (dopuszczalne 0-4)")

        new_hand = hand.copy()
        for idx in indices:
            new_card = self.deck.draw()
            old_card = new_hand[idx]
            self.deck.discard_to_bottom(old_card)
            new_hand[idx] = new_card
        return new_hand

    def showdown(self) -> Player:
        active_players = [p for p in self.players if not p.folded]
        if not active_players:
            raise exceptions.GameError("Brak aktywnych graczy")
        return active_players[0]