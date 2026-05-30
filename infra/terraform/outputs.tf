output "vpc_id" {
  value = module.vpc.vpc_id
}

output "uploads_bucket" {
  value = aws_s3_bucket.uploads.bucket
}
