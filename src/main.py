from src.deck import Deck
from src.player import Player
from src.game_engine import GameEngine
from src.fileops.session_manager import SessionManager


def main():
    session_manager = SessionManager()

    deck = Deck()
    players = [
        Player(1000, "Gracz 1", True),
        Player(1000, "Gracz pryncypał", False),
    ]

    game = GameEngine(players, deck, 25, 50)

    round_count = 1

    while True:
        print(f"\n--- Runda {round_count} ---")
        game.play_round()

        active_players = [p for p in players if p.get_stack_amount() > 0]
        if len(active_players) <= 1:
            print(f"\nKoniec rundy! {active_players[0].get_name()} jest zwycięzcą!")
            break

        players_to_remove = []
        for player in active_players:
            if player.is_human():
                play_next_round = input(f"{player.get_name()}, Czy grasz dalej? (y/n): ").lower()
                if play_next_round != 'y':
                    print(f"{player.get_name()} zakończył grę z {player.get_stack_amount()}.")
                    players_to_remove.append(player)

        for player in players_to_remove:
            players.remove(player)

        if len(players) < 2:
            print("\nNie wystarczająca ilość graczy, gra się zakończyła.")
            break

        round_count += 1

    print("\n--- Wynik końcowy ---")
    for player in players:
        print(f"{player.get_name()} has {player.get_stack_amount()} chips.")


if __name__ == "__main__":
    main()
