from enum import Enum
from typing import List, Tuple, Dict, Set
from pydantic import BaseModel, Field
import random
from collections import Counter
from itertools import combinations
import math

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class HandRank(Enum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class Card(BaseModel):
    rank: Rank
    suit: Suit
    
    def __str__(self):
        rank_str = {
            Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
            Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
            Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K", Rank.ACE: "A"
        }
        card_str = f"{rank_str[self.rank]}{self.suit.value}"
        
        # Color red suits (hearts, diamonds) red and black suits (clubs, spades) dark gray
        if self.suit in [Suit.HEARTS, Suit.DIAMONDS]:
            return f"\033[31m{card_str}\033[0m"  # Red
        else:
            return f"\033[90m{card_str}\033[0m"  # Dark gray
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))

class Hand(BaseModel):
    cards: List[Card] = Field(default_factory=list)
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def __str__(self):
        return " ".join(str(card) for card in self.cards)

class Deck(BaseModel):
    cards: List[Card] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.create_deck()
        self.shuffle()
    
    def create_deck(self):
        self.cards = [Card(rank=rank, suit=suit) for rank in Rank for suit in Suit]
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("Cannot deal from empty deck")
        return self.cards.pop()
    
    def cards_remaining(self) -> int:
        return len(self.cards)

class HandEvaluator:
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate hand")
        
        best_hand = None
        best_rank = HandRank.HIGH_CARD
        best_values = []
        
        for combo in combinations(cards, 5):
            rank, values = HandEvaluator._evaluate_five_cards(list(combo))
            if rank.value > best_rank.value or (rank == best_rank and values > best_values):
                best_hand = combo
                best_rank = rank
                best_values = values
        
        return best_rank, best_values
    
    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        ranks = [card.rank.value for card in cards]
        suits = [card.suit for card in cards]
        rank_counts = Counter(ranks)
        
        is_flush = len(set(suits)) == 1
        is_straight = HandEvaluator._is_straight(ranks)
        
        sorted_ranks = sorted(ranks, reverse=True)
        counts = sorted(rank_counts.values(), reverse=True)
        
        if is_straight and is_flush:
            if sorted_ranks == [14, 13, 12, 11, 10]:
                return HandRank.ROYAL_FLUSH, [14]
            return HandRank.STRAIGHT_FLUSH, [max(ranks)]
        
        if counts == [4, 1]:
            four_kind = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            return HandRank.FOUR_OF_A_KIND, [four_kind, kicker]
        
        if counts == [3, 2]:
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            return HandRank.FULL_HOUSE, [three_kind, pair]
        
        if is_flush:
            return HandRank.FLUSH, sorted_ranks
        
        if is_straight:
            return HandRank.STRAIGHT, [max(ranks)]
        
        if counts == [3, 1, 1]:
            three_kind = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            return HandRank.THREE_OF_A_KIND, [three_kind] + kickers
        
        if counts == [2, 2, 1]:
            pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
            kicker = [rank for rank, count in rank_counts.items() if count == 1][0]
            return HandRank.TWO_PAIR, pairs + [kicker]
        
        if counts == [2, 1, 1, 1]:
            pair = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = sorted([rank for rank, count in rank_counts.items() if count == 1], reverse=True)
            return HandRank.ONE_PAIR, [pair] + kickers
        
        return HandRank.HIGH_CARD, sorted_ranks
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        sorted_ranks = sorted(set(ranks))
        if len(sorted_ranks) != 5:
            return False
        
        if sorted_ranks == [2, 3, 4, 5, 14]:  # A-2-3-4-5 straight
            return True
        
        return sorted_ranks[-1] - sorted_ranks[0] == 4

class OddsCalculator:
    @staticmethod
    def calculate_odds(hole_cards: List[Card], community_cards: List[Card], deck: Deck, simulations: int = 10000) -> Dict[str, Tuple[float, str]]:
        known_cards = set(hole_cards + community_cards)
        remaining_cards = [card for card in deck.cards if card not in known_cards]
        
        cards_needed = 5 - len(community_cards)
        results = {hand_rank.name: 0 for hand_rank in HandRank}
        total_remaining = len(remaining_cards)
        
        for _ in range(simulations):
            sim_deck = remaining_cards.copy()
            random.shuffle(sim_deck)
            
            sim_community = community_cards + sim_deck[:cards_needed]
            all_cards = hole_cards + sim_community
            
            hand_rank, _ = HandEvaluator.evaluate_hand(all_cards)
            results[hand_rank.name] += 1
        
        # Calculate percentages and explanations
        odds_with_explanations = {}
        for hand, count in results.items():
            percentage = (count / simulations) * 100
            if cards_needed > 0:
                total_combinations = math.comb(total_remaining, cards_needed)
                explanation = f"({count}/{simulations} simulations = {percentage:.2f}%)"
            else:
                explanation = f"(final hand determined)"
            odds_with_explanations[hand] = (percentage, explanation)
        
        return odds_with_explanations

class TexasHoldemGame(BaseModel):
    deck: Deck = Field(default_factory=Deck)
    player_hand: Hand = Field(default_factory=Hand)
    community_cards: List[Card] = Field(default_factory=list)
    
    def start_game(self):
        print("🎰 Welcome to Texas Hold'em!")
        print("=" * 50)
        
        # Deal hole cards
        print("\n📋 Dealing your hole cards...")
        for _ in range(2):
            card = self.deck.deal_card()
            self.player_hand.add_card(card)
        
        print(f"Your hole cards: {self.player_hand}")
        self._display_odds()
        
        print("\n" + "="*30)
        self._deal_flop()
        
        print("\n" + "="*30)
        self._deal_turn()
        
        print("\n" + "="*30)
        self._deal_river()
        
        self._show_final_result()
    
    def _deal_flop(self):
        print("\n🃏 The Flop:")
        for _ in range(3):
            card = self.deck.deal_card()
            self.community_cards.append(card)
        
        print(f"Community cards: {' '.join(str(card) for card in self.community_cards)}")
        self._display_odds()
    
    def _deal_turn(self):
        print("\n🃏 The Turn:")
        card = self.deck.deal_card()
        self.community_cards.append(card)
        
        print(f"Community cards: {' '.join(str(card) for card in self.community_cards)}")
        self._display_odds()
    
    def _deal_river(self):
        print("\n🃏 The River:")
        card = self.deck.deal_card()
        self.community_cards.append(card)
        
        print(f"Community cards: {' '.join(str(card) for card in self.community_cards)}")
        self._display_odds()
    
    def _display_odds(self):
        odds = OddsCalculator.calculate_odds(
            self.player_hand.cards, 
            self.community_cards, 
            self.deck,
            simulations=5000
        )
        
        print("\n📊 Your odds for each hand type:")
        for hand_type, percentage in sorted(odds.items(), key=lambda x: x[1], reverse=True):
            if percentage > 0.01:  # Only show odds > 0.01%
                print(f"  {hand_type.replace('_', ' ').title()}: {percentage:.2f}%")
    
    def _show_final_result(self):
        all_cards = self.player_hand.cards + self.community_cards
        final_hand, values = HandEvaluator.evaluate_hand(all_cards)
        
        print("\n" + "=" * 50)
        print("🎯 FINAL RESULT")
        print("=" * 50)
        print(f"Your hole cards: {self.player_hand}")
        print(f"Community cards: {' '.join(str(card) for card in self.community_cards)}")
        print(f"Best hand: {final_hand.name.replace('_', ' ').title()}")
        print("=" * 50)

def main():
    game = TexasHoldemGame()
    game.start_game()


if __name__ == "__main__":
    main()
