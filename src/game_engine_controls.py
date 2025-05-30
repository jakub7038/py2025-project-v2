from src.game_engine import GameEngine
from src.player import Player
import random
from typing import List
from src.utils import ranks_to_int

class DerivedGameEngine(GameEngine):
    def __init__(self, players, deck, gui_handler, small_blind=25, big_blind=50):
        super().__init__(players, deck, small_blind, big_blind)
        self.gui = gui_handler

    def prompt_bet(self, player: Player, current_bet: int) -> str:
        if not player.is_human():
            return self._bot_decide_action(player, current_bet)

        self.gui.show_current_bet(self.current_bet, current_bet)
        self.gui.show_player_info(player.get_name(), player.get_stack_amount(), player.cards_to_str())
        action = self.gui.prompt_action(
            options=["fold", "check", "call", "raise"],
            can_check=(current_bet == 0),
            can_call=(current_bet > 0),
            can_raise=True
        )
        if action == "raise":
            min_raise = max(self.big_blind, current_bet + 1)
            raise_amt = self.gui.prompt_raise_amount(min_amount=min_raise)
            self.gui.last_raise_amount = raise_amt
        return action

    def _get_raise_amount(self, current_bet):
        amount = getattr(self.gui, 'last_raise_amount', None)
        if amount is None:
            raise ValueError("No raise amount provided by GUI handler.")
        return amount

    def _handle_card_exchange(self, players: List[Player]):
        for player in players:
            try:
                if not player.is_human():
                    hand_ranks = [card.rank for card in player.get_player_hand()]
                    numeric_ranks = ranks_to_int(hand_ranks)
                    ex_cards = [i for i, rank in enumerate(numeric_ranks) if rank < 8]
                    indices = random.sample(ex_cards, min(len(ex_cards), random.randint(0, 2)))
                else:
                    self.gui.show_player_cards(player.get_name(), player.cards_to_str())
                    indices = self.gui.prompt_exchange_indices(max_indices=3)

                    if not isinstance(indices, list):
                        raise ValueError("Oczekiwano listy indeksów")
                    hand_size = len(player.get_hand())
                    unique = set()
                    valid_indices = []
                    for idx in indices:
                        if not isinstance(idx, int):
                            raise ValueError(f"Nieprawidłowy indeks: {idx}")
                        if idx < 0 or idx >= hand_size:
                            raise ValueError(f"Indeks poza zakresem: {idx}")
                        if idx in unique:
                            continue
                        unique.add(idx)
                        valid_indices.append(idx)
                    indices = valid_indices

                exchanged = self.exchange_cards(player.get_hand(), indices)
                player.set_hand(exchanged)

            except Exception as e:
                if player.is_human():
                    self.gui.show_error(f"Niedozwolona wymiana: {e}. Nie wymieniono kart.")
                continue
