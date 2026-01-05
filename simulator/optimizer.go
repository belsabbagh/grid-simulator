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
	Offer Meter
	Score float64
}

// Model represents the weight matrix extracted from Keras
type Model struct {
	Weights *mat.Dense
}

func LoadWeights(path string) (func([]float64) float64, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)

	if _, err := reader.Read(); err != nil {
		return nil, err
	}

	var weightValues []float64
	var bias float64

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}

		val, _ := strconv.ParseFloat(record[3], 64)

		if record[1] == "weight" {
			weightValues = append(weightValues, val)
		} else if record[1] == "bias" {
			bias = val
		}
	}
	weights := mat.NewVecDense(len(weightValues), weightValues)

	return func(x []float64) float64 {
		if len(x) != len(weightValues) {
			return 0.0
		}
		input := mat.NewVecDense(len(x), x)
		res := mat.Dot(weights, input) + bias
		return res
	}, nil
}

// MkPredictFunction calculates efficiency and duration
func MkPredictFunction(effModelPath, durModelPath string) func(float64, float64, float64, float64, float64) (float64, float64) {
	effModel, err := LoadWeights(effModelPath)
	if err != nil {
		fmt.Printf("Error loading %s: %s", effModelPath, err)
	}
	durModel, err := LoadWeights(durModelPath)
	if err != nil {
		fmt.Printf("Error loading %s: %s", durModelPath, err)
	}
	return func(gridLoad, gridTemp, voltage, intensity, amount float64) (float64, float64) {
		// efficiency_model([[grid_load_gwh, grid_temp_c]])
		gridLoss := effModel([]float64{gridLoad, gridTemp})
		efficiency := (gridLoad - gridLoss) / gridLoad

		// duration_model([[voltage_v, global_intensity_A, efficiency, transaction_amount_wh]])
		duration := durModel([]float64{voltage, intensity, efficiency, amount})

		return efficiency, duration
	}
}

// MkFitnessFunction calculates the fitness score
func MkFitnessFunction(effPath string, durPath string, weights []float64) func(float64, Offer, []float64) float64 {
	predict := MkPredictFunction(effPath, durPath)

	if weights == nil {
		weights = []float64{1, -1, 1, -1, 1, -1}
	}

	return func(amountNeeded float64, offer Meter, metrics []float64) float64 {
		eff, dur := predict(metrics[0], metrics[1], metrics[2], metrics[3], offer.Amount)

		// Placeholder for calculate_transaction_score logic
		quality := (offer.Amount - amountNeeded) / (dur + 1e-6)

		params := []float64{
			eff,
			dur,
			quality,
			float64(offer.ParticipationCount),
			amountNeeded,
			offer.Amount,
		}

		// Manual dot product for weights
		var score float64
		for i := range weights {
			score += weights[i] * params[i]
		}
		return score
	}
}

func ChooseBestOffers(amountNeeded float64, offers []Meter, metrics []float64, count int) []ScoredOffer {
	fitness := MkFitnessFunction("eff.json", "dur.json", nil)

	// Shuffle and Subset (Random Sample)
	rand.Shuffle(len(offers), func(i, j int) { offers[i], offers[j] = offers[j], offers[i] })
	if len(offers) > count {
		offers = offers[:count]
	}

	scored := make([]ScoredOffer, len(offers))
	for i, o := range offers {
		scored[i] = ScoredOffer{Offer: o, Score: fitness(amountNeeded, o, metrics)}
	}

	// Sort descending
	sort.Slice(scored, func(i, j int) bool {
		return scored[i].Score > scored[j].Score
	})

	return scored
}

type FitnessFunc func(amountNeeded float64, offer Meter, metrics []float64) float64
type BestOffersFunc func(amountNeeded float64, offers []Meter, metrics []float64, count int) []ScoredOffer

func MkChooseBestOffersFunction(
	effPath, durPath, qualPath string,
	weights []float64,
) BestOffersFunc {

	fitness := MkFitnessFunction(effPath, durPath, weights)

	return func(amountNeeded float64, offers []Meter, metrics []float64, count int) []ScoredOffer {
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
