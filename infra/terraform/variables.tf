variable "aws_region" {
    type        = string
    description = "The AWS region to deploy resources in"
    default     = "us-east-1"
}

variable "instance_type" {
    type        = string
    description = "The EC2 instance type to use for the application servers"
    default     = "t3.medium"
}

variable "key_pair_name" {
    type        = string
    description = "The name of the AWS key pair to use for SSH access to EC2 instances"
    default     = "sisdist"
}

variable "ssh_cidr" {
    type        = string
    description = "The CIDR block to allow SSH access from"
    default     = "0.0.0.0/0"
}

# AMI de ubuntu
variable "ami_id" {
    type        = string
    description = "The ID of the Amazon Machine Image (AMI) to use for EC2 instances"
    default     = "ami-0c2b8ca1dad447f8" # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
}

variable "worker_count" {
  type        = number
  description = "Number of workers"
  default     = 3
}