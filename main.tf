terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS provider region used for API calls. Route 53 is global."
  type        = string
  default     = "us-east-1"
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID containing domain_name."
  type        = string
  default     = "Z123EXAMPLE"
}

variable "domain_name" {
  description = "Failover DNS name presented to clients."
  type        = string
  default     = "app.example.com"
}

variable "primary_endpoint" {
  description = "Primary regional DNS endpoint, without scheme."
  type        = string
  default     = "primary.example.net"
}

variable "secondary_endpoint" {
  description = "Secondary regional DNS endpoint, without scheme."
  type        = string
  default     = "secondary.example.net"
}

variable "health_path" {
  description = "HTTPS path used by Route 53 health checks."
  type        = string
  default     = "/health"
}

resource "aws_route53_health_check" "primary" {
  fqdn              = var.primary_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_path
  request_interval  = 30
  failure_threshold = 3

  tags = {
    Name    = "multi-region-primary"
    Project = "Multi-Region-Failover-AWS"
  }
}

resource "aws_route53_health_check" "secondary" {
  fqdn              = var.secondary_endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = var.health_path
  request_interval  = 30
  failure_threshold = 3

  tags = {
    Name    = "multi-region-secondary"
    Project = "Multi-Region-Failover-AWS"
  }
}

resource "aws_route53_record" "primary" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = 30
  records = [var.primary_endpoint]

  set_identifier  = "primary-region"
  health_check_id = aws_route53_health_check.primary.id

  failover_routing_policy {
    type = "PRIMARY"
  }
}

resource "aws_route53_record" "secondary" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = 30
  records = [var.secondary_endpoint]

  set_identifier  = "secondary-region"
  health_check_id = aws_route53_health_check.secondary.id

  failover_routing_policy {
    type = "SECONDARY"
  }
}

output "failover_dns_name" {
  description = "Client-facing Route 53 failover name."
  value       = var.domain_name
}

output "primary_health_check_id" {
  value = aws_route53_health_check.primary.id
}

output "secondary_health_check_id" {
  value = aws_route53_health_check.secondary.id
}
