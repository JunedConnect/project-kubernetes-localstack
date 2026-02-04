variable "aws_tags" {
  description = "Tags for Resources"
  type        = map(string)
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "hash_key" {
  description = "DynamoDB hash key"
  type        = string
}
