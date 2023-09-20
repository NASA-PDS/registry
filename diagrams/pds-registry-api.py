from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, ECS, Fargate
from diagrams.aws.network import CF, ELB
from diagrams.aws.analytics import ES
from diagrams.aws.security import SecretsManager
from diagrams.aws.cost import CostAndUsageReport
from diagrams.aws.management import Cloudwatch, SSM
from diagrams.onprem.container import Docker
from diagrams.onprem.iac import Terraform
from diagrams.oci.devops import APIService
from diagrams.programming.flowchart import Database
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Relationship

with Diagram("Registry-API", show=False, direction="TB", curvestyle="curved"):
    cf = CF("CloudFront")
    alb = ELB("ALB")
    secrets = SecretsManager("Secrets Manager")
    ssm = SSM("Systems Manager Parameter Store")
    cw = Cloudwatch("CloudWatch Logs")
    tf = Terraform("Terraform")
    cost = CostAndUsageReport("Cost and Usage Report")

    cf >> alb

    with Cluster("Image Creation"):
        ecr = ECR("ECR")
        ecr << Docker("Docker-Image")

    with Cluster("Image Processing"):
        ecs = ECS("ECS")
        fargate = Fargate("Fargate")
        alb >> ecs
        with Cluster("Task Execution"):
            task_execution = [[ssm,secrets] >> APIService("Registry-API"),
                              APIService("Registry-API"),
                              APIService("Registry-API")]
        ecr >> ecs

    with Cluster("ES Database"):
        opensearch_cluster = [ES("ES1"),
                              Database("ES DB"),
                              Database("ES DB"),
                              Database("ES DB")]
        task_execution[0] >> opensearch_cluster[0]

    with SystemBoundary("On-Prem"):
        harvest = Container(
            name = "Harvest",
            technology="Query OpenSearch"
        )
        reistry_mgr = Container(
            name = "Registry Manager",
            technology="Manage Registry-API"
        )

    reistry_mgr >> opensearch_cluster[0]
