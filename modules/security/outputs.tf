output "templates" {
  description = "Map of all created Model Armor template IDs"
  value       = {
    for id, template in google_model_armor_template.templates : id => template.id
  }
}

# Helpers for easier access in root main.tf
output "promo_req_id" {
  value = google_model_armor_template.templates["promo-req"].id
}

output "promo_resp_id" {
  value = google_model_armor_template.templates["promo-resp"].id
}