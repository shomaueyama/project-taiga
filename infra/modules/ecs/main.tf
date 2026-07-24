resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/taiga/${var.name_prefix}/backend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/taiga/${var.name_prefix}/worker"
  retention_in_days = 30
}

data "aws_iam_policy_document" "task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.name_prefix}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name               = "${var.name_prefix}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role.json
}

resource "aws_iam_role_policy" "task" {
  name = "${var.name_prefix}-app-access"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::${var.uploads_bucket_id}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "secretsmanager:GetSecretValue"
        ]
        Resource = [var.database_url_parameter_arn]
      }
    ]
  })
}

locals {
  common_environment = [
    { name = "APP_ENV", value = "production" },
    { name = "LOCAL_AUTH_ENABLED", value = "false" },
    { name = "RUNNER_ENABLED", value = "false" },
    { name = "EXAM_ENABLED", value = "true" },
    { name = "UPLOAD_STORAGE_BACKEND", value = "s3" },
    { name = "UPLOADS_BUCKET", value = var.uploads_bucket_id }
  ]
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.name_prefix}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.backend_image
      essential = true
      portMappings = [{ containerPort = var.app_port, protocol = "tcp" }]
      environment  = local.common_environment
      secrets      = [{ name = "DATABASE_URL", valueFrom = var.database_url_parameter_arn }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name        = "worker"
      image       = var.worker_image
      essential   = true
      command     = ["python", "-m", "taiga.worker"]
      environment = local.common_environment
      secrets     = [{ name = "DATABASE_URL", valueFrom = var.database_url_parameter_arn }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "backend" {
  name            = "${var.name_prefix}-backend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type      = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.backend_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "backend"
    container_port   = var.app_port
  }
}

resource "aws_ecs_service" "worker" {
  name            = "${var.name_prefix}-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type      = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.worker_security_group_id]
    assign_public_ip = false
  }
}

