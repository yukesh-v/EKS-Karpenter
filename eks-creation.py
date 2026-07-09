import argparse
import sys
import time
import boto3
from botocore.exceptions import ClientError  

def create_cluster(stack_name, region, subnet_ids, cluster_version, security_group, instance_types):
    cfn = boto3.client("cloudformation", region_name=region)

    try:
        with open("EKS-Creation.yaml", "r") as f:
            template_body = f.read()
    except FileNotFoundError:
        print("Error: EKS-Creation.yaml template file not found.")
        sys.exit(1)

    seen_event_ids = set() 

    try:
        cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {"ParameterKey": "ClusterName", "ParameterValue": stack_name},
                {"ParameterKey": "SubnetIds", "ParameterValue": subnet_ids},
                {"ParameterKey": "ClusterVersion", "ParameterValue": cluster_version},
                {"ParameterKey": "SecurityGroup", "ParameterValue": security_group},
                {"ParameterKey": "InstanceTypes", "ParameterValue": instance_types},
            ],
            Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        )
    except ClientError as e:
        print(f"Failed to initiate stack creation: {e}")
        sys.exit(1)

    print(f"Stack creation initiated for {stack_name}...")

    while True:
        try:
            response = cfn.describe_stacks(StackName=stack_name)
            stack_status = response["Stacks"][0]["StackStatus"]

            events_response = cfn.describe_stack_events(StackName=stack_name)
            events = events_response["StackEvents"]

            for event in reversed(events):
                event_id = event["EventId"]
                if event_id in seen_event_ids:
                    continue

                resource_type = event.get("ResourceType", "")
                status = event.get("ResourceStatus", "")
                reason = event.get("ResourceStatusReason", "")

                # Clean log reporting tracking resource groups
                if status in ["CREATE_IN_PROGRESS", "CREATE_COMPLETE", "CREATE_FAILED"]:
                    print(f"[{resource_type}] -> Status: {status} | Reason: {reason}")

                seen_event_ids.add(event_id)

            if stack_status in ["CREATE_COMPLETE", "ROLLBACK_IN_PROGRESS", "ROLLBACK_COMPLETE", "CREATE_FAILED"]:
                print(f"\nFinal Stack Status Summary: {stack_status}")
                if stack_status != "CREATE_COMPLETE":
                    sys.exit(1) # Fail the Jenkins build step if CFN fails!
                break

        except ClientError as e:
            # Handle infrastructure API drops cleanly without locking up
            print(f"\n[AWS API Warning]: {e}")
            
        time.sleep(15)  

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack_name", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--subnet-ids", required=True)
    parser.add_argument("--security-group", required=True)
    parser.add_argument("--cluster_version", default="1.35")
    parser.add_argument("--instance_types", required=True)

    args = parser.parse_args()

    create_cluster(
        stack_name=args.stack_name,
        region=args.region,
        subnet_ids=args.subnet_ids,
        cluster_version=args.cluster_version,
        security_group=args.security_group,
        instance_types=args.instance_types,
    )
