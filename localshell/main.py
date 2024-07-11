import os
import sys
from multiprocessing import Process
from time import sleep

import boto3
import click

from .awscli import start_session
from .data import VpcConfig, Environment

ENVIRONMENT_NAME = "cloudshell-local"

# patch in our own models by setting the AWS_DATA_PATH
os.environ["AWS_DATA_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


@click.command()
@click.option("--vpc-id", prompt="VpcId")
@click.option("--subnet-ids", prompt="SubnetIds")
@click.option("--security-group-ids", prompt="SecurityGroupIds")
def run(vpc_id, subnet_ids, security_group_ids):
    requested_vpc_config = VpcConfig(
        vpc_id,
        frozenset(subnet_ids.split(",")),
        frozenset(security_group_ids.split(",")),
    )

    cloudshell = boto3.client("cloudshell")
    environments = [Environment.load(x) for x in cloudshell.describe_environments()["Environments"]]

    envs_without_vpc = set()
    other_envs_with_vpc = set()
    our_env = None
    for e in environments:
        if e.vcp_config is None:
            envs_without_vpc.add(e)
        elif e.vcp_config == requested_vpc_config:
            our_env = e
        elif e.environment_name == ENVIRONMENT_NAME:
            our_env = e
        else:
            other_envs_with_vpc.add(e)

    if our_env is None and len(other_envs_with_vpc) >= 2:
        print("There are already 2 Environments with a VPC Configuration. Aborting", file=sys.stderr)
        exit(1)

    if our_env is not None and our_env.vcp_config != requested_vpc_config:
        print(f"Environment {ENVIRONMENT_NAME} already exists with a different configuration. Recreating it")
        cloudshell.delete_environment(EnvironmentId=our_env.environment_id)
        our_env = None
    if our_env is None:
        our_env = Environment.load(
            cloudshell.create_environment(
                EnvironmentName=ENVIRONMENT_NAME,
                VpcConfig=requested_vpc_config.dump(),
            )
        )

    print(f"Using environment {our_env.environment_name} ({our_env.environment_id})")

    status = cloudshell.get_environment_status(EnvironmentId=our_env.environment_id)["Status"]
    while status != "RUNNING":
        print(f"current status: {status}")
        if status == "SUSPENDED":
            cloudshell.start_environment(EnvironmentId=our_env.environment_id)
        elif status in {"RESUMING", "CREATING"}:
            pass
        else:
            raise ValueError(f"Unexpected status {status}")
        sleep(5)
        status = cloudshell.get_environment_status(EnvironmentId=our_env.environment_id)["Status"]

    print("Environment is ready, creating session")
    session = cloudshell.create_session(EnvironmentId=our_env.environment_id)
    print(f"Session created: {session['SessionId']}")
    process = start_keep_alive(our_env)
    start_session(session, str(boto3.session.Session.region_name))
    process.terminate()
    sleep(1)
    process.kill()


def start_keep_alive(environment: "Environment") -> Process:
    p = Process(target=keep_alive, args=[environment.environment_id])
    p.start()
    return p


def keep_alive(environment_id: str) -> None:
    cloudshell = boto3.client("cloudshell")
    while True:
        cloudshell.send_heart_beat(EnvironmentId=environment_id)
        sleep(5 * 60)


if __name__ == "__main__":
    run()
