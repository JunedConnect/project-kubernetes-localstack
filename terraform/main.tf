module "s3" {
  source = "./modules/s3"

  app_name    = var.app_name
  bucket_name = var.bucket_name
}

module "dynamodb" {
  source = "./modules/dynamodb"

  app_name   = var.app_name
  table_name = var.table_name
  hash_key   = var.hash_key
}
