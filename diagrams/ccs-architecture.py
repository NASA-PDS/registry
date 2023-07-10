from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, ECS, Fargate
from diagrams.aws.network import CF, ELB
from diagrams.aws.analytics import ES

with Diagram("ccs-architecture", show=False, direction="TB"):
    cf = CF("CloudFront")
    alb = ELB("ALB")
    cf >> alb
    with Cluster("EN"):
        with Cluster("EN-cluster"):
            ecs_en= ECS("ECS")
            fargate_en = Fargate("Fargate")
        en = [ecs_en,fargate_en] >> ES("EN Node")
    alb >> ecs_en
    with Cluster("DN-1"):
        with Cluster("DN1-cluster"):
            ecs_dn1 = ECS("ECS")
            fargate_dn1 = Fargate("Fargate")
        dn1 = [ecs_dn1,fargate_dn1] >> ES("EN Node")
    en >> Edge(style="bold", color="black") >> dn1
    with Cluster("DN-2"):
        with Cluster("DN2-cluster"):
            ecs_dn2 = ECS("ECS")
            fargate_dn2 = Fargate("Fargate")
        dn2 = [ecs_dn2,fargate_dn2] >> ES("EN Node")
    en >> Edge(style="bold", color="black") >> dn2
    with Cluster("GEO"):
        with Cluster("GEO-cluster"):
            ecs_geo = ECS("ECS")
            fargate_geo = Fargate("Fargate")
        geo = [ecs_geo,fargate_geo] >> ES("EN Node")
    en >> Edge(style="bold", color="black") >> geo
    alb >> Edge(style="dashed") >> fargate_geo
        