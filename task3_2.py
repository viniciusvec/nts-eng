import sys
import boto3
import re

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


# To parse AMI name and use in the lookup for new images
def parse_ami_name(ami_name_string):
    # example: ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20240605.1
    static_name_pattern = r"(ubuntu/images/hvm-ssd-gp3/ubuntu-noble-[\d\.]+-amd64-server-)"
    version_pattern = r"ubuntu-noble-([\d\.])+"
    release_pattern = r"amd64-server-([\d\.]+)"

    static_name_match = re.match(static_name_pattern, ami_name_string)
    version_match = re.search(version_pattern, ami_name_string)
    release_match = re.search(release_pattern, ami_name_string)
    if static_name_match and version_match and release_match:
        static_name = static_name_match.group(1)
        version = version_match.group(1)
        release = release_match.group(1)
        return static_name, version, release
    return None, None

# To look up AMIs
def list_amis_by_static_name(static_name):
    response = ec2_client.describe_images(
        Filters=[
            {'Name': 'name', 'Values': [f"{static_name}*"]}
        ]
    )
    amis_info = []
    for image in response['Images']:
        amis_info.append({
            'ImageID': image['ImageId'],
            'Name': image['Name'],
            'CreationDate': image['CreationDate']
        })
    # Sort by CreationDate
    amis_info_sorted = sorted(amis_info, key=lambda x: x["CreationDate"])
    return amis_info_sorted

# To tag instances that has old AMIs 
def tag_instance_w_old_ami(ec2_instance):
    enriched_ec2_instance = ec2_instance
    if enriched_ec2_instance["ami_name"]:
        enriched_ec2_instance["ami_static_name"], enriched_ec2_instance["ami_version"], enriched_ec2_instance["ami_release"] = parse_ami_name(enriched_ec2_instance["ami_name"])
        if enriched_ec2_instance["ami_static_name"]:
            amis_info_sorted = list_amis_by_static_name(enriched_ec2_instance["ami_static_name"])
            if amis_info_sorted:
                latest_ami = amis_info_sorted[-1]  # Get the latest AMI based on creation date
                enriched_ec2_instance["latest_ami_available"] = {
                    "ImageID": latest_ami["ImageID"],
                    "Name": latest_ami["Name"],
                    "CreationDate": latest_ami["CreationDate"]
                }
                enriched_ec2_instance["is_ami_outdated"] = enriched_ec2_instance["ami_id"] != latest_ami["ImageID"]
            else:
                enriched_ec2_instance["latest_ami_available"] = None
                enriched_ec2_instance["is_ami_outdated"] = False
        else:
            enriched_ec2_instance["latest_ami_available"] = None
            enriched_ec2_instance["is_ami_outdated"] = False
    else:
        enriched_ec2_instance["latest_ami_available"] = None
        enriched_ec2_instance["is_ami_outdated"] = False
    return enriched_ec2_instance


if __name__ == "__main__":
    if len(sys.argv) < 2:  
        print("Please provide the region name as the first parameter.")  
        sys.exit(1)  

    region_name = sys.argv[1]  
    ec2_client = boto3.client('ec2', region_name=region_name)

    ec2_instances = list_ec2_instances()

    print(f"\nOutdated instaces:")
    for ec2_instance in ec2_instances:
        enriched_instance = tag_instance_w_old_ami(ec2_instance)

        if enriched_instance["is_ami_outdated"]:
            print(f"\n{enriched_instance}")
            # enabled for readable verbose outside json
            #print(f'\nInstance {enriched_instance["Name"]} has AMI on release {enriched_instance["ami_release"]} --> it can go to AMI {enriched_instance["latest_ami_available"]["Name"]}')
            latest_ami_id = enriched_instance["latest_ami_available"]["ImageID"]