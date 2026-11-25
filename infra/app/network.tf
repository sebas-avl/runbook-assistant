# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "runbook-assistant"
  }
}

# Subnets (2 publics and 2 privates)
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-north-1a"

  tags = {
    Name = "runbook-assistant-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-north-1b"

  tags = {
    Name = "runbook-assistant-public-b"
  }
}


resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "eu-north-1a"

  tags = {
    Name = "runbook-assistant-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = "eu-north-1b"

  tags = {
    Name = "runbook-assistant-private-b"
  }
}

# Internet access for the public subnets (IGW)
# Internet Gateway Creation
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "runbook-assistant"
  }
}

# Public route table creation 
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "runbook-assistant-public"
  }
}

# Route (a line/rule inside the table) in public route table = public -> internet
resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# Private route table creation 
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "runbook-assistant-private"
  }
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private.id
}

#Security Group of ALB (is open on port 80)
resource "aws_security_group" "alb" {
  name        = "runbook-assistant-alb"
  description = "Load Balancer: HTTP from the internet"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "runbook-assistant-alb"
  }
}

#Security Group of Service - ECS service accepts traffic only from ALB
resource "aws_security_group" "service" {
  name        = "runbook-assistant-service"
  description = "ECS service: only traffic from the load balancer"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "runbook-assistant-service"
  }
}

#Ingress rule from internet to alb-security_group (for ALB Security Group)
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

#Egress rule from alb-security group to service (for ALB Security Group)
resource "aws_vpc_security_group_egress_rule" "alb_to_service" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.service.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

#Ingress rule from alb to service-security_group (for Service Security Group)
resource "aws_vpc_security_group_ingress_rule" "service_from_alb" {
  security_group_id            = aws_security_group.service.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

#Egress rule from service-security group to all (for Service Security Group)
resource "aws_vpc_security_group_egress_rule" "service_to_all" {
  security_group_id = aws_security_group.service.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# NAT: lets the private subnets reach the internet (Bedrock, ECR) without being reachable from it
# Elastic IP creation
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "runbook-assistant-nat"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id

  tags = {
    Name = "runbook-assistant"
  }

  depends_on = [aws_internet_gateway.main]
}

# Add a new route (a line/rule inside the table) in the private route table = send internet traffic (0.0.0.0/0) to the NAT
resource "aws_route" "private_nat" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}