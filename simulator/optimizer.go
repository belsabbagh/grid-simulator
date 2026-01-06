package simulator

import (
	"encoding/csv"
	"fmt"
	"io"
	"math/rand"
	"os"
	"sort"
	"strconv"

	"gonum.org/v1/gonum/mat"
)

type ScoredOffer struct {
	Offer *Meter
	Score float64
}

type Model struct {
	Weights *mat.VecDense
	Bias    float64
}

func NewModel() *Model {
	return &Model{
		Weights: nil,
		Bias:    0.0,
	}
}

func (m *Model) LoadFromCSV(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	reader := csv.NewReader(file)

	if _, err := reader.Read(); err != nil {
		return err
	}

	var weightValues []float64
	var bias float64

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		val, err := strconv.ParseFloat(record[3], 64)
		if err != nil {
			continue
		}

		if record[1] == "weight" {
			weightValues = append(weightValues, val)
		} else if record[1] == "bias" {
			bias = val
		}
	}

	m.Weights = mat.NewVecDense(len(weightValues), weightValues)
	m.Bias = bias
	return nil
}

func (m *Model) Predict(x []float64) (float64, error) {
	if m.Weights == nil {
		return 0, fmt.Errorf("uninitialized weights")
	}

	if len(x) != m.Weights.Len() {
		return 0, fmt.Errorf("dimension mismatch")
	}

	input := mat.NewVecDense(len(x), x)
	res := mat.Dot(m.Weights, input) + m.Bias
	return res, nil
}

func MkPredictFunction(effModelPath, durModelPath string) func(float64, float64, float64, float64, float64) (float64, float64) {
	effModel := NewModel()
	durModel := NewModel()
	err := effModel.LoadFromCSV(effModelPath)
	if err != nil {
		fmt.Printf("Error loading %s: %s", effModelPath, err)
	}
	err = durModel.LoadFromCSV(durModelPath)
	if err != nil {
		fmt.Printf("Error loading %s: %s", durModelPath, err)
	}
	return func(gridLoad float64, gridTemp float64, voltage float64, intensity float64, amount float64) (float64, float64) {
		effModelParams := []float64{gridLoad, gridTemp}
		gridLoss, _ := effModel.Predict(effModelParams)
		efficiency := (gridLoad - gridLoss) / gridLoad
		durModelParams := []float64{voltage, intensity, efficiency, amount}
		duration, _ := durModel.Predict(durModelParams)
		return efficiency, duration
	}
}

func MkFitnessFunction(effPath string, durPath string, weights []float64) func(float64, *Meter, []float64) float64 {
	predict := MkPredictFunction(effPath, durPath)

	if weights == nil {
		weights = []float64{1, -1, 1, -1, 1, -1}
	}

	return func(amountNeeded float64, offer *Meter, metrics []float64) float64 {
		eff, dur := predict(metrics[0], metrics[1], metrics[2], metrics[3], offer.Surplus)

		quality := (offer.Surplus - amountNeeded) / (dur + 1e-6)

		params := []float64{
			eff,
			dur,
			quality,
			float64(offer.ParticipationCount),
			amountNeeded,
			offer.Surplus,
		}

		var score float64
		for i := range weights {
			score += weights[i] * params[i]
		}
		return score
	}
}

type FitnessFunc func(amountNeeded float64, offer *Meter, metrics []float64) float64
type BestOffersFunc func(amountNeeded float64, offers []*Meter, metrics []float64, count int) []ScoredOffer

func MkChooseBestOffersFunction(
	effPath, durPath, qualPath string,
	weights []float64,
) BestOffersFunc {

	fitness := MkFitnessFunction(effPath, durPath, weights)

	return func(amountNeeded float64, offers []*Meter, metrics []float64, count int) []ScoredOffer {
		scoredOffers := make([]ScoredOffer, len(offers))
		for i, offer := range offers {
			scoredOffers[i] = ScoredOffer{
				Offer: offer,
				Score: fitness(amountNeeded, offer, metrics),
			}
		}

		sort.Slice(scoredOffers, func(i, j int) bool {
			return scoredOffers[i].Score > scoredOffers[j].Score
		})

		if len(scoredOffers) > count {
			return scoredOffers[:count]
		}
		return scoredOffers
	}
}
