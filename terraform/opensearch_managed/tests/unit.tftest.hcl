# Unit tests for OpenSearch Managed domain module
#
# PURPOSE: Catch regressions in the Terraform module code itself.
# These verify that hardcoded values in main.tf haven't drifted and that
# variables wire through correctly. They do NOT test AWS API behavior.
#
# WHAT BREAKS THESE: A developer changes enforce_https=true to false in main.tf.
# WHAT DOESN'T:      AWS API quirks, provider bugs, or deployed infrastructure state.
#
# For real AWS validation, use: tests/integration-test.sh
# Run these with: terraform test

# -----------------------------------------------------------------------------
# Mock providers - no real AWS calls
# -----------------------------------------------------------------------------

mock_provider "aws" {}

# -----------------------------------------------------------------------------
# Variables for test runs
# -----------------------------------------------------------------------------

variables {
  domain_name               = "test-domain"
  aws_region                = "us-west-2"
  ebs_volume_gb             = 100
  venue                     = "test"
  data_node_instance_type   = "t3.small.search"
  data_node_count           = 3
  master_node_instance_type = "t3.small.search"
  master_node_count         = 3
}

# -----------------------------------------------------------------------------
# Variable wiring tests
# -----------------------------------------------------------------------------

run "domain_name_wires_through" {
  command = plan

  variables {
    domain_name = "custom-domain"
  }

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.domain_name == "custom-domain"
    error_message = "Domain name variable should wire through to resource"
  }
}

run "domain_name_output_matches_input" {
  command = plan

  assert {
    condition     = output.domain_name == "test-domain"
    error_message = "domain_name output should match input variable"
  }
}

# -----------------------------------------------------------------------------
# Hardcoded config regression tests - catch accidental changes to main.tf
# -----------------------------------------------------------------------------

run "dedicated_master_is_enabled" {
  command = plan

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.cluster_config[0].dedicated_master_enabled == true
    error_message = "Dedicated master should be enabled (hardcoded in main.tf)"
  }
}

run "zone_awareness_is_enabled" {
  command = plan

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.cluster_config[0].zone_awareness_enabled == true
    error_message = "Zone awareness should be enabled (hardcoded in main.tf)"
  }
}

run "ebs_is_enabled" {
  command = plan

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.ebs_options[0].ebs_enabled == true
    error_message = "EBS should be enabled (hardcoded in main.tf)"
  }
}

run "https_is_enforced" {
  command = plan

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.domain_endpoint_options[0].enforce_https == true
    error_message = "HTTPS should be enforced (hardcoded in main.tf)"
  }
}

run "tls_policy_is_1_2" {
  command = plan

  assert {
    condition     = aws_opensearch_domain.pds-opensearch-domain.domain_endpoint_options[0].tls_security_policy == "Policy-Min-TLS-1-2-2019-07"
    error_message = "TLS 1.2 policy should be set (hardcoded in main.tf)"
  }
}

# -----------------------------------------------------------------------------
# SSM parameter path tests - catch path typos or refactoring mistakes
# -----------------------------------------------------------------------------

run "ssm_domain_name_path_format" {
  command = plan

  variables {
    component_name = "registry"
  }

  assert {
    condition     = aws_ssm_parameter.domain_name[0].name == "/pds/registry/opensearch_managed/domain_name"
    error_message = "SSM domain_name path should follow /pds/{component}/opensearch_managed/domain_name"
  }
}

run "ssm_domain_arn_path_format" {
  command = plan

  variables {
    component_name = "registry"
  }

  assert {
    condition     = aws_ssm_parameter.domain_arn[0].name == "/pds/registry/opensearch_managed/domain_arn"
    error_message = "SSM domain_arn path should follow /pds/{component}/opensearch_managed/domain_arn"
  }
}
