import boto3
import os

SSM_CLIENT = boto3.client("ssm")
LOG_BUCKET = os.environ["LOG_BUCKET"]
LOG_BUCKET_REGION = os.environ["LOG_BUCKET_REGION"]

commands = ["echo 'started'", "echo 'sleep 20 seconds'", "sleep 20", "echo 'finished'"]


def __send_command(execution_uuid, instance_ids):
    response = SSM_CLIENT.send_command(
        Targets=[
            {
                "Key": "InstanceIds",
                "Values": instance_ids
            },
        ],
        DocumentName="AWS-RunShellScript",
        MaxConcurrency="50",
        MaxErrors="0",
        Parameters={
            "commands": commands
        },
        TimeoutSeconds=3600,
        OutputS3BucketName=LOG_BUCKET,
        OutputS3KeyPrefix=f"{execution_uuid}/logs",
        OutputS3Region=LOG_BUCKET_REGION,
    )
    print(response)
    command_id = response["Command"]["CommandId"]
    return command_id


def lambda_handler(event, context):
    print(event)
    instance_ids = event["instance_ids"]
    execution_uuid = event["execution_id"].split(":")[-1]
    command_id = __send_command(execution_uuid, instance_ids)
    return {
        'command_id': command_id,
        'instance_ids': instance_ids,
    }
