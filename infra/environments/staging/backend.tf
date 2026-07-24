terraform {
  backend "s3" {
    bucket         = "REPLACE_ME-taiga-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "REPLACE_ME-taiga-terraform-locks"
  }
}

