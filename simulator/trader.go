package simulator

import (
	"fmt"
	"math"
	"sort"
	"time"
)

type TradeRequest struct {
	Meter *Meter
	Score float64
}

type Trader struct {
	tradeChooser BestOffersFunc
}

func NewTrader() *Trader {
	tradeChooser := MkChooseBestOffersFunction("models/grid-loss-weights.csv", "models/duration-weights.csv", "models/grid-loss.json", make([]float64, 0))
	return &Trader{
		tradeChooser: tradeChooser,
	}
}

func (t *Trader) ScoreOffers(m *Meter, offers []*Meter, gridState *GridState, limit int) []ScoredOffer {
	choices := t.tradeChooser(m.Surplus, offers, gridState, limit)
	return choices
}

func (t *Trader) CollectRequests(meters map[string]*Meter, gridState *GridState) map[*Meter][]*TradeRequest {
	requests := make(map[*Meter][]*TradeRequest)

	var offers []*Meter
	for _, m := range meters {
		if m.Surplus > 0 {
			offers = append(offers, m)
			continue
		}
	}
	if len(offers) == 0 {
		return requests
	}
	for _, m := range meters {
		scoredOffers := t.ScoreOffers(m, offers, gridState, len(offers)-1)
		for _, o := range scoredOffers {
			seller := o.Offer
			requests[seller] = append(requests[seller], &TradeRequest{
				Meter: m, Score: o.Score,
			})
		}
	}
	return requests
}

func (t *Trader) ExecuteTrades(requests map[*Meter][]*TradeRequest, meters map[string]*Meter, gridState *GridState, duration time.Duration) error {
	for seller, tradeRequests := range requests {
		sort.Slice(tradeRequests, func(i, j int) bool {
			return tradeRequests[i].Score > tradeRequests[j].Score
		})
		buyer := tradeRequests[0].Meter
		seller.ParticipationCount++
		buyer.Trade = fmt.Sprintf("Buying:%s", seller.ID)
		seller.Trade = fmt.Sprintf("Selling:%s", buyer.ID)
		gridLimit := gridState.Intensity * gridState.Voltage * duration.Seconds()
		transferAmount := math.Min(
			math.Min(seller.Surplus, gridLimit),
			math.Abs(buyer.Surplus),
		)

		buyer.Purchased = transferAmount
		seller.Purchased = -transferAmount
	}
	return nil
}
