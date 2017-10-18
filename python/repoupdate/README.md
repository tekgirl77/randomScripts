# S3 YUM REPOUPDATER
--------------------
This daemon script can be used to keep an s3-hosted YUM repository updated
when new RPM packages are added or removed to the S3 bucket. It listens on 
the respective AWS SQS queue for S3 event messages that specify new packages 
published or removed from a YUM repo hosted on S3.

After waiting a while and grouping any additional messages, the script will
update the YUM repodata files to add or remove the packages as directed by the
'add' or 'remove' operation.

It is equivalent to using `createrepo` and an `s3cmd sync`.

Only a temporary copy of the repo metadata is needed locally, so there's no
need to keep a full clone of the repository and all of it's packages.

This is also very useful if packages are uploaded by many users or systems.
Running a `repoupdate-daemon` instance to monitor the SQS queue receiving
notification upon package(s) added to S3 and an instance to monitor the SQS queue
receiving notification upon package(s) removed from S3, will ensure packages
are added or removed respectively from the repository metadata, avoiding issues
with concurrent updates.

The addition/removal of new package(s) to s3 can be handled by whatever client is
used to build RPMs, e.g. a CI system like Jenkins or Buildbot.

## HOW-TO
---------
To add/remove package(s), use the `bin/updatePackages.py` helper script. Once package(s)
have been added/removed, S3 will send an event notification to an SQS queue to notify the daemon.
Usage Examples:
    ./bin/updatePackages.py -b 'mybucket' -p 'repopath' -o 'add' *.rpm
    ./bin/updatepackages.py -o 'remove' rpms/package.rpm rpms/anotherpackage.rpm

Once packages have been added or removed from s3://mybucket/centos6-x86_64/, S3 sends an
event notification to the respective SQS queue.

The daemon polls either the `your-repo_new-packages` or `your-repo_removed-packages` queues
as directed when the daemon is started.  Two instances of this daemon should be running at
all times to monitor both queues.  The default queue_check_interval is currently 60 seconds.
Once messages are retrieved from the queue, the daemon then downloads the repodata files locally,
updates, then uploads them back to S3.


The daemon uses standard boto configuation to access the AWS credentials: IAM
role, environment variables, or boto config file.

### Configure YUM Repo
----------------------
Create the following INI formatted file and save to /etc/yum.repos.d/your.repo:
```ini
[your-rpms]
name=Custom RPMS for YOUR_REPO - Centos 6
baseurl=http://mybucket.s3.amazonaws.com/centos6-x86_64
enabled=1
gpgcheck=0
```
Run the following commands to make sure YUM pulls in new packages:
```sh
yum clean all
yum makecache fast
```

### Run Daemon
--------------
The daemons are configured to run when the dev server is started.
    /usr/local/bin/repoupdate-daemon.py -q your-repo_new-packages -d
    /usr/local/bin/repoupdate-daemon.py -q your-repo_removed-packages -d

Verify daemon is running:
`ps aux | grep -i repoupdate`

### Test Add/Remove
-------------------
Run the `updatePackages` helper script:
```sh
./bin/updatePackages.py -b mybucket -o 'add' local/dir/some*.rpm
```

If you have access to log onto the AWS S3 console, you can refresh the
`mybucket/centos6-x86_64` bucket path to see your packages added/removed.
You can refresh the `mybucket/centos6-x86_64/repodata` directory to view
the date/time the XML metadata files are updated once the daemon is done
processing and pushes it back up to S3.

Run the following commands to update YUM and verify you see the `mybucket` repo
and packages listed:
```sh
yum clean all
yum makecache fast
yum repolist
yum list | grep -i your_repo
yum search <package_added_or_removed>
```


