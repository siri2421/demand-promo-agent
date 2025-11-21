output "instance_group_url" {
  value = google_compute_instance_group.ig_adk_web.self_link
}

output "vm_internal_ip" {
  value = google_compute_instance.adk_web.network_interface[0].network_ip
}