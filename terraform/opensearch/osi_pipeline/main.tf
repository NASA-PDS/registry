terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/osi_pipeline.tfstate"
    region = "us-west-2"
  }
}

resource "aws_osis_pipeline" "pds_osi_pipeline" {
  pipeline_name               = "${var.pipeline_name}"
  pipeline_configuration_body = file("${var.pipeline_config_yaml_file}")
  pipeline_role_arn           = "{var.pipeline_role_arn}"

  max_units                   = var.pipeline_max_units
  min_units                   = var.pipeline_min_units 

  log_publishing_options {
    is_logging_enabled = true
    cloudwatch_log_destination {
      log_group = "${var.cloudwatch_log_group}"
    }
  }

  vpc_options {
    subnet_ids              = [ "${var.subnet_ids}" ]
    security_group_ids      = [ "${var.security_group_ids}" ]
    vpc_endpoint_management = "${var.vpc_endpoint_management}"
  }
}
