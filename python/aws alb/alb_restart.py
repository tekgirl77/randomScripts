#!/bin/env python

'''
This script will automagically scale an AWS Auto Scaling Group out to bring up
new nodes and then scale back down to the minimum desired once they are
healthy.
'''

import boto3
import fasteners
import core.log

# Our normal baseline for the number instances in an ASG
baseline_count = 3
wait_time = 600

core.log.configure_logging()
log = core.log.logger('alb_restart')

def main():
    (albs, target_groups, asg) = find_arns()

    target_count = asg['DesiredCapacity'] + baseline_count

    check_asg(asg, target_count)

    scale(asg, target_count)
    monitor_scale_out(target_groups, target_count)
    scale(asg, baseline_count)

def find_arns():
    client = boto3.client('resourcegroupstaggingapi')
    all_arns = [r['ResourceARN'] for r in client.get_resources(TagFilters=[ { 'Key': 'type', 'Values': ['web'] }, {'Key': 'mode', 'Values': ['prod']}], ResourceTypeFilters=['elasticloadbalancing'])['ResourceTagMappingList']]

    albs = [arn for arn in all_arns if ':loadbalancer/app' in arn]
    targets = [arn for arn in all_arns if ':targetgroup/' in arn]

    client = boto3.client('autoscaling')
    asgs = []

    for asg in client.describe_auto_scaling_groups()['AutoScalingGroups']:
        tags = {}
        for tag in asg['Tags']:
            tags[tag['Key']] = tag['Value']

        if ('type' in tags and tags['type'] == 'web' and
            'mode' in tags and tags['mode'] == 'prod'):
            asgs.append(asg)

    if len(asgs) > 1:
        raise Exception('Found more than one ASG that fits our critieria, dying')
    
    return [albs, targets, asgs[0]]

def check_asg(asg, target_count):
    if target_count > asg['MaxSize']:
        raise Exception("""Increasing the ASG size would exceed the ASG's MaxSize, dying""")

    for instance in asg['Instances']:
        if instance['HealthStatus'] != 'Healthy':
            raise Exception("""Unhealthy instances in the ASG, dying""")
            
        if instance['LifecycleState'] != 'InService' and instance['LifecycleState'] != 'Terminating':
            raise Exception("""Instances are in the ASG that are not InService, dying""")

    log.debug('ASG checks successful')

    return True


def scale(asg, count):
    client = boto3.client('autoscaling')

    log.debug('Setting DesiredCapacity for %s to %d' % (asg['AutoScalingGroupName'], count))

    client.set_desired_capacity(AutoScalingGroupName=asg['AutoScalingGroupName'], DesiredCapacity=count)

    return True

def monitor_scale_out(target_groups, target_count):
    import time
    client = boto3.client('elbv2')

    tgs = {tg: True for tg in target_groups}

    count = 0

    while tgs and count < wait_time:
        for tg in tgs.keys():
            health = client.describe_target_health(TargetGroupArn=tg)['TargetHealthDescriptions']
            healthy_count = len([target for target in health if target['TargetHealth']['State'] == 'healthy'])
            if healthy_count == target_count:
                log.debug('%s became healthy' % (tg))
                del tgs[tg]
            else:
                if count % 30 == 0:
                    log.debug('%s is not healthy (%d healthy, %d required)' % (tg, healthy_count, target_count))

        count = count + 1
        time.sleep(1)

    if tgs:
        raise Exception("""Not all of the targets became healthy after 10 minutes, dying""")

if __name__ == "__main__":
    lock = fasteners.InterProcessLock('/tmp/web_restart')

    if lock.acquire(timeout=1):
        main()
    else:
        raise Exception("""A restart is currently running, hold your horses.""")

    
