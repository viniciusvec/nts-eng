
############################ SG

# Security Group for ALB 
resource "aws_security_group" "sg" {
  vpc_id = aws_vpc.main.id
}


resource "aws_vpc_security_group_ingress_rule" "allow_http_into_alb" {
  security_group_id = aws_security_group.sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}


############################ VPC

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Subnets 
resource "aws_subnet" "public_subnet" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = var.availability_zones[0]
}

