import boto3  
  
# vars  
region_name = "eu-west-2"  
ec2 = boto3.client('ec2', region_name=region_name)  
  
def list_security_groups():  
    response = ec2.describe_security_groups()  
    return response['SecurityGroups']  
  
def is_overly_permissive(rule):  
    # Check if the rule allows all traffic
    return (rule.get('IpProtocol') == '-1' or rule.get('IpProtocol') == 'tcp' or rule.get('IpProtocol') == 'udp') and any(ip_range.get('CidrIp') == '0.0.0.0/0' for ip_range in rule.get('IpRanges', []))  
  
def find_overly_permissive_security_groups(security_groups):  
    permissive_groups = []  
    for sg in security_groups:  
        for permission in sg.get('IpPermissions', []):  
            if is_overly_permissive(permission):  
                permissive_groups.append(sg)  
                break  
    return permissive_groups  
  
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
            ec2.revoke_security_group_ingress(  
                GroupId=sg['GroupId'],  
                IpPermissions=[permission]  
            )  
            print(f"Deleted overly permissive rule from Security Group {sg['GroupId']}")  
  
def main():  
    print(f"Listing all security groups in region: {region_name}")  
    security_groups = list_security_groups()  
    print(f"Found {len(security_groups)} security groups.")  
      
    print("Identifying security groups with overly permissive inbound rules...")  
    permissive_groups = find_overly_permissive_security_groups(security_groups)  
      
    if permissive_groups:  
        print(f"Found {len(permissive_groups)} overly permissive security groups:")  
        print_security_group_details(permissive_groups)  
          
        for sg in permissive_groups:  
            delete_overly_permissive_rules(sg)  
    else:  
        print("No overly permissive security groups found.")  
  
if __name__ == "__main__":  
    main()  
