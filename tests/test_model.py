from collections import Counter

from skyjoliance.model import generate_deck


def test_deck():
    deck = generate_deck()

    assert len(deck) == 150
    # Count occurrences of each card value
    value_counts = Counter(card.value for card in deck)

    assert value_counts[-2] == 5
    assert value_counts[-1] == 10
    assert value_counts[0] == 15
    for i in range(1, 13):
        assert value_counts[i] == 10


if __name__ == "__main__":
    test_deck()
