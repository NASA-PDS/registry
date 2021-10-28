# Define the cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "pds-${var.node_name_abbr}-reg-cluster"
}

# An ECR repository is a private alternative to Docker Hub.
data "aws_ecr_repository" "pds-registry-api-service" {
  name = "pds-registry-api-service"
}

# Log groups hold logs from our app.
resource "aws_cloudwatch_log_group" "pds-registry-log-group" {
  name = "/ecs/pds-${var.node_name_abbr}-reg-api-svc-task"
}

# The main service.
resource "aws_ecs_service" "pds-registry-reg-service" {
  name            = "pds-${var.node_name_abbr}-reg-service"
  task_definition = aws_ecs_task_definition.pds-registry-ecs-task.arn
  cluster         = aws_ecs_cluster.ecs_cluster.id
  launch_type     = "FARGATE"

  desired_count = 1

  # load_balancer {
    # target_group_arn = aws_lb_target_group.pds-registry-target-group.arn
    # container_name   = "pds-${var.node_name_abbr}-reg-container"
    # container_port   = "80"
  # }

  network_configuration {
    assign_public_ip = false

    security_groups = var.aws_fg_security_groups

    subnets = var.aws_fg_subnets
  }
}

# The task definition for our app.
resource "aws_ecs_task_definition" "pds-registry-ecs-task" {
  family = "pds-${var.node_name_abbr}-reg-api-svc-task"

  container_definitions = <<EOF
  [
    {
      "name": "pds-${var.node_name_abbr}-reg-container",
      "image": "${var.aws_fg_image}",
      "portMappings": [
        {
          "containerPort": 80
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-region": "${var.aws_region}",
          "awslogs-group": "${aws_cloudwatch_log_group.pds-registry-log-group.name}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck" : {
        "retries": 3,
        "command": [
          "CMD-SHELL",
          "date || exit 1"
        ],
        "timeout": 5,
        "interval": 60,
        "startPeriod": 300
      }
    }
  ]

EOF

  execution_role_arn = data.aws_iam_role.pds-task-execution-role.arn
  task_role_arn      = data.aws_iam_role.pds-task-execution-role.arn

  # These are the minimum values for Fargate containers.
  cpu                      = 256
  memory                   = 512
  requires_compatibilities = ["FARGATE"]

  # This is required for Fargate containers
  network_mode = "awsvpc"
}

# role under which ECS will execute tasks.
data "aws_iam_role" "pds-task-execution-role" {
  name    = "am-ecs-task-execution"
}

# resource "aws_lb_target_group" "pds-registry-target-group" {
  # name        = "pds-${var.node_name_abbr}-reg-tgt"
  # port        = 80
  # protocol    = "HTTP"
  # target_type = "ip"
  # vpc_id      = "${var.aws_fg_vpc}"

  # health_check {
    # enabled = true
    # path    = "/swagger-ui.html"
  # }

  # depends_on = [data.aws_alb.pds-alb]
# }

# data "aws_alb" "pds-alb" {
  # name   = "pds-en-ecs"      # TODO: Change name to be more global
# }
