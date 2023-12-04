#!/bin/bash

# Set your S3 bucket name
S3_BUCKET_NAME="mernserver"

# Set the local directory on the EC2 instance to store downloaded files
LOCAL_DIRECTORY="/home/ec2-user/my_app/"

# Make sure the local directory exists
mkdir -p "$LOCAL_DIRECTORY"

# Use the AWS CLI to sync the S3 bucket to the local directory
aws s3 sync "s3://$S3_BUCKET_NAME/" "$LOCAL_DIRECTORY/"
