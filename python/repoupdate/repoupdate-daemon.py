#!/usr/bin/python
"""

Daemon for serializing metadata updates on an s3-hosted yum repository.

Listens on AWS SQS for S3 event messages that specify new packages published
or removed from a YUM repo hosted on s3.
After waiting a while and grouping any additional messages, this script will
update the yum repodata to add or remove the packages as directed by the
'add' or 'remove' operation.

Updated and adapted by Salle J. Ingle
Based on the original found here:
https://github.com/wonderpl/s3yum-updater

"""

import os
import sys
import time
import json
import urlparse
import tempfile
import shutil
import optparse
import logging
import collections
import yum
import createrepo
import boto3
import botocore
from rpmUtils.miscutils import splitFilename

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LoggerCallback(object):
    def errorlog(self, message):
        logging.error(message)
    def log(self, message):
        message = message.strip()
        if message:
            logging.debug(message)


class S3Grabber(object):
    def __init__(self, baseurl):
        self.base = urlparse.urlsplit(baseurl)
        self.baseurl = baseurl
        self.s3_resource = boto3.resource('s3')
        self.s3_client = boto3.client('s3', region_name='us-west-1')
        self.bucket = self.s3_resource.Bucket(self.base.netloc)
        # Verify connectivity to bucket
        try:
            self.s3_resource.meta.client.head_bucket(Bucket=self.bucket.name)
        except botocore.exceptions.ClientError as e:
            # If it was a 404 error, then the bucket does not exist.
            error_code = int(e.response['Error']['Code'])
            logging.error(error_code)

    def _getkey(self, url):
        if url.startswith(self.baseurl):
            url = url[len(self.baseurl):].lstrip('/')
        url = (self.base.path.lstrip('/')) + url
        for key in self.bucket.objects.all():
            if url == key.key:
                return key

    def urlgrab(self, url, filename, **kwargs):
        key = self._getkey(url)
        if not key:
            raise createrepo.grabber.URLGrabError(14, '%s not found' % url)
        logging.debug('Downloading: {0}'.format(key.key))
        try:
            with open(str(filename), 'wb') as data:
                self.s3_client.download_fileobj(self.bucket.name, key.key, data)
        except IOError as e:
            logging.error("Downloading {0} from {1} failed due to I/O error({2}): {3}".
                format(key, self.bucket.name, e.errno, e.strerror))
        except:
            logging.error("Unexpected error downloading {0} from {1}: {2}".
                          format(key, self.bucket.name, (sys.exc_info()[0])))
        return filename

    def syncdir(self, dir):
        # Remove old repodata files and upload updated tmpdir/repodata files to S3
        prefix = os.path.join(self.base.path.lstrip('/'), 'repodata')
        existing_keys = []
        for key in self.bucket.objects.filter(Prefix=prefix):
            existing_keys.append(key.key)
        print "existing_keys {0}".format(str(existing_keys))
        new_keys = []
        for file in sorted(os.listdir(dir)):
            key = os.path.join(prefix, file)
            filename = os.path.join(dir,file)
            try:
                with open(filename, 'rb') as data:
                    self.s3_client.upload_fileobj(data, self.bucket.name, key)
                    logging.debug("Successfully uploaded to S3: {0}".format(key))
                    success = True
            except IOError as e:
                logging.error("Uploading {0} to S3 from {1} failed due to I/O error({2}): {3}".
                              format(key, self.bucket.name, e.errno, e.strerror))
            except:
                logging.error("Unexpected error uploading {0} to S3 from {1}: {2}".
                              format(key, self.bucket.name, (sys.exc_info()[0])))
            new_keys.append(key)
        if success:
            for key in existing_keys:
                if key not in new_keys:
                    try:
                        self.s3_client.delete_object(Bucket=self.bucket.name, Key=key)
                        logging.debug('Successfully deleted old key from S3: {0}'.format(str(key)))
                    except:
                        logging.error("Unexpected error deleting {0} from {1}: {2}".
                                      format(key, self.bucket.name, (sys.exc_info()[0])))
        else:
            logging.critical("Did not remove existing repodata from S3 since we were "
                             "unable to upload the updated repodata. Run in '-v' "
                             "verbose mode and see logfile for debug info.")


def update_repodata(operation, repopath, rpmfiles, options):
    tmpdir = tempfile.mkdtemp()
    s3base = urlparse.urlunsplit(('https', options.bucket, repopath, '', ''))
    s3grabber = S3Grabber(s3base)

    # Set up temporary YUM repo that will fetch repodata from s3
    yumbase = yum.YumBase()
    yumbase.preconf.disabled_plugins = '*'
    yumbase.conf.cachedir = os.path.join(tmpdir, 'cache')
    yumbase.repos.disableRepo('*')
    repo = yumbase.add_enable_repo('s3')
    repo._grab = s3grabber
    repo._urls = [os.path.join(s3base, '')]
    # Ensure that missing base path doesn't cause trouble
    repo._sack = yum.sqlitesack.YumSqlitePackageSack(
        createrepo.readMetadata.CreaterepoPkgOld)

    # Create metadata generator
    mdconf = createrepo.MetaDataConfig()
    mdconf.directory = tmpdir
    mdconf.pkglist = yum.packageSack.MetaSack()
    mdgen = createrepo.MetaDataGenerator(mdconf, LoggerCallback())
    mdgen.tempdir = tmpdir
    mdgen._grabber = s3grabber

    # Combine old package sack with updated RPM file list
    new_packages = yum.packageSack.PackageSack()
    for rpmfile in rpmfiles:
        filename = rpmfile[rpmfile.rfind("/") + 1:]
        #print 'filename - {0}'.format(filename)
        (name, version, release, epoch, arch) = splitFilename(filename)
        if operation == "add":
            # Combine existing package sack with new rpm file list
            newpkg = mdgen.read_in_package(os.path.join(s3base, filename))
            newpkg._baseurl = ''  # don't leave s3 base urls in primary metadata
            new_packages.addPackage(newpkg)
            logger.debug("Successfully added package to yum.packageSack: {0}".format(filename))
        else:
            # Remove deleted package
            old_versions = yumbase.pkgSack.searchNevra(name=name)
            print "old_versions - {0}".format(str(old_versions))
            if old_versions:
                for i, older in enumerate(old_versions, 1):
                    # Remove package from yumbase.pkgSack
                    if older.version == version and older.release == release:
                        yumbase.pkgSack.delPackage(older)
                        logger.info("Successfully deleted package from yumbase.pkgSack: {0}".format(filename))
            else:
                logging.error('Unable to find {0} in yumbase.pkgSack.'.format(str(filename)))
    mdconf.pkglist.addSack('existing', yumbase.pkgSack)
    mdconf.pkglist.addSack('new', new_packages)

    # Write out new metadata to tmpdir
    mdgen.doPkgMetadata()
    mdgen.doRepoMetadata()
    mdgen.doFinalMove()

    # Replace metadata on S3
    s3grabber.syncdir(os.path.join(tmpdir, 'repodata'))
    # Clean up tmpdir
    shutil.rmtree(tmpdir)


def main(options):
    loglevel = ('WARNING', 'INFO', 'DEBUG')[min(2, options.verbose)]
    logging.basicConfig(
        filename=options.logfile,
        level=logging.getLevelName(loglevel),
        format='%(asctime)s %(levelname)s %(message)s',
    )
    # Determine operation
    if options.sqs_name == 'your-repo_new-packages':
        operation = 'add'
    elif options.sqs_name == 'your-repo_removed-packages':
        operation = 'remove'
    else:
        sys.exit("Make sure you have passed either 'your-repo_new-packages' or "
                     "'your-repo_removed-packages' as the queue name.")
    # Connect to SQS queue
    try:
        sqs_client = boto3.client('sqs', region_name='us-west-1')
        queue = sqs_client.get_queue_url(QueueName=options.sqs_name)
        queue_url = queue['QueueUrl']
        logging.debug("queue {0}".format(queue))
    except:
        logging.critical("Unable to connect to {0} queue with the following error: {1}".
                      format(options.sqs_name, sys.exc_info()[0]))
    messages = []
    visibility_timeout = ((options.process_delay_count + 2) *
                          options.queue_check_interval)
    logging.debug("SQS visibility_timeout: {0}".format(visibility_timeout))

    while True:
        messages = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, VisibilityTimeout=visibility_timeout)
        logging.debug("Checking for new_messages: {0}...".format(messages))
        if messages:
            if "Messages" in messages.keys():
                logging.info("Processing new messages from queue: {0}".format(str(options.sqs_name)))
                # Store messages so we can delete from the queue after processing
                message_handles = []
                pkgmap = collections.defaultdict(list)
                for message in messages['Messages']:
                    message_handles.append(message['ReceiptHandle'])
                    json_message = json.loads(message['Body'])
                    record = json_message['Records'][0]
                    s3Elem = record['s3']
                    bucketName = s3Elem['bucket']['name']
                    key = s3Elem['object']['key']
                    filename = key[key.rfind("/") + 1:]
                    repopath = options.repopath
                    pkgmap[repopath].append(str(filename))
                    logger.info("Added message to pkgmap for processing: {0}/{1}".format(bucketName, key))

                for repopath, rpmfiles in pkgmap.items():
                    logging.info('Processing {0}...'.format(rpmfiles))
                    try:
                        update_repodata(operation, repopath, set(rpmfiles), options)
                    except:
                        logging.exception('Update failed for: {0}'.format(rpmfiles))
                # Reset messages:
                for handle in message_handles:
                    try:
                        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=handle)
                    except:
                        logging.error("Unable to delete message with handle {0} with error: {1}".
                                      format(handle,sys.exc_info()[0]))
                logging.debug("Done processing; resetting messages.")
                messages = []
            else:
                messages = []
        logging.debug("Sleeping {0}...".format(options.queue_check_interval))
        try:
            time.sleep(options.queue_check_interval)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-b', '--bucket', default='mybucket',
                      help='''Default is \'mybucket\'.''')
    parser.add_option('-p', '--repopath', default='/centos6-x86_64/',
                      help='''Default is \'centos6-x86_64\'.''')
    parser.add_option('-r', '--region', default='us-west-1',
                      help='''Default is \'us-west-1\'.''')
    parser.add_option('-q', '--sqs-name',
                      help='''Required: Specify either \'your-repo_new-packages\' 
                      or \'your-repo_removed-packages\'''')
    parser.add_option('-v', '--verbose', action='count', default=0)
    parser.add_option('-l', '--logfile', default='/var/log/repoupdate.log',
                      help='''Default is \'/var/log/repoupdate.log\'.''')
    parser.add_option('-d', '--daemon', action='store_true')
    parser.add_option('--queue-check-interval', type='int', default=60,
                      help='''Default is 60 seconds.''')
    parser.add_option('--process-delay-count', type='int', default=2,
                      help='''Default is 2.''')
    options, args = parser.parse_args()

    if not options.sqs_name:
        parser.error("Must specify SQS queue name with '-q' option. "
                     "See 'repoupdate-daemon.py -h' for options.")
    if args:
        parser.error("Add/Remove packages using the updatePackages.py helper script. "
                     "This daemon will update the S3 repodata accordingly.")
    try:
        fh = logging.FileHandler(options.logfile)
        logger.addHandler(fh)
    except:
        logging.error("Unable to create logging.FileHandler at {0} with error: {1}.\n"
                      "\nVerify access to the logging location and try starting daemon again.\n"
                      "Run 'repoupdate-daemon.py -h' to view available options.\n".
                      format(options.logfile, sys.exc_info()[0]))
        sys.exit(1)
    if options.daemon:
        import daemon
        with daemon.DaemonContext(files_preserve=[ fh.stream, ]) as context:
            try:
                main(options)
            except Exception, e:
                import traceback
                exc = sys.exc_info()
                logger.debug("".join(traceback.format_exception(exc[0], exc[1], exc[2])))
                sys.exit(1)
    else:
        main(options)