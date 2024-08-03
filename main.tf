provider "aws" {
  region = "eu-west-2" # Specify your desired region  
}

############################ EC2

resource "aws_instance" "gold_image" {
  ami                         = "ami-01ec84b284795cbc7" # Ubuntu 24.04 AMI ID  
  instance_type               = "t2.micro"
  associate_public_ip_address = false
  vpc_security_group_ids      = [aws_security_group.sg.id]
  tags = {
    Name = "gold_image"
    Env  = "dev"
    Gold = "true"
  }

  # Ensure the instance is terminated when destroyed  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_instance" "nts_test-1" {
  ami                         = "ami-02240cf608bc9cd79" # Ubuntu 24.04 AMI ID  
  instance_type               = "t2.micro"
  associate_public_ip_address = false

  tags = {
    Name = "nts-test-1"
    Env  = "dev"
  }

  # Ensure the instance is terminated when destroyed  
  lifecycle {
    create_before_destroy = true
  }
}



############################ SG

# Security Group for ALB 
resource "aws_security_group" "sg" {
}


resource "aws_vpc_security_group_ingress_rule" "allow_http_into_alb" {
  security_group_id = aws_security_group.sg.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "tcp"
  from_port   = 80
  to_port     = 80
}


# data "aws_ami" "amzn-linux-2023-ami" {
#   most_recent = true
#   owners      = ["amazon"]

#   filter {
#     name   = "name"
#     values = ["al2023-ami-2023.*-x86_64"]
#   }
# }
