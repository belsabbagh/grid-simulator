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
		seller := meters[sellerID]
		buyer := meters[buyers[0].Meter.ID]
		seller.ParticipationCount++
		buyer.From = sellerID
		gridLimit := gridState[len(gridState)-1] * gridState[len(gridState)-2] * inc.Seconds()
		transferAmount := math.Min(
			math.Min(seller.Surplus, gridLimit),
			math.Abs(buyer.Surplus),
		)

		buyer.Purchased = transferAmount
		seller.Purchased = -transferAmount
	}
	return transfers
}
