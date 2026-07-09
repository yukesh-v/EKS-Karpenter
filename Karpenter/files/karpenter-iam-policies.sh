#!/bin/bash

AWS_PARTITION="aws"

aws iam attach-role-policy --role-name "KarpenterNodeRole" \
    --policy-arn "arn:${AWS_PARTITION}:iam::aws:policy/AmazonEKSWorkerNodePolicy"

aws iam attach-role-policy --role-name "KarpenterNodeCNIRole" \
    --policy-arn "arn:${AWS_PARTITION}:iam::aws:policy/AmazonEKS_CNI_Policy"

aws iam attach-role-policy --role-name "KarpenterNodeEC2ContainerRegistryRole" \
    --policy-arn "arn:${AWS_PARTITION}:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"

aws iam attach-role-policy --role-name "KarpenterNodeSSMManagedInstanceRole" \
    --policy-arn "arn:${AWS_PARTITION}:iam::aws:policy/AmazonSSMManagedInstanceCore"
