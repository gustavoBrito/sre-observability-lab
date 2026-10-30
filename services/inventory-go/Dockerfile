FROM golang:1.27-alpine AS build

WORKDIR /src

COPY go.mod go.sum ./
# Network needed once at build time; layer cached as long as go.sum is stable
RUN go mod download
RUN CGO_ENABLED=0 go build -o /bin/inventory ./cmd/inventory

FROM alpine:3.21 AS runtime

COPY --from=build /bin/inventory /bin/inventory

EXPOSE 8003 9003

ENTRYPOINT ["/bin/inventory"]
