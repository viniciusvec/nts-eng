# nts-eng

Hello.

### Directory Structure

```shell
|-- LICENSE
|-- README.md
|-- buildspec.yaml      -> for CodeBuild
|-- main.tf             -> for Terraform
|-- variables.tf        -> for Terraform
|-- loadbalancing.tf    -> for Terraform
|-- computing.tf        -> for Terraform
|-- storage.tf          -> for Terraform
```

## Pre-Requisites

### Instance Security:

1. List all running instances in a specified region.
2. Check if instances are using the latest Amazon Machine Image (AMI).
3. Implement a function to update instances with outdated AMIs.
4. List all environments using instances tags (dev, prod, staging)

### Network Security:

5. List all security groups in a specified region.
6. Identify security groups with overly permissive inbound rules (allowing all traffic) and
   print their details.
7. Implement a function to update security groups to restrict overly permissive rules.

### 1, 2, 3:

...

### 4

In the terraform file `resource_group.tf` has been created. Resource groups can be easily used to enumerate resources based on attributes such as tags.

```shell
aws resource-groups list-group-resources --group-name dev_resource_group
```

### 5

### 6

### 7
