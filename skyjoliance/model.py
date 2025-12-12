from dataclasses import dataclass, field
from enum import StrEnum
from random import shuffle
from typing import Literal


class CardState(StrEnum):
    FACE_UP = "face_up"
    FACE_DOWN = "face_down"


@dataclass
class Card:
    value: Literal[-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    state: CardState = CardState.FACE_DOWN

    def flip(self, new_state: CardState = None):
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


def generate_deck(seed=0) -> list[Card]:
    deck = [-2] * 5 + [-1] * 10 + [0] * 15
    for i in range(1, 13):
        deck += [i] * 10
    deck = [Card(value=v) for v in deck]

    shuffle(deck)

    return deck


type GridOfCards = list[list[Card]]


class PlayerDrawAction(StrEnum):
    DRAW_FROM_DECK = "draw_from_deck"
    DRAW_FROM_DISCARD = "draw_from_discard"

class PlayerPlayAction(StrEnum):
    DISCARD_DRAWN_CARD = "discard_drawn_card"
    REPLACE_CARD_IN_GRID = "replace_card_in_grid"
    


@dataclass
class PlayerStrategy:
    name: str
    
    def decide_draw(self, round_state: "Round", player: "Player") -> PlayerDrawAction:
        ...
    
    def decide_play(self, round_state: "Round", player: "Player") -> PlayerPlayAction:
        ...
        

@dataclass
class Player:
    name: str
    strategy: PlayerStrategy
    cards: GridOfCards = None

    def set_grid_of_cards(self, card: list[Card]):
        if self.cards is not None:
            raise ValueError("Player already has a grid of cards assigned.")

        grid = [card[i : i + 4] for i in range(0, len(card), 4)]
        self.cards = grid
        
    def play_card(self, round_state: "Round") -> Card:
        # Placeholder for player strategy to play a card
        for row in self.cards:
            for card in row:
                if card.state == CardState.FACE_DOWN:
                    card.flip()
                    return card
        raise ValueError("No face-down cards left to play.")


@dataclass
class Round:
    players: list[Player]
    current_player_index: int = 0
    cards_deck: list[Card] = field(default_factory=generate_deck)
    discard_pile: list[Card] = field(default_factory=list)

    def __post_init__(self):
        for player in self.players:
            player.cards = []
        self._distribute_cards()

        card = self.cards_deck.pop()
        card.flip(CardState.FACE_UP)
        self.discard_pile.append(card)

    def _distribute_cards(self):
        if any(player.cards for player in self.players):
            raise ValueError("Cards have already been distributed to players.")

        cards_per_player = 12

        hands = [[] for _ in self.players]
        for _ in range(cards_per_player):
            for player_hand in hands:
                card = self.cards_deck.pop()
                player_hand.append(card)

        for player, hand in zip(self.players, hands):
            player.set_grid_of_cards(hand)
            
    def make_player_play()
