# ==============================================================================
# 1. HEALTH CHECK (TCP 8000)
#    Verifies the agent is listening before sending traffic
# ==============================================================================
resource "google_compute_health_check" "hc_tcp8000" {
  name               = "hc-tcp8000"
  project            = var.project_id
  timeout_sec        = 5
  check_interval_sec = 5

  tcp_health_check {
    port = "8000"
  }
}

# ==============================================================================
# 2. BACKEND SERVICE
#    Defines how traffic is distributed to the Instance Group
# ==============================================================================
resource "google_compute_backend_service" "be_adk_web" {
  name                  = "be-adk-web"
  project               = var.project_id
  protocol              = "HTTP"
  port_name             = "http8000" # Must match the Named Port in the Instance Group
  load_balancing_scheme = "EXTERNAL" # Global Load Balancer
  timeout_sec           = 86400      # 24 Hours (Ideal for Agent streaming/WebSockets)

  health_checks = [google_compute_health_check.hc_tcp8000.id]

  backend {
    group           = var.instance_group_url
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  # Enable Logging (Sample Rate 1 = 100%)
  log_config {
    enable      = true
    sample_rate = 1.0
  }

  enable_cdn = false
  
  # Cloud Armor (None) - Explicitly set security policy to null if previously set, or omit.
  security_policy = null 
}

# ==============================================================================
# 3. URL MAP
#    Routes incoming requests to the Backend Service
# ==============================================================================
resource "google_compute_url_map" "adk_map" {
  name            = "glb-adk-web"
  project         = var.project_id
  default_service = google_compute_backend_service.be_adk_web.id
}

# ==============================================================================
# 4. TARGET PROXY
#    Terminates the HTTP connection
# ==============================================================================
resource "google_compute_target_http_proxy" "adk_proxy" {
  name    = "glb-adk-web-proxy"
  project = var.project_id
  url_map = google_compute_url_map.adk_map.id
}

# ==============================================================================
# 5. GLOBAL FORWARDING RULE (Frontend)
#    The entry point (Public IP)
# ==============================================================================
resource "google_compute_global_forwarding_rule" "fe_adk_web" {
  name       = "fe-adk-web"
  project    = var.project_id
  target     = google_compute_target_http_proxy.adk_proxy.id
  port_range = "80"
  load_balancing_scheme = "EXTERNAL"
}