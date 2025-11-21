output "network_name" {
  description = "The name of the created VPC network"
  value       = google_compute_network.agent_vpc.name
}

output "subnet_name" {
  description = "The name of the primary subnetwork"
  value       = google_compute_subnetwork.agent_subnet.name
}

output "secure_tag_value_id" {
  description = "The full resource ID of the secure tag (app/agent)"
  value       = google_tags_tag_value.agent_value.id
}