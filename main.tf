provider "aws" {
  region = "eu-west-2" # Specify your desired region  
}

############################ EC2

data "aws_ami" "ubuntu-linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = var.ami_filter
  }
}

resource "aws_launch_configuration" "ubuntu-lc" {
  name_prefix     = "lc-ubuntu-"
  image_id        = data.aws_ami.ubuntu-linux.id
  instance_type   = var.instance_type
  security_groups = [aws_security_group.sg.id]

  lifecycle {
    create_before_destroy = true
  }
}


resource "aws_autoscaling_group" "nts" {
  name                 = "nts-asg"
  max_size             = 2
  min_size             = 1
  desired_capacity     = 2
  launch_configuration = aws_launch_configuration.ubuntu-lc.name
  vpc_zone_identifier  = [aws_subnet.public_subnet.id]

  tag {
    key                 = "Name"
    value               = "nts-instance"
    propagate_at_launch = true
  }
  tag {
    key                 = "Env"
    value               = "dev"
    propagate_at_launch = true
  }

  health_check_type         = "EC2"
  health_check_grace_period = 60

  lifecycle {
    create_before_destroy = true
  }
}

