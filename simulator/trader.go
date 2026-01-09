package simulator

import (
	"math"
	"sort"
	"time"
)

type Trader struct {
	tradeChooser BestOffersFunc
	Trades       map[string]string
}

func NewTrader(tradeChooser BestOffersFunc) *Trader {
	return &Trader{
		tradeChooser: tradeChooser,
		Trades:       make(map[string]string),
	}
}
func (t *Trader) ScoreOffers(m *Meter, offers []*Meter, gridState []float64, limit int) []ScoredOffer {
	choices := t.tradeChooser(m.Surplus, offers, gridState, limit)
	return choices
}

func (t *Trader) ExecuteTrades(requests map[string][]*Request, meters map[string]*Meter, gridState []float64, inc time.Duration) map[string]float64 {
	transfers := make(map[string]float64)
	for sellerID, buyers := range requests {
		sort.Slice(buyers, func(i, j int) bool {
			return buyers[i].Score > buyers[j].Score
		})

		buyerID := buyers[0].Meter.ID
		meters[sellerID].ParticipationCount++
		t.Trades[buyerID] = sellerID
		gridLimit := gridState[len(gridState)-1] * gridState[len(gridState)-2] * inc.Seconds()
		transferAmount := math.Min(
			math.Min(meters[sellerID].Surplus, gridLimit),
			math.Abs(meters[buyerID].Surplus),
		)

		transfers[buyerID] = transferAmount
		transfers[sellerID] = -transferAmount
	}
	return transfers
}
