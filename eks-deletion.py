import argparse
import sys
import time
import boto3
from botocore.exceptions import ClientError


def delete_cluster(stack_name, region):
    cfn = boto3.client("cloudformation", region_name=region)

    # Track seen events to avoid duplicate print lines
    seen_event_ids = set()

    print(f"Initiating deletion for stack: {stack_name}...")

    try:
        # Trigger the CloudFormation Stack Deletion
        cfn.delete_stack(StackName=stack_name)
    except ClientError as e:
        print(f"Failed to initiate stack deletion: {e}")
        sys.exit(1)

    # Monitoring loop
    while True:
        try:
            response = cfn.describe_stacks(StackName=stack_name)
            stack_status = response["Stacks"][0]["StackStatus"]

            # Fetch recent events for specific resource tracking
            events_response = cfn.describe_stack_events(StackName=stack_name)
            events = events_response["StackEvents"]

            # Process events from oldest to newest in the current batch
            for event in reversed(events):
                event_id = event["EventId"]
                if event_id in seen_event_ids:
                    continue

                logical_id = event.get("LogicalResourceId", "")
                resource_type = event.get("ResourceType", "")
                status = event.get("ResourceStatus", "")

                # 1. Track Addons Detachment/Deletion
                if "AWS::EKS::Addon" in resource_type:
                    if status == "DELETE_IN_PROGRESS":
                        print(
                            f"Addon is being detached/deleted from cluster...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "DELETE_COMPLETE":
                        print(
                            f"\nAddon detached and removed successfully!"
                        )

                # 2. Track NodeGroup Deletion
                elif "AWS::EKS::Nodegroup" in resource_type:
                    if status == "DELETE_IN_PROGRESS":
                        print(
                            f"Nodegroup is being deleted...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "DELETE_COMPLETE":
                        print(
                            f"\nNodegroup successfully deleted!"
                        )

                # 3. Track Cluster Deletion
                elif "AWS::EKS::Cluster" in resource_type:
                    if status == "DELETE_IN_PROGRESS":
                        print(
                            f"Cluster is being deleted...",
                            end="\r",
                            flush=True,
                        )
                    elif status == "DELETE_COMPLETE":
                        print(
                            f"\nCluster successfully deleted!"
                        )

                seen_event_ids.add(event_id)

            # Break if the stack reaches a final failure status during teardown
            if stack_status in [
                "DELETE_FAILED",
                "ROLLBACK_IN_PROGRESS",
                "ROLLBACK_COMPLETE",
            ]:
                print(f"\nFinal Stack Status: {stack_status}")
                break

        except ClientError as e:
            # When a stack is completely deleted, describe_stacks throws a ValidationError.
            # This means the deletion is 100% finished.
            if "ValidationError" in str(e) or "does not exist" in str(e):
                print(
                    f"\nFinal Stack Status: DELETE_COMPLETE (Stack successfully removed)"
                )
                break
            # Ignore other temporary network/throttling issues
            pass

        time.sleep(5)  # Poll every 5 seconds


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack_name", required=True)
    parser.add_argument("--region", required=True)

    args = parser.parse_args()

    delete_cluster(stack_name=args.stack_name, region=args.region)