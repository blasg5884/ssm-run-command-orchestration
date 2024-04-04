import boto3

SSM_CLIENT = boto3.client("ssm")


def __poll_command(command_id, instance_id):
    response = SSM_CLIENT.get_command_invocation(
        CommandId = command_id,
        InstanceId = instance_id,
    )
    return response


def check_under_execution(command_id, instance_ids):
    for instance_id in instance_ids:
        response = __poll_command(command_id, instance_id)
        status = response["Status"]
        if status in ["Delayed", "InProgress", "Pending"]:
            print("Under execution...")
            return True
    return False


def lambda_handler(event, context):
    print(event)
    print(context)
    command_id, instance_ids = event["command_id"], event["instance_ids"]
    is_under_execution = check_under_execution(command_id, instance_ids)
    return {
        'command_id': command_id,
        'instance_ids': instance_ids,
        'is_under_execution': is_under_execution,
    }
