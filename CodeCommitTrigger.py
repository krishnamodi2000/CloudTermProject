import boto3
import os
import mimetypes

def get_blob_list(codecommit, repository, branch, folder_path):
    response = codecommit.get_differences(
        repositoryName=repository,
        afterCommitSpecifier=branch,
    )
    blob_list = [difference['afterBlob'] for difference in response['differences'] if difference['afterBlob']['path'].startswith(folder_path)]
    while 'nextToken' in response:
        response = codecommit.get_differences(
            repositoryName=repository,
            afterCommitSpecifier=branch,
            nextToken=response['nextToken']
        )
        blob_list += [difference['afterBlob'] for difference in response['differences'] if difference['afterBlob']['path'].startswith(folder_path)]
    return blob_list

def make_s3_objects_public(s3_client, bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        objects = response.get('Contents', [])

        for obj in objects:
            object_key = obj['Key']
            s3_client.put_object_acl(Bucket=bucket_name, Key=object_key, ACL='public-read')
    except Exception as e:
        print(f"Error making S3 objects public: {e}")

def lambda_handler(event, context):
    # S3 buckets
    frontend_s3_bucket_name = os.environ['frontendS3BucketName']
    backend_s3_bucket_name = os.environ['backendS3BucketName']
    s3_client = boto3.client('s3')
    # Source CodeCommit
    codecommit = boto3.client('codecommit', region_name=os.environ['codecommitRegion'])
    repository_name = os.environ['repository']
    
    # Frontend folder path
    frontend_folder_path = 'client/build/'  # Replace with the desired frontend folder path
    
    # Backend folder path (exclude frontend folder)
    backend_folder_path = ''  # Replace with the desired backend folder path
    
    # Delete all existing objects in the frontend S3 bucket
    try:
        objects_to_delete = s3_client.list_objects_v2(Bucket=backend_s3_bucket_name)['Contents']
        if objects_to_delete:
            s3_client.delete_objects(
                Bucket=backend_s3_bucket_name,
                Delete={'Objects': [{'Key': obj['Key']} for obj in objects_to_delete]}
            )
    except Exception as e:
        print(f"Error deleting objects from S3 bucket: {e}")

    
    # Delete all existing objects in the backend S3 bucket
    try:
        objects_to_delete = s3_client.list_objects_v2(Bucket=frontend_s3_bucket_name)['Contents']
        if objects_to_delete:
            s3_client.delete_objects(
                Bucket=frontend_s3_bucket_name,
                Delete={'Objects': [{'Key': obj['Key']} for obj in objects_to_delete]}
            )
    except Exception as e:
        print(f"Error deleting objects from S3 bucket: {e}")

    
    # Read each file in the branch and upload it to the Frontend S3 bucket with creating a similar path structure
    for blob in get_blob_list(codecommit, repository_name, os.environ['branch'], frontend_folder_path):
        content = (codecommit.get_blob(repositoryName=repository_name, blobId=blob['blobId']))['content']
        
        # Remove the common path prefix
        relative_path = os.path.relpath(blob['path'], frontend_folder_path)
        
        # We have to guess the mime content-type of the files and provide it to S3 since S3 cannot do this on its own.
        content_type = mimetypes.guess_type(relative_path)[0]
        if content_type is not None:
            s3_client.put_object(Body=content, Bucket=frontend_s3_bucket_name, Key=relative_path, ContentType=content_type)
        else:
            s3_client.put_object(Body=content, Bucket=frontend_s3_bucket_name, Key=relative_path)
        make_s3_objects_public(s3_client, frontend_s3_bucket_name)
    print("Frontend S3 bucket updated successfully")

    
    # Read each file in the branch and upload it to the Backend S3 bucket with creating a similar path structure
    for blob in get_blob_list(codecommit, repository_name, os.environ['branch'], backend_folder_path):
        # Skip the frontend folder
        if blob['path'].startswith('client/'):
            continue
        
        content = (codecommit.get_blob(repositoryName=repository_name, blobId=blob['blobId']))['content']
        
        # Use the original path as the key
        key = blob['path']
        
        # We have to guess the mime content-type of the files and provide it to S3 since S3 cannot do this on its own.
        content_type = mimetypes.guess_type(key)[0]
        if content_type is not None:
            s3_client.put_object(Body=content, Bucket=backend_s3_bucket_name, Key=key, ContentType=content_type)
        else:
            s3_client.put_object(Body=content, Bucket=backend_s3_bucket_name, Key=key)
    
    print("Backend S3 bucket updated successfully")


