locals {
  # List of base names for the buckets
  bucket_names = toset([
    "agent-inventory", 
    "adk-code", 
    "agent-staging"
  ])
}

# 1. Create Buckets
resource "google_storage_bucket" "buckets" {
  for_each = local.bucket_names

  # Append project_id to ensure global uniqueness
  name          = "${each.key}-bucket-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  public_access_prevention = "enforced"
  force_destroy            = true # Allows deleting bucket even if it has files (safe for demos)
}

# 2. Upload inventory.csv (Only to the inventory bucket)
resource "google_storage_bucket_object" "inventory_file" {
  name    = "inventory.csv"
  # We select the specific bucket from the map created above
  bucket  = google_storage_bucket.buckets["agent-inventory"].name
  source = "${path.root}/inventory.csv"
  content_type = "text/csv"
}

# 3. Grant Access to Service Account
resource "google_storage_bucket_iam_member" "viewer_access" {
  for_each = google_storage_bucket.buckets

  bucket = each.value.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.service_account_email}"
}

# ==============================================================================
# 4. AUTOMATED CODE UPLOAD
#    Recursively uploads everything from promo-agent/multi_agent to the bucket
# ==============================================================================
resource "google_storage_bucket_object" "multi_agent_code" {
  # 1. Find all files in the local folder (recursive '**')
  #    ${path.root} ensures we look from the project root, not the module folder
  for_each = fileset("${path.root}/promo-agent/multi_agent", "**")

  # 2. Set the destination path in the bucket
  #    Result: gs://bucket-name/multi_agent/file.py
  name   = "multi_agent/${each.value}"
  
  # 3. Select the correct bucket
  bucket = google_storage_bucket.buckets["adk-code"].name
  
  # 4. Source file location
  source = "${path.root}/promo-agent/multi_agent/${each.value}"

  # 5. Detect content type automatically
  #    (Terraform usually does this well, or defaults to application/octet-stream)
}