data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}
