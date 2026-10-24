locals {
  project = "webbpulse"

  prefix = "${local.project}-${var.environment}"

  common_tags = {
    Project     = local.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  workload_dns_role_arn = var.environment == "production" ? var.route53_write_role_arn : ""

  repository_subject = "repo:WebbPulse@185014056/WebbPulse-Site@1431798864"
}
