from src.game_engine import GameEngine
from src.utils import ranks_to_int, evaluate_hand, hand_rank_names
import random


class GuiGameEngine(GameEngine):
    def __init__(self, players, deck, small_blind, big_blind, gui_handler):
        super().__init__(players, deck, small_blind, big_blind)
        self.gui = gui_handler
        self.pending_action = None
        self.raise_amount = 0
        self.pending_exchange_indices = None
        self._exchange_players = []
        self._exchange_index = 0

    def play_round(self):
        self._reset_round()
        self._post_blinds()
        self.deck.shuffle()
        self.deck.deal(self.players, 5)

        self.betting_round()

        self.gui.disable_betting_controls()

        active_players = [p for p in self.players if not p.folded]
        if len(active_players) > 1:
            self.current_stage = "exchange"
            self._handle_card_exchange(active_players)
        else:
            self._resume_after_exchange()

    def prompt_bet(self, player, current_bet):
        if player.is_human():
            self.gui.request_player_action(player, current_bet)
            while self.pending_action is None:
                self.gui.process_events()
            action = self.pending_action
            self.pending_action = None
            return action
        else:
            return super().prompt_bet(player, current_bet)

    def _get_raise_amount(self, current_bet):
        if self.current_player and self.current_player.is_human():
            while self.raise_amount == 0:
                self.gui.process_events()

            amt = self.raise_amount
            self.raise_amount = 0
            return amt
        else:
            # For bots, simulate a raise with a reasonable amount
            return random.randint(self.big_blind, self.big_blind * 3)

    def _handle_card_exchange(self, players):
        self._exchange_players = players
        self._exchange_index = 0
        self._wait_for_exchange()

    def _wait_for_exchange(self):
        if self._exchange_index >= len(self._exchange_players):
            self._resume_after_exchange()
            return

        player = self._exchange_players[self._exchange_index]
        if player.is_human():
            self.gui.request_card_exchange(player)
            self.pending_exchange_indices = None  # Reset to None before waiting
            while self.pending_exchange_indices is None:  # Wait until set to a list (even empty)
                self.gui.process_events()

            # Allow empty list (no cards to exchange)
            new_hand = self.exchange_cards(player.get_hand(), self.pending_exchange_indices)
            player.set_hand(new_hand)
            self.gui.show_cards(player)

            self._exchange_index += 1
            self._wait_for_exchange()
        else:
            hand_ranks = [card.rank for card in player.get_player_hand()]
            numeric_ranks = ranks_to_int(hand_ranks)
            ex_cards = [i for i, rank in enumerate(numeric_ranks) if rank < 8]
            indices = random.sample(ex_cards, min(len(ex_cards), random.randint(0, 2)))
            exchanged = self.exchange_cards(player.get_hand(), indices)
            player.set_hand(exchanged)
            self._exchange_index += 1
            self._wait_for_exchange()

    def _resume_after_exchange(self):
        self.current_stage = "showdown"
        active_players = [p for p in self.players if not p.folded]

        if not active_players:
            raise Exception("Brak aktywnych graczy w showdown")

        # Build showdown result string
        rankings = []
        result_lines = []
        for player in active_players:
            hand = player.get_player_hand()
            rank_value, tiebreakers = evaluate_hand(hand)
            hand_name = hand_rank_names[rank_value]
            card_strs = [str(card) for card in hand]
            result_lines.append(f"{player.get_name():<10} | {hand_name:<15} | {' '.join(card_strs)}")
            rankings.append((rank_value, tiebreakers, player))

        rankings.sort(reverse=True, key=lambda x: (x[0], x[1]))
        winner = rankings[0][2]
        pot_amount = self.pot

        winner.set_stack_amount(winner.get_stack_amount() + pot_amount)
        self.pot = 0

        result_lines.append(f"\n🏆 Zwycięzca: {winner.get_name()} otrzymuje {pot_amount} żetonów!")
        self.gui.show_showdown_results("\n".join(result_lines))

        session = {
            "game_id": None,
            "players": self.players,
            "deck": self.deck,
            "stage": self.current_stage,
            "bets": self.bets,
            "pot": pot_amount,
            "current_player": None,
            "completed_round": True
        }
        self.session_manager.save_session(session)
        self.bets.clear()

    def set_exchange_indices(self, indices):
        self.pending_exchange_indices = indices

    def set_player_action(self, action):
        self.pending_action = action

    def set_raise_amount(self, amount):
        self.raise_amount = amount
