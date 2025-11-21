output "deployment_complete_id" {
  value       = null_resource.deploy_to_reasoning_engine.id
  description = "ID timestamp indicating deployment is finished"
}