resource "google_compute_instance" "adk_web" {
  name         = "adk-web"
  machine_type = "n1-standard-1"
  zone         = var.zone
  project      = var.project_id

  # Shielded VM Config
  shielded_instance_config {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network    = var.network_name
    subnetwork = var.subnet_name
    network_ip = "10.0.0.10" # Static Internal IP
    # No access_config block = No External IP (Private VM)
  }

  service_account {
    email  = var.service_account_email
    scopes = ["cloud-platform"] # Full Access (Refine in production)
  }

  # ---------------------------------------------------------
  # STARTUP SCRIPT
  # ---------------------------------------------------------
  metadata_startup_script = <<EOF
#! /bin/bash
# 1. Install Ops Agent (Observability)
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# 2. Install Dependencies
sudo apt update
sudo apt install -y python3-venv git

# 3. Setup Environment
mkdir -p /opt/app
cd /opt/app
python3 -m venv .venv
source .venv/bin/activate

# 4. Install Python Libs
cat << 'EOT' > requirements.txt
google-cloud-aiplatform==1.114.0
google-adk==1.14.1
google-cloud-secret-manager==2.24.0
google-cloud-modelarmor==0.2.8
google-crc32c==1.7.1
google-cloud-storage==2.19.0
google-genai==1.38.0
httpx==0.28.1
google-auth==2.40.3
PyJWT==2.10.1
EOT

pip install -r requirements.txt

# 5. Download Code (Using variable for bucket name)
mkdir adk
gcloud storage cp --recursive gs://${var.code_bucket_name}/multi_agent adk

# 6. Run Application
cd adk
# Using nohup to keep running after script exit
nohup adk web --host 0.0.0.0 --port 8000 > /var/log/adk.log 2>&1 &
EOF
}

# ==============================================================================
# 2. BIND SECURE TAG (For Firewall Access)
# ==============================================================================
resource "google_tags_location_tag_binding" "binding" {
  parent    = "//compute.googleapis.com/projects/${var.project_id}/zones/${var.zone}/instances/${google_compute_instance.adk_web.instance_id}"
  tag_value = var.secure_tag_value_id
  location  = var.zone
}

# ==============================================================================
# 3. UNMANAGED INSTANCE GROUP
# ==============================================================================
resource "google_compute_instance_group" "ig_adk_web" {
  name      = "ig-adk-web"
  zone      = var.zone
  project   = var.project_id
  instances = [google_compute_instance.adk_web.self_link]

  named_port {
    name = "http8000"
    port = 8000
  }
}