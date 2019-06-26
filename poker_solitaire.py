#!/usr/bin/env python2

from deuces import Card, Deck, Evaluator
import numpy as np
from numpy.random import shuffle

evaluator = Evaluator()

def possibility_of_getting_burnt(board, chosen_value, deck,
                                 left_to_deal, nsamples=100):
    # the only way that keeping the hand with a <50% chance of winning
    # is the correct move is if there is at least some possibility that
    # there will be *two* hands that beat you, and moreover they come in
    # the wrong order

    if left_to_deal <= 1:
        # you IDIOT, of course keep your hand
        return 0

    nburns = 0
    cards = deck.cards
    copied_deck = Deck()
    for _ in xrange(nsamples):
        shuffle(cards)
        copied_deck.cards = list(cards)
        got_beat = False
        value_to_beat = -1
        for x in range(left_to_deal):
            hand = copied_deck.draw(2)
            value = evaluator.evaluate(board, hand)
            if got_beat and value < value_to_beat:
                nburns += 1
                break
            if value < chosen_value:
                got_beat = True
                value_to_beat = value
    return nburns * 1.0 / nsamples

def chance_to_win_given_choice(board, chosen_value, deck,
                               left_to_deal, nsamples=100,
                               return_burns=False):
    if left_to_deal == 0:
        if return_burns:
            return (1., 0.)
        return 1.
    nwins = 0
    nburns = 0
    cards = deck.cards
    copied_deck = Deck()
    for _ in xrange(nsamples):
        shuffle(cards)
        copied_deck.cards = list(cards)
        won = True
        burnt = False

        value_to_beat = - 1
        for x in range(left_to_deal):
            hand = copied_deck.draw(2)
            value = evaluator.evaluate(board, hand)
            if not won and value < value_to_beat:
                burnt = True
                break
            if value < chosen_value:
                won = False
                value_to_beat = value
        if won:
            nwins += 1
        if burnt:
            nburns += 1

    if return_burns:
        return (nwins * 1.0 / nsamples, nburns * 1.0 / nsamples)
    return nwins * 1.0 / nsamples

def sample_win_probability_dumb(board, value_to_beat, deck,
                                left_to_deal, nsamples=100):
    nwins = 0
    cards = deck.cards
    copied_deck = Deck()
    for _ in xrange(nsamples):
        shuffle(cards)
        copied_deck.cards = list(cards)
        won = False
        decided = False
        best_value = value_to_beat
        chosen_value = 10**10
        for x in range(left_to_deal):
            hand = copied_deck.draw(2)
            value = evaluator.evaluate(board, hand)
            if value < value_to_beat and not decided:
                # have to decide whether to stay!
                win_prob = chance_to_win_given_choice(board, value,
                                                      deck, left_to_deal-x-1)
                if win_prob > 0.5:
                    chosen_value = value
                    decided = True
            best_value = min(best_value, value)

        if chosen_value < best_value:
            nwins += 1

    return nwins * 1.0 / nsamples

def sample_win_probability(board, value_to_beat, deck,
                                left_to_deal, nsamples = 50):
    pwin = 0.
    cards = deck.cards
    copied_deck = Deck()
    for _ in xrange(nsamples):
        shuffle(cards)
        copied_deck.cards = list(cards)
        new_hand = copied_deck.draw(2)
        value = evaluator.evaluate(board, new_hand)
        if value > value_to_beat:
            # the new hand is worse, so no decision to be made
            if left_to_deal > 1:
                # just burn the cards and keep going
                pwin += sample_win_probability(board, value_to_beat,
                                              copied_deck, left_to_deal-1)
            elif left_to_deal == 1:
                # this was our last chance, we lost
                pwin += 0
        else:
            if left_to_deal == 1:
                # this was our last hand.  We won!
                pwin += 1
            else:
                # we have a choice.  What do we do??
                prob_if_stayed,prob_burn = chance_to_win_given_choice(board, value,
                                                            copied_deck, left_to_deal-1,
                                                                      return_burns=True)
                # we have the inequality
                #       P(there is a better hand) - P(you get "burnt")
                #           < P(win if you pass) < P(there is a better hand)
                # also,
                #  P(there is a better hand) = 1 - P(win if you stay)
                # If P(win if you pass) < P(win if you stay) then you should stay
                # and if P(win if you pass) > P(win if you stay) then you should continue
                if prob_if_stayed > 0.5:
                    # definitely should stay
                    pwin += prob_if_stayed
                    continue
                if prob_burn <= 0.1:
                    # if burns are pretty rare, then let's just say that
                    # the win probability is well approximated by the
                    # "dumb" strategy.
                    prob_if_passed = sample_win_probability_dumb(board, value,
                                                                 copied_deck, left_to_deal-1)
                else:
                    prob_if_passed = sample_win_probability(board, value,
                                                        copied_deck, left_to_deal-1)
                pwin += max(prob_if_stayed, prob_if_passed)

    return pwin * 1. / nsamples

def make_decision(board, value, deck, left_to_deal, nsamples=100):
    prob_if_stayed, prob_burn = chance_to_win_given_choice(board, value,
                                                deck, left_to_deal-1,
                                                           return_burns=True)
    if prob_if_stayed >= 0.5:
        return (True, prob_if_stayed)
    elif prob_if_stayed <= 1 - prob_if_stayed - prob_burn:
        return (False, 1-prob_if_stayed)
    print "Wow this is quite the hand!!"
    print "The probability that this hand wins is ", prob_if_stayed
    print "And the chance of getting 'burned' is ", prob_burn
    #else:
    #    # THIS IS NOT THE OPTIMAL STRATEGY!!
    #    return (False, 1-prob_if_stayed)
    #if prob_if_stayed < 0.2:
    #    return (False, 1-prob_if_stayed)
    prob_if_passed = sample_win_probability(board, value,
                                            deck, left_to_deal-1)
    return (prob_if_stayed > prob_if_passed, max(prob_if_passed,prob_if_stayed))

def main():
    depth = 3
    deck = Deck()
    board = deck.draw(5)
    print sample_win_probability(board, 10**10, deck, depth, nsamples=100)

def play():
    nhands = 8
    nwon = 0
    nplayed = 0
    computer_won = 0
    while True:
        deck = Deck()
        board = deck.draw(5)
        all_hands = []
        best_value = 10**10
        hand_index = -1
        comp_index = -1
        for hand_num in range(nhands):
            all_hands.append(deck.draw(2))
            hand_value = evaluator.evaluate(board,all_hands[-1])
            if hand_index == -1:
                print "===== The board: ====="
                Card.print_pretty_cards(board)
                print "===== The hands: ====="
                for hand in all_hands:
                    Card.print_pretty_cards(hand)
            if hand_value < best_value:
                best_value = hand_value
                if comp_index == -1:
                    choice = make_decision(board, best_value,
                                           deck, nhands - hand_num -1)
                    if choice[0]:
                        print "Computer chose to keep this hand, estimating a win probability of ", choice[1]
                        comp_index = hand_num
                        comp_value = hand_value
                    else:
                        print "Computer thinks it has a win probability of",\
                            choice[1], "by continuing"
            if hand_num < nhands - 1 and hand_index == -1:
                stop = raw_input("Would you like to stop (y if so)?")
                if stop[0] == 'y' or stop[0] == 'Y':
                    hand_index = hand_num
            elif hand_num == nhands - 1:
                if hand_index == -1:
                    print "You have chosen the last hand"
                    hand_index = hand_num
                if comp_index == -1:
                    comp_index = hand_num
                    comp_value = hand_value

        for _ in range(nhands - hand_num - 1):
            all_hands.append(deck.draw(2))

        print "===== The board: ====="
        Card.print_pretty_cards(board)
        print "===== The hands: ====="
        best_index = -1
        chosen_value = -1
        print "You chose hand number ", hand_index
        print "The computer chose hand number ", comp_index
        for idx,hand in enumerate(all_hands):
            Card.print_pretty_cards(hand)
            score = evaluator.evaluate(board, hand)
            if score <= best_value:
                best_index = idx
                best_value = score
            if idx == hand_index:
                chosen_value = score
        score = evaluator.evaluate(board,all_hands[best_index])
        hand_class = evaluator.get_rank_class(score)
        print "The winning hand was", best_index, "(",evaluator.class_to_string(hand_class),")"

        if  chosen_value<= best_value:
            print "Your hand won!!"
            nwon += 1
        else:
            print "Your hand lost to hand number ", best_index

        if comp_value <= best_value:
            print "The computer won!"
            computer_won += 1
        else:
            print "The computer lost."

        nplayed += 1
        if nplayed % 100 == 0:
            print computer_won, nplayed
        again = raw_input("Play again?")
        if again[0] != 'y' and again[0] != 'Y':
            break

    print "You played ", nplayed ," games and won ", nwon, " times"
    print "The computer won ", computer_won, " of the same games"


if __name__=="__main__":
    play()
    #main()
