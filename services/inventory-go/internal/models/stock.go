// Package models stores the outward DTOs - nothing else imports them.

package models

// Stock is the outward read model for the /stock endpoint.
type Stock struct {
	SKU   string `json:"sku"`
	Units int    `json:"units"`
}
