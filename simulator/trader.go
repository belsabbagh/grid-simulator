package simulator

import (
	"math"
	"sort"
	"time"
)

type Trader struct {
	tradeChooser BestOffersFunc
}

func NewTrader(tradeChooser BestOffersFunc) *Trader {
	return &Trader{
		tradeChooser: tradeChooser,
	}
}
func (t *Trader) ScoreOffers(m *Meter, offers []*Meter, gridState []float64, limit int) []ScoredOffer {
	choices := t.tradeChooser(m.Surplus, offers, gridState, limit)
	return choices
}

func (t *Trader) ExecuteTrades(requests map[string][]*TradeRequest, meters map[string]*Meter, gridState []float64, duration time.Duration) error {
	for sellerID, buyers := range requests {
		sort.Slice(buyers, func(i, j int) bool {
			return buyers[i].Score > buyers[j].Score
		})
		seller := meters[sellerID]
		buyer := meters[buyers[0].Meter.ID]
		seller.ParticipationCount++
		buyer.From = sellerID
		gridLimit := gridState[len(gridState)-1] * gridState[len(gridState)-2] * duration.Seconds()
		transferAmount := math.Min(
			math.Min(seller.Surplus, gridLimit),
			math.Abs(buyer.Surplus),
		)

		buyer.Purchased = transferAmount
		seller.Purchased = -transferAmount
	}
	return nil
}
