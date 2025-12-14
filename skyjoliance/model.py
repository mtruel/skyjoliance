from dataclasses import dataclass, field
from enum import StrEnum
from random import Random
from typing import Literal, Protocol, runtime_checkable


class CardPositionError(Exception):
    pass


class CardStateError(Exception):
    pass


class ImpossibleGameStateError(Exception):
    pass


class CardState(StrEnum):
    FACE_UP = "face_up"
    FACE_DOWN = "face_down"


class RoundState(StrEnum):
    AWAITING_DISTRIBUTION = "awaiting_distribution"
    AWAITING_TWO_CARDS_REVEAL = "awaiting_two_cards_reveal"
    ONGOING = "ongoing"
    LAST_TURN = "last_turn"
    ENDED = "ended"


ValidCardValue = Literal[-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


@dataclass
class Card:
    value: ValidCardValue
    state: CardState = CardState.FACE_DOWN

    def copy(self) -> "Card":
        return Card(self.value, self.state)

    def flip(self, new_state: CardState | None = None):
        if new_state is None:
            if self.state == CardState.FACE_DOWN:
                self.state = CardState.FACE_UP
            else:
                self.state = CardState.FACE_DOWN
        else:
            self.state = new_state

    def __repr__(self):
        if self.state == CardState.FACE_UP:
            is_visible = "up"
        else:
            is_visible = "down"

        return f"Card({self.value}, {is_visible})"


def generate_deck(seed: int = 0) -> list[Card]:
    deck = [-2] * 5 + [-1] * 10 + [0] * 15
    for i in range(1, 13):
        deck += [i] * 10
    deck = [Card(value=v) for v in deck]

    rng = Random(seed)
    rng.shuffle(deck)

    return deck


class GridOfCards:
    """A grid of cards for a player.

    Card are stored in a flat list, but accessed as a 2D grid. The grid is Column-major."""

    def __init__(self, rows: int, cols: int):
        self._cards: list[Card | None] = [None] * (rows * cols)
        self._rows = rows
        self._cols = cols

    def copy(self) -> "GridOfCards":
        new_grid = GridOfCards(self._rows, self._cols)
        new_grid._cards = [
            card.copy() if card is not None else None for card in self._cards
        ]
        return new_grid

    def _get_index(self, row: int, col: int) -> int:
        if row < 0 or row >= self._rows:
            raise IndexError(f"Row index {row} out of range (0-{self._rows - 1})")
        if col < 0 or col >= self._cols:
            raise IndexError(f"Column index {col} out of range (0-{self._cols - 1})")
        return row * self._cols + col

    def reveal_card(self, row: int, col: int):
        index = self._get_index(row, col)
        card = self._cards[index]
        if card is None:
            raise CardPositionError(f"No card at position ({row}, {col})")
        if card.state == CardState.FACE_UP:
            raise CardStateError(f"Card at position ({row}, {col}) is already face up")

        card.flip(CardState.FACE_UP)

    def pick_card(self, row: int, col: int) -> Card:
        index = self._get_index(row, col)
        card = self._cards[index]
        if card is None:
            raise CardPositionError(f"No card at position ({row}, {col})")

        self._cards[index] = None
        return card

    def place_card(self, row: int, col: int, card: Card):
        index = self._get_index(row, col)
        if self._cards[index] is not None:
            raise CardPositionError(f"Position ({row}, {col}) is already occupied")

        self._cards[index] = card

    def replace_card(self, position: tuple[int, int], card: Card):
        row, col = position

        old_card = self.pick_card(row, col)
        self.place_card(row, col, card)
        return old_card

    def pick_column(self, col: int) -> tuple[Card, Card, Card]:
        if self._rows != 3:
            raise ValueError("pick_column is only supported for 3-row grids")

        cards: list[Card] = []
        for row in range(3):
            card = self.pick_card(row, col)
            cards.append(card)
        return tuple(cards)

    def identify_any_complete_column(self) -> int | None:
        cols_to_discard: list[int] = []
        for col in range(self._cols):
            column = [
                self._cards[self._get_index(row, col)] for row in range(self._rows)
            ]
            if any(card is None for card in column):
                continue

            is_to_discard = all(
                card.state == CardState.FACE_UP for card in column if card is not None
            )
            if is_to_discard:
                cols_to_discard.append(col)
        if len(cols_to_discard) == 0:
            return None
        elif len(cols_to_discard) == 1:
            return cols_to_discard[0]
        else:
            raise ImpossibleGameStateError("Multiple complete revealed columns found")

    def all_cards_revealed(self) -> bool:
        return all(
            card is None or card.state == CardState.FACE_UP for card in self._cards
        )


class DrawDecision(StrEnum):
    DRAW_FROM_DECK = "draw_from_deck"
    DRAW_FROM_DISCARD = "draw_from_discard"


class PlayDecision(StrEnum):
    DISCARD_DRAWN_CARD_AND_REVEAL = "discard_drawn_card_and_reveal"
    REPLACE_CARD_IN_GRID = "replace_card_in_grid"


@dataclass
class PlayerPlayAction:
    action: PlayDecision
    target_position: tuple[int, int]


@runtime_checkable
class PlayerStrategy(Protocol):
    name: str = "StrategyProtocol"

    def decide_draw(
        self,
        round_state: "Round",
        current_player_id: int,
    ) -> DrawDecision: ...

    def decide_play(
        self,
        drawn_card: Card,
        round_state: "Round",
        current_player_id: int,
    ) -> PlayerPlayAction: ...

    def decide_reveal_two_cards(
        self, player: "Player"
    ) -> tuple[tuple[int, int], tuple[int, int]]: ...


class RandomSkyjoStrategy:
    name: str = "RandomSkyjoStrategy"

    def decide_draw(
        self,
        round_state: "Round",
        current_player_id: int,
    ) -> DrawDecision:
        from random import choice

        return choice(list(DrawDecision))

    def decide_play(
        self,
        drawn_card: Card,
        round_state: "Round",
        current_player_id: int,
    ) -> PlayerPlayAction:
        from random import choice

        current_player = round_state.players[current_player_id]
        if current_player._cards is None:
            raise ImpossibleGameStateError("Player has no card configuration.")

        action = choice(list(PlayDecision))

        if action == PlayDecision.DISCARD_DRAWN_CARD_AND_REVEAL:
            # For reveal action, only choose face-down cards
            possible_positions = [
                (row, col)
                for row in range(current_player._cards._rows)
                for col in range(current_player._cards._cols)
                if (
                    card := current_player._cards._cards[
                        current_player._cards._get_index(row, col)
                    ]
                )
                and card.state == CardState.FACE_DOWN
            ]
        else:
            # For replace action, only choose positions with cards
            possible_positions = [
                (row, col)
                for row in range(current_player._cards._rows)
                for col in range(current_player._cards._cols)
                if current_player._cards._cards[
                    current_player._cards._get_index(row, col)
                ]
                is not None
            ]

        target_position = choice(possible_positions)

        return PlayerPlayAction(action=action, target_position=target_position)

    def decide_reveal_two_cards(
        self, player: "Player"
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        from random import sample

        if player._cards is None:
            raise ImpossibleGameStateError("Player has no card configuration.")

        possible_positions = [
            (row, col)
            for row in range(player._cards._rows)
            for col in range(player._cards._cols)
            if player._cards._cards[player._cards._get_index(row, col)].state
            == CardState.FACE_DOWN
        ]

        positions_to_reveal = sample(possible_positions, 2)
        return (positions_to_reveal[0], positions_to_reveal[1])


class Player:
    def __init__(self, name: str, strategy: PlayerStrategy):
        self._name = name
        self.strategy = strategy
        self._cards: GridOfCards | None = None

    def copy(self) -> "Player":
        new_player = Player(self._name, self.strategy)
        if self._cards is not None:
            new_player._cards = self._cards.copy()
        return new_player

    def place_distributed_cards(
        self, cards: list[Card], configuration: tuple[int, int]
    ):
        rows, cols = configuration
        if len(cards) != rows * cols:
            raise ImpossibleGameStateError("Number of cards does not match grid size")

        self._cards = GridOfCards(rows, cols)

        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols
            self._cards.place_card(row, col, card)

    def all_cards_revealed(self) -> bool:
        if self._cards is None:
            raise ImpossibleGameStateError("Player has no card configuration.")

        return self._cards.all_cards_revealed()

    def play_card(
        self,
        drawn_card: Card,
        play_action: PlayerPlayAction,
    ) -> tuple[Card] | tuple[Card, Card, Card, Card]:
        if self._cards is None:
            raise ImpossibleGameStateError("Player has no card configuration.")

        discarded_card: Card
        also_discard_column: tuple[Card, Card, Card] | None = None

        if play_action.action == PlayDecision.DISCARD_DRAWN_CARD_AND_REVEAL:
            discarded_card = drawn_card
            row, col = play_action.target_position
            self._cards.reveal_card(row, col)
        elif play_action.action == PlayDecision.REPLACE_CARD_IN_GRID:
            row, col = play_action.target_position
            discarded_card = self._cards.replace_card((row, col), drawn_card)
        else:
            raise ValueError(f"Unknown play action: {play_action.action}")

        complete_column = self._cards.identify_any_complete_column()
        if complete_column is not None:
            also_discard_column = self._cards.pick_column(complete_column)

        all_discarded_cards = (
            (discarded_card,)
            if also_discard_column is None
            else (discarded_card, *also_discard_column)
        )
        return all_discarded_cards


@dataclass
class Round:
    players: list[Player]
    current_player_index: int = 0
    cards_deck: list[Card] = field(default_factory=generate_deck)
    discard_pile: list[Card] = field(default_factory=list)
    state: RoundState = RoundState.AWAITING_DISTRIBUTION
    starting_player_index: int | None = None
    player_who_triggered_last_turn: int | None = None

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def copy(self) -> "Round":
        return Round(
            players=[player.copy() for player in self.players],
            current_player_index=self.current_player_index,
            cards_deck=[card.copy() for card in self.cards_deck],
            discard_pile=[card.copy() for card in self.discard_pile],
            state=self.state,
            starting_player_index=self.starting_player_index,
            player_who_triggered_last_turn=self.player_who_triggered_last_turn,
        )

    def distribute_cards(self, configuration: tuple[int, int] = (3, 4)):
        if any(player._cards for player in self.players):
            raise ValueError("Cards have already been distributed to players.")

        if not self.state == RoundState.AWAITING_DISTRIBUTION:
            raise ImpossibleGameStateError(
                "Cannot distribute cards when round has already started."
            )

        cards_per_player = configuration[0] * configuration[1]

        hands: list[list[Card]] = [[] for _ in self.players]
        for _ in range(cards_per_player):
            for player_hand in hands:
                card = self.cards_deck.pop()
                player_hand.append(card)

        for player, hand in zip(self.players, hands):
            player.place_distributed_cards(hand, configuration)

        card = self.cards_deck.pop()
        card.flip(CardState.FACE_UP)
        self.discard_pile.append(card)

        self.state = RoundState.AWAITING_TWO_CARDS_REVEAL

    def make_player_reveal_two_cards(self):
        if not self.state == RoundState.AWAITING_TWO_CARDS_REVEAL:
            raise ImpossibleGameStateError(
                "Cannot reveal two cards when round has already started."
            )

        for player in self.players:
            positions = player.strategy.decide_reveal_two_cards(player.copy())
            for row, col in positions:
                player._cards.reveal_card(row, col)

        self.state = RoundState.ONGOING

    def make_current_player_play(self) -> RoundState:
        if not (self.state == RoundState.ONGOING or self.state == RoundState.LAST_TURN):
            raise ImpossibleGameStateError(
                f"Cannot make a play when round state is {self.state}"
            )

        current_player = self.players[self.current_player_index]

        draw_action = current_player.strategy.decide_draw(
            round_state=self.copy(),
            current_player_id=self.current_player_index,
        )

        if draw_action == DrawDecision.DRAW_FROM_DECK:
            drawn_card = self.cards_deck.pop()
        elif draw_action == DrawDecision.DRAW_FROM_DISCARD:
            drawn_card = self.discard_pile.pop()
        else:
            raise ImpossibleGameStateError(f"Unknown draw action: {draw_action}")

        play_action = current_player.strategy.decide_play(
            drawn_card,
            round_state=self.copy(),
            current_player_id=self.current_player_index,
        )
        discarded_card = current_player.play_card(drawn_card, play_action)

        self.discard_pile.extend(discarded_card)
        # Trigger last turn if all cards are revealed
        if current_player.all_cards_revealed() and self.state != RoundState.LAST_TURN:
            self.state = RoundState.LAST_TURN
            self.player_who_triggered_last_turn = self.current_player_index
        return self.state
