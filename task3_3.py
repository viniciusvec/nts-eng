import re
import boto3


ec2_client = boto3.client('ec2')

# Define the pattern to match AMIs
# example ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20240801
ami_name_pattern = r"ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-[\d\.]+"
ami_aws_filter = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"

response = ec2_client.describe_images(
    Filters=[
        {
            'Name': 'name',
            'Values': [ami_aws_filter]
        }
    ]
)

images = response['Images']
images_sorted = sorted(images, key=lambda x: x['CreationDate'], reverse=True)  # Sort images by creation date reversed

ami_variable_file = "ami_variable.tf"
with open(ami_variable_file, 'r') as file:
    current_ami = re.search(ami_name_pattern, file.read()).group(0)
    print(f"Current AMI: {current_ami}")

# Find the latest AMI that matches the pattern
latest_ami = None
for image in images_sorted:
    if re.match(ami_name_pattern, image['Name']):
        latest_ami = image['Name']
        break

if latest_ami is None:
    print("No matching AMI found.")


if  latest_ami != current_ami :
    ami_variable_file = "ami_variable.tf"

    # read the original file
    with open(ami_variable_file, 'r') as file:
        data = file.read()

    # replace the old AMI > new one
    new_data = re.sub(ami_name_pattern, latest_ami, data)

    # Write the updated content back to the file
    with open(ami_variable_file, 'w') as file:
        file.write(new_data)

    print(f"\nUpdated AMI to: {latest_ami}")
else:
    print("AMI is the latest version")
