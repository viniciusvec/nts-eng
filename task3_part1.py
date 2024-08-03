import boto3
import re

# Initialize the EC2 client
ec2_client = boto3.client('ec2')
gold_image_name = 'gold_image'

# To get Name and other tags
def get_value_from_tags(key, tags):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return None


# To gather ec2 data
def describe_instace(instance):
    instance_info = {
        'InstanceID': instance['InstanceId'],
        'InstanceType': instance['InstanceType'],
        'Name': get_value_from_tags('Name', instance.get('Tags', [])),
        'ami_id': instance['ImageId'],
        'Env': get_value_from_tags('Env', instance.get('Tags', []))
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

# To get AMI name from ID
def get_ami_name(ami_id):
    response = ec2_client.describe_images(
        ImageIds=[ami_id]
    )
    if response['Images']:
        return response['Images'][0]['Name']
    return None

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
    enriched_ec2_instance["ami_name"] = get_ami_name(ec2_instance["ami_id"])
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

# lookup volume ID for gold image
def get_gold_image_vol_id():
    instances = ec2_client.describe_instances(  
        Filters=[{'Name': 'tag:Name', 'Values': [gold_image_name]},{'Name': 'instance-state-name', 'Values': ['running']}]  
    )  
    
    instance_id = instances['Reservations'][0]['Instances'][0]['InstanceId']  
    
    # Retrieve the volume ID associated with the instance  
    volumes = ec2_client.describe_volumes(  
        Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}]  
    )  
    
    return volumes['Volumes'][0]['VolumeId']


# Update AMI
def update_instance_ami(instance_id, new_ami_id):
    print(f'Updating instance {instance_id} to use AMI {new_ami_id}')

    # Stop the instance
    ec2_client.stop_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])

    # Get the root volume ID
    instance_description = ec2_client.describe_instances(InstanceIds=[instance_id])
    root_device_name = instance_description['Reservations'][0]['Instances'][0]['RootDeviceName']
    root_volume_id = None
    for block_device in instance_description['Reservations'][0]['Instances'][0]['BlockDeviceMappings']:
        if block_device['DeviceName'] == root_device_name:
            root_volume_id = block_device['Ebs']['VolumeId']
            break

    if not root_volume_id:
        raise Exception("Root volume not found")

    print(f"\nCurrent volume: {root_volume_id}")


    # Create a snapshot of the gold volume
    print(f"\nCreate a snapshot of the GOLD volume")
    snapshot_response = ec2_client.create_snapshot(VolumeId=get_gold_image_vol_id(), Description="gold_snapshot")
    snapshot_id = snapshot_response['SnapshotId']
    
    print(f"snapshot_id : {snapshot_id}")


    # Wait for the snapshot to complete
    print(f" .. Wait for the snapshot to complete")
    waiter = ec2_client.get_waiter('snapshot_completed')
    waiter.wait(SnapshotIds=[snapshot_id])

    # Create a new volume from the snapshot
    print(f"\nCreate a new volume from the snapshot")
    availability_zone = instance_description['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    new_volume_response = ec2_client.create_volume(SnapshotId=snapshot_id, AvailabilityZone=availability_zone)
    new_volume_id = new_volume_response['VolumeId']
    
    print(f"\nNew volume: {new_volume_id}")
    
    #print(f"new_volume_id: ", new_volume_id)

    # Wait for the new volume to become available
    print(f" .. Wait for the new volume to become available")
    waiter = ec2_client.get_waiter('volume_available')
    waiter.wait(VolumeIds=[new_volume_id])

    # Detach the old root volume
    print(f"\nDetach the old root volume")
    ec2_client.detach_volume(VolumeId=root_volume_id, InstanceId=instance_id, Device=root_device_name)
    waiter = ec2_client.get_waiter('volume_available')
    waiter.wait(VolumeIds=[root_volume_id])
    #print(f"old vol:", VolumeIds=[root_volume_id])


    # Attach the new volume
    print(f"\nAttach the new volume")
    ec2_client.attach_volume(VolumeId=new_volume_id, InstanceId=instance_id, Device=root_device_name)
    waiter = ec2_client.get_waiter('volume_in_use')
    waiter.wait(VolumeIds=[new_volume_id])
    #print(f"new vol:", VolumeIds=[new_volume_id])

    # Start the instance
    print(f"\nStart the instance")
    ec2_client.start_instances(InstanceIds=[instance_id])
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

    # Delete the snapshot and old volume
    print(f"\nDelete the snapshot and old volume")
    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
    ec2_client.delete_volume(VolumeId=root_volume_id)

    #print(f'Instance {instance_id} updated to use AMI {new_ami_id}')

if __name__ == "__main__":
    ec2_instances = list_ec2_instances()
    for ec2_instance in ec2_instances:
        enriched_instance = tag_instance_w_old_ami(ec2_instance)
        print(f"\n{enriched_instance}")

        if enriched_instance["is_ami_outdated"] and enriched_instance["Name"] != "gold_image":
            print(f'\nInstance {enriched_instance["Name"]} has AMI on release {enriched_instance["ami_release"]} --> it can go to AMI {enriched_instance["latest_ami_available"]["Name"]}')
            user_input = input(f"\nPress 'y' to continue: ").strip().lower()  
            if user_input == 'y':  
                latest_ami_id = enriched_instance["latest_ami_available"]["ImageID"]
                update_instance_ami(enriched_instance["InstanceID"], latest_ami_id)
                print(f"\n\n\n\t--Updated:\n")
                print(enriched_instance)
            else:  
                break
