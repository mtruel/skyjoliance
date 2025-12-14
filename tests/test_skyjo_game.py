from skyjoliance.model import Player, RandomSkyjoStrategy, Round, RoundState


def test_full_skyjo_game():
    players = [
        Player("Alice", RandomSkyjoStrategy()),  # noqa: F821
        Player("Bob", RandomSkyjoStrategy()),
        Player("Charlie", RandomSkyjoStrategy()),
    ]

    round = Round(players)
    round.distribute_cards()
    round.make_player_reveal_two_cards()

    while round.state != RoundState.LAST_TURN:
        round.make_current_player_play()
        round.next_player()


if __name__ == "__main__":
    test_full_skyjo_game()
