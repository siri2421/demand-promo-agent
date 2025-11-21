output "secret_resource_id" {
  description = "The full resource name of the secret version (for the app to fetch)"
  value       = google_secret_manager_secret_version.maps_key_version.name
}