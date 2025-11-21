
# Output the URL returned by the module
output "weather_mcp_url" {
  value = module.weather_mcp_server.service_url
}

# Output the IDs so you can see them in the terminal
output "model_armor_templates" {
  value = {
    req  = module.security.promo_req_id
    resp = module.security.promo_resp_id
  }
}

output "storage_buckets" {
  value = module.storage_setup.bucket_details
}

# Output the final LB IP so you can access your agent
output "load_balancer_ip" {
  value = module.loadbalancer_setup.lb_public_ip
}

/*
output "enterprise_portal_url" {
  value = module.agent_ui.ui_url
}

output "agent_service_account_email" {
  description = "The email of the service account for the agent."
  value       = google_service_account.agent_service_account.email
}

output "staging_bucket_name" {
  description = "The name of the GCS staging bucket."
  value       = google_storage_bucket.staging_bucket.name
}

*/