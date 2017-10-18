#!/bin/bash 
export PATH=$PATH:/usr/bin

# Exit script if error is returned.
# Exit if a pipeline results in an error.
set -e
set -o pipefail

# Get AWS instance vars 
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\" '{print $4}')
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep instanceId | awk -F\" '{print $4}')
MODE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=mode" --region=$REGION --output=text | cut -f5)
ROLE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=type" --region=$REGION --output=text | cut -f5)

# Update /etc/filebeat.yml global fields for this server 
[ ! -z "$ROLE" ] && sed -i -e "s/_role_/$ROLE/" /etc/filebeat/filebeat.yml || sed -i -e "s/_role_/unknown/" /etc/filebeat/filebeat.yml 
[ ! -z "$MODE" ] && sed -i -e "s/_env_/$MODE/" /etc/filebeat/filebeat.yml || sed -i -e "s/_env_/unknown/" /etc/filebeat/filebeat.yml  

# Enable filebeat service
/sbin/chkconfig filebeat on

# Start filebeat service
/etc/init.d/filebeat start