#!/usr/bin/python
"""
Script to add/remove packages to s3 repository and notify repoupdate-daemon.
Usage:
    ./updatePackages.py -b 'mybucket' -p 'repopath' -o 'add' dir/*.rpm
    ./updatepackages.py -o 'remove' rpms/package.rpm rpms/anotherpackage.rpm
"""

import os
import sys
import optparse
import boto3

parser = optparse.OptionParser()
parser.add_option('-b', '--bucket', default='mybucket', help='''Default is \'mybucket\'''')
parser.add_option('-p', '--repopath', default='/centos6-x86_64/')
parser.add_option('-r', '--region', default='us-west-1')
parser.add_option('-o', '--operation', help='''\'add\' or \'remove\'''')
options, args = parser.parse_args()

s3_client = boto3.client('s3', region_name='us-west-1')

for rpmfile in args:
    filename = os.path.split(rpmfile)[1]
    key = os.path.join(options.repopath.lstrip('/'),filename)
    if options.operation == 'add':
        try:
            with open(rpmfile, 'rb') as data:
                s3_client.upload_fileobj(data, options.bucket, key)
                print("{0} uploaded to S3".format(rpmfile))
        except IOError as e:
            print("Uploading {0} to S3 from {1} failed due to I/O error({2}): {3}".
                          format(key, options.bucket, e.errno, e.strerror))
        except:
            print("Unexpected error uploading {0} to S3 from {1}: {2}".
                          format(key, options.bucket, (sys.exc_info()[0])))
    else:
        try:
            s3_client.delete_object(Bucket=options.bucket, Key=key)
            print ("{0} removed from S3".format(str(filename)))
        except:
            print ("Unable to delete {0} from s3 with the following error: {1}".
                   format(filename, sys.exc_info()[0]))
