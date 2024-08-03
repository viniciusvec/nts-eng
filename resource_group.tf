

resource "aws_resourcegroups_group" "resourcegroup" {
  name = "dev_resource_group"

  resource_query {
    query = <<JSON
{
  "ResourceTypeFilters": [
    "AWS::EC2::Instance"
  ],
  "TagFilters": [
    {
      "Key": "Env",
      "Values": ["dev"]
    }
  ]
}
JSON
  }
}
