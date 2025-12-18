# Stage 1: Build the Go application
FROM golang:1.25-alpine AS builder

RUN apk --no-cache add git ca-certificates

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0 disables CGO for static compilation, which is a best practice
RUN CGO_ENABLED=0 go build -o /go-api-app ./cmd/server/main.go

FROM alpine:latest

WORKDIR /root/

COPY --from=builder /go-api-app .

EXPOSE 8080
CMD ["./energy-trading-simulator"]

