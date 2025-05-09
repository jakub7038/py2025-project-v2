from typing import List, Tuple
from card import Card

def ranks_to_int(ranks_list):
    rank_map = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    return [rank_map[rank] for rank in ranks_list]


def evaluate_hand(hand: List[Card]) -> Tuple[int, List[int]]:
    raw_ranks = [c.rank for c in hand]
    ranks = sorted(ranks_to_int(raw_ranks), reverse=True)
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