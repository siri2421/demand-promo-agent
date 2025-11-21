
#The null_resource helps ensure the default VPC is deleted before proceeding
# as the default VPC removal sometimes fails if the project is brand new.
resource "null_resource" "delete_default_network" {
  triggers = {
    # Re-run this check if the project ID changes
    project = var.project_id
  }

  provisioner "local-exec" {
    # Attempt to delete the default network, suppress errors if it doesn't exist
    command = "gcloud compute networks delete default --project=${var.project_id} --quiet || true"
  }
}
# ---------------------------------------------------------
# 1. GET PROJECT NUMBER (Required for Firewall Policy Parent)
# ---------------------------------------------------------
data "google_project" "current" {
  project_id = var.project_id
}

# ==============================================================================
# 1. VPC NETWORK & SUBNET
# ==============================================================================
resource "google_compute_network" "agent_vpc" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
  # Required to associate with NGFW Firewall Policies
  network_firewall_policy_enforcement_order = "AFTER_CLASSIC_FIREWALL" 

  depends_on = [null_resource.delete_default_network]
}

resource "google_compute_subnetwork" "agent_subnet" {
  name          = var.subnet_name
  project       = var.project_id
  network       = google_compute_network.agent_vpc.id
  region        = var.region
  ip_cidr_range = "10.0.0.0/24"
  
  # Private Google Access (PGA) - Enabled
  private_ip_google_access = true 
}

# ==============================================================================
# 2. SECURE TAG (NETWORK TAGS)
#    (Must use google_tags resources)
# ==============================================================================
# Create the Tag Key
resource "google_tags_tag_key" "app_key" {
  provider     = google-beta
  parent       = "projects/${var.project_id}"
  short_name   = "app-secure"
  description  = "Application Tag Key for Firewall"
  purpose      = "GCE_FIREWALL"
  purpose_data = {
    # Syntax must be: "project_id/network_name"
    network = "${var.project_id}/${google_compute_network.agent_vpc.name}"
  }
}

# Create the Tag Value
resource "google_tags_tag_value" "agent_value" {
  provider     = google-beta
  parent       = google_tags_tag_key.app_key.id
  short_name   = "agent"
  description  = "Tag Value for Agentic Services"
}

# ==============================================================================
# 3. CLOUD NGFW FIREWALL POLICY (Global Network Firewall Policy)
# ==============================================================================

# 3.1 Create the Policy (Project Level)
resource "google_compute_network_firewall_policy" "fw_pol_agentic" {
  provider    = google-beta
  name        = "fw-pol-agentic"
  project     = var.project_id
  description = "Network Firewall Policy for Agentic Services"
}

# 3.2 Associate the policy with the VPC network
resource "google_compute_network_firewall_policy_association" "fw_pol_agentic_assoc" {
  provider          = google-beta
  name              = "fw-pol-agentic-assoc"
  project           = var.project_id
  attachment_target = google_compute_network.agent_vpc.id
  firewall_policy   = google_compute_network_firewall_policy.fw_pol_agentic.name
}

# 3.3 Rule 1: Ingress TCP 22 (SSH for IAP)
resource "google_compute_network_firewall_policy_rule" "rule_ssh_iap" {
  provider        = google-beta
  firewall_policy = google_compute_network_firewall_policy.fw_pol_agentic.name
  project         = var.project_id
  priority        = 1000
  action          = "allow"
  direction       = "INGRESS"
  description     = "Allow SSH from IAP"
  rule_name       = "allow-iap-ssh"

  match {
    src_ip_ranges = ["35.235.240.0/20"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["22"]
    }
  }

  # Apply rule to resources with this secure tag
  target_secure_tags {
    name = google_tags_tag_value.agent_value.id
  }
}

# 3.4 Rule 2: Ingress TCP 8000 (LB/Health Checks)
resource "google_compute_network_firewall_policy_rule" "rule_lb_hc" {
  provider        = google-beta
  firewall_policy = google_compute_network_firewall_policy.fw_pol_agentic.name
  project         = var.project_id
  priority        = 2000
  action          = "allow"
  direction       = "INGRESS"
  description     = "Allow Health Checks"
  rule_name       = "allow-health-checks"

  match {
    src_ip_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["8000"]
    }
  }

  target_secure_tags {
    name = google_tags_tag_value.agent_value.id
  }
}

# ==============================================================================
# 4. CLOUD ROUTER & CLOUD NAT (For Egress/Outbound Traffic)
# ==============================================================================
resource "google_compute_router" "cr_us_central1" {
  name    = "cr-us-central1"
  project = var.project_id
  region  = var.region
  network = google_compute_network.agent_vpc.id
}

resource "google_compute_router_nat" "cn_us_central1" {
  name                               = "cn-us-central1"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.cr_us_central1.name
  
  # Configure NAT to apply to the subnet we created
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
  
  subnetwork {
    name = google_compute_subnetwork.agent_subnet.self_link
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  nat_ip_allocate_option = "AUTO_ONLY"
  
  # Required to ensure NAT provides connection tracking/ports
  icmp_idle_timeout_sec    = 30
  tcp_established_idle_timeout_sec = 1200
}