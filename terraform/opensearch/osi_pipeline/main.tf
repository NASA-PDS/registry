terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/osi_pipeline.tfstate"
    region = "us-west-2"
  }
}

resource "aws_osis_pipeline" "pds_osi_pipeline" {
  pipeline_name              = "${var.pipeline_name}""
  pipeline_configuration_body = <<EOF

    version: '2'
    extension:
      osis_configuration_metadata:
        builder_type: visual
    pds-dev-test-pipeline:
      source:
        opensearch:
          acknowledgments: true
          hosts:
            - '${var.source_opensearch_uri}'
          aws:
            serverless: var.source_opensearch_serverless
            region: var.aws_region
            serverless_options:
              network_policy_name: ''
          indices:
             include:
               - index_name_regex: '*'
          search_options:
            batch_size: '${var.source_batch_size}''
      processor: []
      sink:
        - opensearch:
            hosts:
              - '${var.sink_opensearch_uri}'
            aws:
              serverless: var.sink_opensearch_serverless
              region: var.aws_region
            index_type: custom
            index: '${getMetadata("opensearch-index")}'
            document_id: '${getMetadata("opensearch-document_id")}'
      max_units                  = var.pipeline_max_units
      min_units                  = var.pipeline_min_units 

EOF

  log_publishing_options {
    is_logging_enabled = true
    cloudwatch_log_destination {
      log_group = "/aws/vendedlogs/OpenSearchService/ingestion/${var.pipeline_name}"
    }
  }
}
