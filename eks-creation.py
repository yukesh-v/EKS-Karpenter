import argparse
import sys
import time
import boto3
from botocore.exceptions import ClientError  


def create_cluster(
    stack_name,
    region,
    subnet_ids,
    cluster_version,
    security_group,
    instance_types,
):
    cfn = boto3.client("cloudformation", region_name=region)

    with open("EKS-Creation.yaml", "r") as f:
        template_body = f.read()
    seen_event_ids = set() 

    try:
        response = cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=[
                {"ParameterKey": "ClusterName", "ParameterValue": stack_name},
                {"ParameterKey": "SubnetIds", "ParameterValue": subnet_ids},
                {
                    "ParameterKey": "ClusterVersion",
                    "ParameterValue": cluster_version,
                },
                {
                    "ParameterKey": "SecurityGroup",
                    "ParameterValue": security_group,
                },
                {
                    "ParameterKey": "InstanceTypes",
                    "ParameterValue": instance_types,
                },
            ],
            Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        )
    except ClientError as e:
        print(f"Failed to initiate stack creation: {e}")
        sys.exit(1)

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

                logical_id = event.get("LogicalResourceId", "")
                resource_type = event.get("ResourceType", "")
                status = event.get("ResourceStatus", "")

                if "AWS::EKS::Cluster" in resource_type:
                    if status == "CREATE_IN_PROGRESS":
                        print(
                            f"{stack_name} is being creating...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "CREATE_COMPLETE":
                        print(
                            f"\n{stack_name} successfully created!"
                        )

                elif "AWS::EKS::Nodegroup" in resource_type:
                    if status == "CREATE_IN_PROGRESS":
                        print(
                            f"{stack_name} NodeGroup is being creating...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "CREATE_COMPLETE":
                        print(
                            f"\nNodegroup successfully created!"
                        )

                elif "AWS::EKS::Addon" in resource_type:
                    if status == "CREATE_IN_PROGRESS":
                        print(
                            f"{stack_name} Addon is being attaching to cluster...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "CREATE_COMPLETE":
                        print(
                            f"\nAddon attached successfully!"
                        )

                seen_event_ids.add(event_id)

            if stack_status in [
                "CREATE_COMPLETE",
                "ROLLBACK_IN_PROGRESS",
                "ROLLBACK_COMPLETE",
                "CREATE_FAILED",
            ]:
                print(f"\nFinal Stack Status: {stack_status}")
                break

        except ClientError:
            pass
        time.sleep(10)  


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack_name", required=True)
    parser.add_argument("--cluster_name", required=True)
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