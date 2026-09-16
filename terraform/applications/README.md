# PDS Registry — Applications

Deploys the application-layer infrastructure: credentials API (API Gateway + Lambda) and registry-sweepers (ECS Fargate).

## Technical architecture

```mermaid
flowchart TB
    subgraph clients["External clients"]
        PDS["PDS client\n(needs temporary AWS credentials)"]
        MWAA["MWAA / Airflow\n(scheduled sweeper runs)"]
    end

    subgraph vpc["VPC (private subnets + security groups)"]
        APIGW["API Gateway\nGET /credentials"]
        Lambda["Lambda\npds-registry-get-awskeys-from-cognitojwt"]
        subgraph fargate["ECS Fargate (one task definition per node)"]
            SweeperEN["registry-sweepers — en"]
            SweeperGEO["registry-sweepers — geo"]
        end
    end

    subgraph aws_managed["AWS managed services"]
        Cognito["Cognito\nUser Pool + Identity Pool"]
        AOSS["OpenSearch Serverless\n(AOSS endpoint)"]
        CW_Lambda["CloudWatch Logs\n/aws/lambda/pds-registry-get-awskeys-..."]
        CW_ECS["CloudWatch Logs\n/pds/ecs/pds-registry-sweepers-{node}-task"]
        SSM["SSM Parameter Store\n/pds/cds-infra/iam/roles/..."]
    end

    PDS -->|"GET /credentials + JWT"| APIGW
    APIGW --> Lambda
    Lambda -->|"validate JWT via JWKS URL"| Cognito
    Lambda -->|"assume role → temp credentials"| Cognito
    Lambda -.->|"logs"| CW_Lambda
    Lambda -.->|"reads IAM role ARNs at deploy time"| SSM

    MWAA -->|"RunTask (iam:PassRole)"| SweeperEN
    MWAA -->|"RunTask (iam:PassRole)"| SweeperGEO
    SweeperEN -->|"index / sweep"| AOSS
    SweeperGEO -->|"index / sweep"| AOSS
    SweeperEN -.->|"logs"| CW_ECS
    SweeperGEO -.->|"logs"| CW_ECS
```

<!-- BEGIN_TF_DOCS -->
<!-- END_TF_DOCS -->
