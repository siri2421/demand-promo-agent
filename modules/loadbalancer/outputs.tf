output "lb_public_ip" {
  description = "The Public IP address of the Global Load Balancer"
  value       = google_compute_global_forwarding_rule.fe_adk_web.ip_address
}