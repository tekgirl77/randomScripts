# Sync objects from source S3 bucket to destination S3 bucket
# Author: Salle J. Ingle
# Date: 08.02.2018

import boto3
from botocore.client import Config

def lambda_handler(event, context):
    s3_client = boto3.client('s3', 'us-east-1', config=Config(s3={'addressing_style': 'path'}))
    source = 'source.bucket.name'
    dest = 'dest.bucket.name'

    def sync_s3_to_s3(source, dest):
        s3 = s3_client.resource('s3')
        dest_obj = []
        dest_bucket = s3.Bucket(dest)
        for obj in dest_bucket.objects.all():
            dest_obj.append(obj.key)

        src_bucket = s3.Bucket(source)
        for src_obj in src_bucket.objects.all():
            if src_obj.key not in dest_obj:
                print "Copying {0} to {1}".format(src_obj.key, dest)
                dest_key = src_obj.key
                copy_source = dict(Bucket=str(source), Key=str(src_obj.key))
                s3.meta.client.copy(copy_source, dest, dest_key)

    sync_s3_to_s3(source, dest)
