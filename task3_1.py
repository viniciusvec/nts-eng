import sys
import boto3

# To get Name and other tags
def get_value_from_tags(key, tags):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return None

# To get AMI name from ID
def get_ami_name(ami_id):
    response = ec2_client.describe_images(
        ImageIds=[ami_id]
    )
    if response['Images']:
        return response['Images'][0]['Name']
    return None

# To gather ec2 data
def describe_instace(instance):
    instance_info = {
        'InstanceID': instance['InstanceId'],
        'InstanceType': instance['InstanceType'],
        'Name': get_value_from_tags('Name', instance.get('Tags', [])),
        'ami_id': instance['ImageId'],
        'Env': get_value_from_tags('Env', instance.get('Tags', [])),
        'ami_name': get_ami_name(instance['ImageId'])
    }
    return instance_info

# To loop through ec2 instances
def list_ec2_instances():
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    instances_info = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_info = describe_instace(instance)
            instances_info.append(instance_info)
    return instances_info

if __name__ == "__main__":
    if len(sys.argv) < 2:  
        print("Please provide the region name as the first parameter.")  
        sys.exit(1)  

    region_name = sys.argv[1]  
    ec2_client = boto3.client('ec2', region_name=region_name)

    ec2_instances = list_ec2_instances()
    print(f"\nInstances:\n")
    for ec2_instance in ec2_instances:
        print(ec2_instance)