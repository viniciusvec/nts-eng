import sys
import boto3  
    
def list_security_groups():  
    response = ec2_client.describe_security_groups()  
    return response['SecurityGroups']  
  
def is_overly_permissive(rule):  
    # Check if the rule allows all traffic
    return (rule.get('IpProtocol') == '-1' or rule.get('IpProtocol') == 'tcp' or rule.get('IpProtocol') == 'udp') and any(ip_range.get('CidrIp') == '0.0.0.0/0' for ip_range in rule.get('IpRanges', []))  
  
  
def print_security_group_details(security_groups):  
    for sg in security_groups:  
        print(f"Security Group ID: {sg['GroupId']}")  
        print(f"Security Group Name: {sg['GroupName']}")  
        print(f"Description: {sg['Description']}")  
        print("Inbound Rules:")  
        for permission in sg.get('IpPermissions', []):  
            print(permission)  
        print("-" * 30)  
  
def delete_overly_permissive_rules(sg):  
    for permission in sg.get('IpPermissions', []):  
        if is_overly_permissive(permission):  
            ec2_client.revoke_security_group_ingress(  
                GroupId=sg['GroupId'],  
                IpPermissions=[permission]  
            )  
            print(f"Deleted overly permissive rule from Security Group {sg['GroupId']}")  
  
if __name__ == "__main__":

    if len(sys.argv) < 2:  
        print("Please provide the region name as the first parameter.")  
        sys.exit(1)  

    region_name = sys.argv[1]  
    ec2_client = boto3.client('ec2', region_name=region_name)
    
    print(f"Listing all security groups in region: {region_name}")  
    security_groups = list_security_groups()  
    print(f"Found {len(security_groups)} security groups.")        

    print_security_group_details(security_groups)  
