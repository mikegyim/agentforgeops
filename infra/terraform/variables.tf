variable "project" {
  type        = string
  default     = "agentforgeops"
  description = "Project tag prefix."
}

variable "env" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string
  default = "us-east-1"
}
