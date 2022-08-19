import time
import json
import boto3


def lambda_handler(event, context):
    print(json.dumps(event))
    tagName = event['tagname']
    tagValue = event['tagvalue']
    actionValue = event['action']
    
    if (actionValue is not None) and (tagName is not None) and (tagValue is not None):
        #EC2
        ec2InstanceList = listEC2InstancesByTag(tagName, tagValue)
        startStopEC2Instances(actionValue, ec2InstanceList)
        #RDS
        startStopRDSInstances(tagName, tagValue, actionValue)
        #DocumentDB
        startStopDocDBCluster(tagName, tagValue, actionValue)

    return {
        'statusCode': 200,
        'body': json.dumps('SUCCESS')
    }

#EC2 Instances.    
def startStopEC2Instances(actionValue, instanceIds):
    ec2 = boto3.resource('ec2')
    client = boto3.client('ec2')
    if actionValue.lower() == 'start':
        print('Starting EC2 instances.')
        return client.start_instances(InstanceIds=instanceIds)
    elif actionValue.lower() == 'stop':
        print('Stopping EC2 instances.')
        return client.stop_instances(InstanceIds=instanceIds)    
                        
                    
def listEC2InstancesByTag(tagkey, tagvalue):
    ec2client = boto3.client('ec2')
    response = ec2client.describe_instances(
        Filters=[
            {
                'Name': 'tag:'+tagkey,
                'Values': [tagvalue]
            }
        ]
    )
    instancelist = []
    for reservation in (response["Reservations"]):
        for instance in reservation["Instances"]:
            instancelist.append(instance["InstanceId"])
    return instancelist       
    
#RDS Instances.
def startStopRDSInstances(tagkey, tagvalue, actionValue):
    rdsclient = boto3.client('rds')
    response = rdsclient.describe_db_instances()
    for dbInstance in (response["DBInstances"]):
        for tag in (dbInstance["TagList"]):
            if tag["Key"] == tagkey and tag["Value"] == tagvalue:
                dbInstanceIdentifier = dbInstance['DBInstanceIdentifier']
                if actionValue.lower() == 'start' and dbInstance['DBInstanceStatus'] == 'stopped':
                    print('Starting RDS DB instance. - ' + dbInstanceIdentifier)
                    rdsclient.start_db_instance(DBInstanceIdentifier=dbInstanceIdentifier)
                elif actionValue.lower() == 'stop' and dbInstance['DBInstanceStatus'] == 'available':
                    print('Stopping RDS DB instance. - ' + dbInstanceIdentifier)
                    rdsclient.stop_db_instance(DBInstanceIdentifier=dbInstanceIdentifier)
                    
        
#DocumentDB Instances.
def startStopDocDBCluster(tagkey, tagvalue, actionValue):
    client = boto3.client('docdb')
    response = client.describe_db_clusters(
        Filters=[
        {
            'Name': 'engine',
            'Values': [
                'docdb'
            ]
        },
    ])
    for docDBCluster in (response["DBClusters"]):
        tagListResponse = client.list_tags_for_resource(ResourceName=docDBCluster['DBClusterArn'])
        tagList = tagListResponse['TagList']
        for tag in tagList:
            if tag["Key"] == tagkey and tag["Value"] == tagvalue:
                if actionValue.lower() == 'start' and docDBCluster['Status'] == 'stopped':
                    print('DocumentDB cluster ' + docDBCluster['DBClusterIdentifier'] + ' is in stopped state. Starting it now.')
                    client.start_db_cluster(DBClusterIdentifier=docDBCluster['DBClusterIdentifier'])
                elif actionValue.lower() == 'stop' and docDBCluster['Status'] == 'available':
                    print('DocumentDB ' + docDBCluster['DBClusterIdentifier'] + ' is in available state. Stopping it now.')
                    client.stop_db_cluster(DBClusterIdentifier=docDBCluster['DBClusterIdentifier'])
        
    
                                     