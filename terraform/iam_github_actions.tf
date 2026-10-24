locals {
  artifacts_account_id = "432410731887"

  codeartifact_domain_arn = "arn:aws:codeartifact:${var.aws_region}:${local.artifacts_account_id}:domain/webbpulse"

  codeartifact_repositories = ["npm", "npm-store", "pypi-store", "python", "shared"]

  github_actions_codeartifact_statements = [
    {
      sid       = "CodeArtifactToken"
      actions   = ["codeartifact:GetAuthorizationToken"]
      resources = [local.codeartifact_domain_arn]
    },
    {
      sid = "CodeArtifactRead"
      actions = [
        "codeartifact:DescribePackageVersion",
        "codeartifact:DescribeRepository",
        "codeartifact:GetPackageVersionAsset",
        "codeartifact:GetPackageVersionReadme",
        "codeartifact:GetRepositoryEndpoint",
        "codeartifact:ListPackageVersionAssets",
        "codeartifact:ListPackageVersionDependencies",
        "codeartifact:ListPackageVersions",
        "codeartifact:ListPackages",
        "codeartifact:ReadFromRepository",
      ]
      resources = concat(
        [for name in local.codeartifact_repositories : "arn:aws:codeartifact:${var.aws_region}:${local.artifacts_account_id}:repository/webbpulse/${name}"],
        [for name in local.codeartifact_repositories : "arn:aws:codeartifact:${var.aws_region}:${local.artifacts_account_id}:package/webbpulse/${name}/*"],
      )
    },
    {
      sid       = "CodeArtifactBearerToken"
      actions   = ["sts:GetServiceBearerToken"]
      resources = ["*"]
      condition = {
        StringEquals = {
          "sts:AWSServiceName" = ["codeartifact.amazonaws.com"]
        }
      }
    },
  ]

  github_actions_gate_statements = [for statement in [
    {
      sid       = "E2EReadGateSigningKey"
      actions   = ["ssm:GetParameter"]
      resources = [one(module.company_site_gate[*].signing_key_ssm_parameter_arn)]
    },
    {
      sid       = "E2EDecryptGateSigningKey"
      actions   = ["kms:Decrypt"]
      resources = [data.aws_kms_alias.ssm.target_key_arn]
      condition = {
        StringEquals = { "kms:ViaService" = ["ssm.${var.aws_region}.amazonaws.com"] }
      }
    },
  ] : statement if local.company_site_gate_enabled]
}

module "github_actions_deploy_role" {
  source  = "terraform.webbpulse.com/WebbPulse/platform-modules/aws//modules/github-actions-role"
  version = "~> 2.39"

  role_name        = "${local.prefix}-site-github-actions-deploy"
  role_description = "Deploys the company site from WebbPulse/WebbPulse-Site and runs its e2e suite."

  create_oidc_provider = false
  oidc_provider_arn    = data.aws_iam_openid_connect_provider.github.arn

  subjects = [
    "${local.repository_subject}:environment:staging",
    "${local.repository_subject}:environment:production",
  ]

  policy_statements = concat(local.github_actions_codeartifact_statements, local.github_actions_gate_statements)

  spa_deploy = {
    bucket_arns       = [module.company_site.bucket_arn]
    distribution_arns = [module.company_site.distribution_arn]
  }
}

module "github_actions_ci_role" {
  source  = "terraform.webbpulse.com/WebbPulse/platform-modules/aws//modules/github-actions-role"
  version = "~> 2.39"

  role_name        = "${local.prefix}-site-github-actions-ci"
  role_description = "Read-only CodeArtifact access for pull request CI in WebbPulse/WebbPulse-Site."

  create_oidc_provider = false
  oidc_provider_arn    = data.aws_iam_openid_connect_provider.github.arn

  subjects = [
    "${local.repository_subject}:pull_request",
    "${local.repository_subject}:ref:refs/heads/staging",
    "${local.repository_subject}:ref:refs/heads/main",
  ]

  inline_policy_name = "codeartifact-read"

  policy_statements = local.github_actions_codeartifact_statements
}
