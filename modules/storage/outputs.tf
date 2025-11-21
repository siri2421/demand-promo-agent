output "bucket_details" {
  description = "Map of bucket names and their URLs"
  value = {
    for name, bucket in google_storage_bucket.buckets : 
    name => {
      name = bucket.name
      url  = bucket.url
    }
  }
}