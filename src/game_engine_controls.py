from src.game_engine import GameEngine
from src.utils import ranks_to_int, evaluate_hand, hand_rank_names
import random


class GuiGameEngine(GameEngine):
    def __init__(self, players, deck, small_blind, big_blind, gui_handler):
        super().__init__(players, deck, small_blind, big_blind)
        self.gui = gui_handler
        self.waiting_for_action = False
        self.waiting_for_raise = False
        self.waiting_for_exchange = False
        self.player_action = None
        self.raise_amount = 0
        self.exchange_indices = None

    def play_round(self):
        try:
            self._reset_round()
            self._post_blinds()

            self.gui.update_all_displays()
            self.gui.add_message(f"Blinds posted: Small ${self.small_blind}, Big ${self.big_blind}")

            self.deck.shuffle()
            self.deck.deal(self.players, 5)

            human_player = next((p for p in self.players if p.is_human()), None)
            if human_player:
                self.gui.show_cards(human_player)
                self.gui.add_message("Cards dealt. Starting betting round...")

            self.current_stage = "betting"
            self.betting_round()

            active_players = [p for p in self.players if not p.folded]
            if len(active_players) > 1:
                self.current_stage = "exchange"
                self.gui.add_message("--- Card Exchange Phase ---")
                self._handle_card_exchange(active_players)

            active_players = [p for p in self.players if not p.folded]
            if len(active_players) > 1:
                self.current_stage = "showdown"
                self._handle_showdown()
            else:
                winner = active_players[0] if active_players else self.players[0]
                self._award_pot_to_winner(winner)

        except Exception as e:
            self.gui.add_message(f"Game error: {str(e)}")
            self.gui.show_game_over()

    def betting_round(self):
        active = [p for p in self.players if not p.folded]
        if len(active) < 2:
            return

        for p in self.players:
            p.last_action = None
            p.current_bet = 0

        self.current_bet = self.big_blind

        max_rounds = 10
        round_count = 0

        while round_count < max_rounds:
            round_count += 1
            active = [p for p in self.players if not p.folded]

            if len(active) < 2:
                return

            betting_complete = True
            players_acted = 0

            for player in active:
                if player.folded:
                    continue

                self.current_player = player

                to_call = max(0, self.current_bet - player.current_bet)

                self.gui.update_all_displays()

                try:
                    if player.get_stack_amount() <= 0:
                        continue

                    action = self.prompt_bet(player, to_call)
                    players_acted += 1

                    if action == 'fold':
                        player.folded = True
                        player.last_action = 'fold'
                        self.gui.add_message(f"{player.get_name()} folds")

                    elif action == 'call':
                        if to_call > 0:
                            available = min(to_call, player.get_stack_amount())
                            if available > 0:
                                self.pot += player.pay(available)
                                player.current_bet += available
                                self.gui.add_message(f"{player.get_name()} calls ${available}")
                            player.last_action = 'call'
                        else:
                            player.last_action = 'check'
                            self.gui.add_message(f"{player.get_name()} checks")

                    elif action == 'check':
                        if to_call > 0:
                            player.folded = True
                            player.last_action = 'fold'
                            self.gui.add_message(f"{player.get_name()} tried to check but must call - folds instead")
                        else:
                            player.last_action = 'check'
                            self.gui.add_message(f"{player.get_name()} checks")

                    elif action == 'raise':
                        raise_amt = self._get_raise_amount(to_call)
                        total_needed = to_call + raise_amt

                        available = min(total_needed, player.get_stack_amount())
                        if available > 0:
                            self.pot += player.pay(available)
                            player.current_bet += available

                            if available >= total_needed:
                                self.current_bet = player.current_bet
                                betting_complete = False
                                self.gui.add_message(f"{player.get_name()} raises to ${player.current_bet}")
                            else:
                                self.gui.add_message(f"{player.get_name()} goes all-in with ${available}")

                            player.last_action = 'raise'
                        else:
                            player.folded = True
                            player.last_action = 'fold'
                            self.gui.add_message(f"{player.get_name()} cannot raise - folds")

                    self.gui.update_all_displays()

                    remaining = [p for p in self.players if not p.folded]
                    if len(remaining) <= 1:
                        return

                except Exception as e:
                    self.gui.add_message(f"Error processing {player.get_name()}'s action: {str(e)}")
                    player.folded = True
                    player.last_action = 'fold'

            active = [p for p in self.players if not p.folded]
            if len(active) <= 1:
                return

            if betting_complete and players_acted > 0:
                max_bet = max(p.current_bet for p in active)
                all_matched = all(p.current_bet == max_bet or p.get_stack_amount() == 0 for p in active)

                if all_matched:
                    break

        self.gui.add_message("Betting round complete")

    def prompt_bet(self, player, current_bet):
        if player.is_human():
            if player.get_stack_amount() <= 0:
                return 'check' if current_bet == 0 else 'fold'

            self.waiting_for_action = True
            self.player_action = None

            self.gui.request_player_action(player, current_bet)

            while self.waiting_for_action and self.player_action is None:
                self.gui.process_events()

            action = self.player_action
            self.waiting_for_action = False
            self.player_action = None

            return action
        else:
            return self._bot_decide_action(player, current_bet)

    def _get_raise_amount(self, current_bet):
        if self.current_player and self.current_player.is_human():
            self.waiting_for_raise = True
            self.raise_amount = 0

            self.gui.request_raise_amount(current_bet)

            while self.waiting_for_raise and self.raise_amount == 0:
                self.gui.process_events()

            amount = self.raise_amount
            self.waiting_for_raise = False
            self.raise_amount = 0

            return amount
        else:
            min_raise = max(self.big_blind, self.big_blind)
            max_raise = min(self.current_player.get_stack_amount() - current_bet, self.big_blind * 4)
            if max_raise >= min_raise:
                return random.randint(min_raise, max(min_raise, max_raise))
            return min_raise

    def _handle_card_exchange(self, players):
        for player in players:
            if player.is_human():
                self.waiting_for_exchange = True
                self.exchange_indices = None

                self.gui.request_card_exchange(player)

                while self.waiting_for_exchange and self.exchange_indices is None:
                    self.gui.process_events()

                if self.exchange_indices is not None:
                    if len(self.exchange_indices) > 0:
                        new_hand = self.exchange_cards(player.get_hand(), self.exchange_indices)
                        player.set_hand(new_hand)
                        self.gui.add_message(f"You exchanged {len(self.exchange_indices)} cards")

                        self.gui.show_cards(player)
                    else:
                        self.gui.add_message("You kept all your cards")

                self.waiting_for_exchange = False
                self.exchange_indices = None

            else:
                hand = player.get_hand()
                hand_ranks = [card.rank for card in hand]
                numeric_ranks = ranks_to_int(hand_ranks)

                rank_counts = {}
                for rank in numeric_ranks:
                    rank_counts[rank] = rank_counts.get(rank, 0) + 1

                cards_to_keep = []
                for i, rank in enumerate(numeric_ranks):
                    if rank_counts[rank] >= 2 or rank >= 9:
                        cards_to_keep.append(i)

                all_indices = set(range(5))
                keep_indices = set(cards_to_keep)
                exchange_indices = list(all_indices - keep_indices)

                if len(exchange_indices) > 3:
                    exchange_indices = exchange_indices[:3]

                if exchange_indices:
                    new_hand = self.exchange_cards(player.get_hand(), exchange_indices)
                    player.set_hand(new_hand)
                    self.gui.add_message(f"{player.get_name()} exchanged {len(exchange_indices)} cards")
                else:
                    self.gui.add_message(f"{player.get_name()} kept all cards")

    def _handle_showdown(self):
        active_players = [p for p in self.players if not p.folded]

        if not active_players:
            self.gui.add_message("No active players for showdown")
            return

        if len(active_players) == 1:
            winner = active_players[0]
            self._award_pot_to_winner(winner)
            return

        self.gui.add_message("--- SHOWDOWN ---")

        rankings = []
        result_lines = []

        for player in active_players:
            hand = player.get_player_hand()
            rank_value, tiebreakers = evaluate_hand(hand)
            hand_name = hand_rank_names[rank_value]
            card_strs = [str(card) for card in hand]

            result_lines.append(f"{player.get_name():<12} | {hand_name:<15} | {' '.join(card_strs)}")
            rankings.append((rank_value, tiebreakers, player))

        rankings.sort(reverse=True, key=lambda x: (x[0], x[1]))
        winner = rankings[0][2]

        pot_amount = self.pot
        self._award_pot_to_winner(winner)

        result_lines.append(f"\n🏆 Winner: {winner.get_name()} wins ${pot_amount}!")
        self.gui.show_showdown_results("\n".join(result_lines))

    def _award_pot_to_winner(self, winner):
        pot_amount = self.pot
        winner.set_stack_amount(winner.get_stack_amount() + pot_amount)
        self.gui.enable_new_round()

        for player in self.players:
            player.current_bet = 0
            player.folded = False

        self.pot = 0
        self.current_bet = 0

        self.gui.update_all_displays()

    def set_player_action(self, action):
        self.player_action = action
        self.waiting_for_action = False

    def set_raise_amount(self, amount):
        self.raise_amount = amount
        self.waiting_for_raise = False

    def set_exchange_indices(self, indices):
        self.exchange_indices = indices if indices is not None else []
        self.waiting_for_exchange = False

    def _bot_decide_action(self, player, current_bet):

        available_chips = player.get_stack_amount()

        if available_chips <= 0:
            return 'check' if current_bet == 0 else 'fold'

        if current_bet > available_chips:
            return 'fold'

        hand = player.get_hand()
        if hand:
            hand_ranks = [card.rank for card in hand]
            numeric_ranks = ranks_to_int(hand_ranks)

            rank_counts = {}
            for rank in numeric_ranks:
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            has_pair = any(count >= 2 for count in rank_counts.values())
            high_cards = sum(1 for rank in numeric_ranks if rank >= 10)

            if current_bet == 0:
                if has_pair or high_cards >= 3:
                    if random.random() < 0.25 and available_chips >= self.big_blind:
                        return 'raise'
                    else:
                        return 'check'
                else:
                    return 'check'
            else:
                if available_chips < current_bet:
                    return 'fold'

                if has_pair or high_cards >= 3:
                    if random.random() < 0.7:
                        return 'call'
                    elif available_chips >= current_bet + self.big_blind:
                        return 'raise'
                    else:
                        return 'call'
                elif high_cards >= 2:
                    if random.random() < 0.5:
                        return 'call'
                    else:
                        return 'fold'
                else:
                    if random.random() < 0.2:
                        return 'call'
                    else:
                        return 'fold'
        else:
            if current_bet == 0:
                return 'check'
            elif random.random() < 0.3:
                return 'call'
            else:
                return 'fold'

    def _reset_round(self):
        super()._reset_round()

        for player in self.players:
            player.current_bet = 0
            player.folded = False
            player.last_action = None

        self.pot = 0
        self.current_bet = 0
        self.current_stage = "pre-flop"