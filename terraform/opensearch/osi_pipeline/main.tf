terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/osi_pipeline.tfstate"
    region = "us-west-2"
  }
}

resource "aws_osis_pipeline" "pds_osi_pipeline" {
  pipeline_name              = "${var.pipeline_name}"
  pipeline_configuration_body = file("${var.pipeline_config_yaml_file}")
      max_units                  = var.pipeline_max_units
      min_units                  = var.pipeline_min_units 

  log_publishing_options {
    is_logging_enabled = true
    cloudwatch_log_destination {
      log_group = "/aws/vendedlogs/OpenSearchService/ingestion/${var.pipeline_name}"
    }
  }
}
