import sys
import boto3
from botocore.exceptions import ClientError

def check_eks_status(cluster_name, region):
    client = boto3.client('eks', region_name=region)
    try:
        response = client.describe_cluster(name=cluster_name)
        status = response['cluster']['status']
        print(f"Cluster Status: {status}")
        if status != 'ACTIVE':
            print(f"Error: Cluster {cluster_name} is not ACTIVE.")
            sys.exit(1)
    except ClientError as e:
        print(f"AWS Error: {e.response['Error']['Message']}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: verify_cluster.py <cluster_name> <region>")
        sys.exit(1)
    check_eks_status(sys.argv[1], sys.argv[2])