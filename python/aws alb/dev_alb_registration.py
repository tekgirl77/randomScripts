#!/usr/bin/env python

import boto3
import sys
from time import sleep
import argparse
import core.config

# Define static global variables
alb_client = boto3.client('elbv2', region_name='us-west-1')
config = core.config.Config()
http_listener = 'insert alb arn'
https_listener = 'insert alb arn'
target_id = 'insert ec2 id for target dev server(s)'
vpc_id = 'insert vpc id'


# Check for existing http/s rule
def check_rule(rules):
    new_rule = True
    for rule in rules['Rules']:
        for value in rule['Conditions']:
            if value['Values'][0] == dev_url:
                new_rule = False
                return new_rule, rule
    return new_rule


# Create new http/s rule
def create_rule(name, rules, listener, conditions, actions):
    # Set new rule priority
    priority = set_priority(rules)
    # Create new rule
    alb_client.create_rule(ListenerArn=listener, Conditions=conditions, Priority=priority, Actions=actions)
    # Validate new rule was created successfully
    updated_rules = alb_client.describe_rules(ListenerArn=listener)
    validate_rule = check_rule(updated_rules)
    if validate_rule[0] is False:
        if args.verbose: print("Validated new {0} rule {1} was created successfully.\n".format(str(name), str(dev_url)))
    else:
        if args.verbose: print('Something went wrong and your new {0} rule {1} was not created. \nPlease verify '
                               'connectivity, investigate, and try again.\n'.format(str(name), str(dev_url)))


# Set priority for new http/https rule
# Note: AWS rules numbering in the web UI can be misleading. If a rule is deleted, for example, the priority of existing
# rules remains static and does not update per the consecutive numbering scheme shown in AWS gui.
# Therefore, we will set the new rule priority based on the last rule priority n + 1.
def set_priority(rules):
    priority_idx = 0
    for priority in rules['Rules']:
        if priority['Priority'].lower() != 'default':
            priority_idx = int((priority['Priority']))
            if args.verbose: print('Priority_idx: {0}.\n'.format(str(priority_idx)))
        else:
            priority_idx = int(priority_idx) + 1
            if args.verbose: print('Setting new rule priority to: {0}\n'.format(str(priority_idx)))
            break
    return int(priority_idx)


# Validate new target group was created successfully
def validate_target_creation(target_group_arn):
    target_group_exists = False
    check_count = 6
    while target_group_exists is False:
        if check_count == 0:
            print('New target group creation failed. Please investigate and try again!\n')
            sys.exit(1)
        target_group_list = alb_client.describe_target_groups()
        for target_group in target_group_list['TargetGroups']:
            if target_group['TargetGroupArn'] == target_group_arn:
                target_group_exists = True
                if args.verbose: print('New target group was created successfully.\n')
                break
        if target_group_exists is not True:
            check_count -= 1
            if check_count != 0:
                if args.verbose: print('Did not find new target group yet. Checking up to {0} more times...\n'.
                                       format(str(check_count)))
            sleep(5)


# Validate target group state is healthy once it is attached to an ALB listener
def validate_target_health(target_group_arn):
    target_health = 'unknown'
    check_count = 12
    while target_health != 'healthy':
        target_health = alb_client.describe_target_health(TargetGroupArn=target_group_arn, Targets=targets)[
            'TargetHealthDescriptions'][0]['TargetHealth']['State']
        if check_count == 0:
            if args.verbose: print('Registered target is still in {0} state.  Please investigate!\n'.
                                   format(str(target_health)))
            sys.exit(1)
        elif target_health != 'healthy':
            check_count -= 1
            if check_count != 0:
                if args.verbose: print('TargetHealth is currently {0}. Checking {1} more times for healthy status... '
                                       '\n'.format(str(target_health), str(check_count)))
            sleep(5)
        elif target_health == 'healthy':
            if args.verbose: print('TargetHealth for instance {0} in target group {1} is healthy.\n'.format(
                str(target_id), str(target_group_name)))
            break


if __name__ == '__main__':
    # Parse any args passed via command line
    parser = argparse.ArgumentParser(description='Setup ALB targets and rules for dev servers')
    parser.add_argument('-hc',
                        '--healthcheck',
                        dest='healthcheck',
                        help="Run script with target group health check for connectivity status with EC2 dev target",
                        action='store_true')
    parser.add_argument('-v',
                        '--verbose',
                        dest='verbose',
                        help="Increase output verbosity",
                        action='store_true')
    args = parser.parse_args()

    # Define globals derived from core.config import
    user_name = config.site.split("_")[0]
    host = config.hostname
    port = int(config.apache_port)
    dev_url = user_name + "-" + str(port) + ".dev.int.actionkit.com"

    # Create new target group; if target_group already exists, this command will not error and ARN will remain the same
    target_group_name = "dev-" + user_name + "-" + str(port)
    target_group_response = alb_client.create_target_group(Name=target_group_name, Protocol='HTTP', Port=port,
                                                           VpcId=vpc_id)

    # Validate new target group was created successfully
    new_target_group_arn = target_group_response['TargetGroups'][0]['TargetGroupArn']
    validate_target_creation(new_target_group_arn)

    # Register dev server target ec2 instance
    targets = [
        {
            'Id': target_id,
            'Port': port
        },
    ]
    register_target_response = alb_client.register_targets(TargetGroupArn=new_target_group_arn, Targets=targets)

    # Get existing rules so we can check for any duplicates and set priority
    http_rules = alb_client.describe_rules(ListenerArn=http_listener)
    https_rules = alb_client.describe_rules(ListenerArn=https_listener)

    # Set variables for HTTP/S rule(s) creation
    conditions = [
        {
            'Field': 'host-header',
            'Values': [dev_url]
        }
    ]
    actions = [
        {
            'Type': 'forward',
            'TargetGroupArn': new_target_group_arn
        },
    ]

    # Create HTTP rule unless it already exists since ALB allows duplicates
    create_http_rule = check_rule(http_rules)
    if create_http_rule is True:
        # Create new HTTP rule
        if args.verbose: print('Creating new HTTP rule for {0}...\n'.format(dev_url))
        create_rule('HTTP', http_rules, http_listener, conditions, actions)
    else:
        if args.verbose: print('HTTP rule already exists for {0}. \n'.format(
            str(dev_url), str(target_group_name)))
        if create_http_rule[1]['Actions'][0]['TargetGroupArn'] == new_target_group_arn:
            if args.verbose: print('Target group is already set to {0}.\n'.format(str(target_group_name)))
        elif create_http_rule[1]['Actions'][0]['TargetGroupArn'] != new_target_group_arn:
            if args.verbose: print('Target group is _not_ set to the new {0} group. You will need to manually update '
                                   'in AWS console.\n'.format(str(target_group_name)))

    # Create HTTPS rule unless it already exists since ALB allows duplicates
    create_https_rule = check_rule(https_rules)
    if create_https_rule is True:
        # Create new HTTP rule
        if args.verbose: print('Creating new HTTPS rule for {0}...\n'.format(dev_url))
        create_rule('HTTPS', https_rules, https_listener, conditions, actions)
        # Validate HTTPS rule was created successfully
    else:
        if args.verbose: print('HTTPS rule already exists for {0}. \n'.format(
            str(dev_url), str(target_group_name)))
        if create_http_rule[1]['Actions'][0]['TargetGroupArn'] == new_target_group_arn:
            if args.verbose: print('Target group is already set to {0}.\n'.format(str(target_group_name)))
        elif create_http_rule[1]['Actions'][0]['TargetGroupArn'] != new_target_group_arn:
            if args.verbose: print('Target group is _not_ set to the new {0} group. You will need to manually update '
                                   'in AWS console.\n'.format(str(target_group_name)))

    # Validate target health once it has been attached to the alb http rule
    if args.healthcheck:
        validate_target_health(new_target_group_arn)

