"""
Code in this file is based on code of the aws-cli, which is Licensed under the
Apache License, Version 2.0. A copy of that License is located at
http://aws.amazon.com/apache2.0/.

https://github.com/aws/aws-cli/blob/3b9e3200639600a4fa73978696c87a043b66f100/LICENSE.txt
"""

import contextlib
import errno
import json
import os
import signal
import sys
from subprocess import check_call
from typing import Mapping


@contextlib.contextmanager
def ignore_user_entered_signals():
    """
    Ignores user entered signals to avoid process getting killed.
    """
    if sys.platform == "win32":
        signal_list = [signal.SIGINT]
    else:
        signal_list = [signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP]
    actual_signals = []
    for user_signal in signal_list:
        actual_signals.append(signal.signal(user_signal, signal.SIG_IGN))
    try:
        yield
    finally:
        for sig, user_signal in enumerate(signal_list):
            signal.signal(user_signal, actual_signals[sig])


def start_session(create_session_response: Mapping, region_name: str):
    # based on StartSessionCaller.invoke() in awscli/customizations/sessionmanager
    # https://github.com/aws/aws-cli/blob/develop/awscli/customizations/sessionmanager.py#L116C9-L117C14

    ssm_env_name = "AWS_SSM_START_SESSION_RESPONSE"
    try:
        session_parameters = {
            "SessionId": create_session_response["SessionId"],
            "TokenValue": create_session_response["TokenValue"],
            "StreamUrl": create_session_response["StreamUrl"],
        }
        start_session_response = json.dumps(session_parameters)

        env = os.environ.copy()

        env[ssm_env_name] = start_session_response
        start_session_response = ssm_env_name
        # ignore_user_entered_signals ignores these signals
        # because if signals which kills the process are not
        # captured would kill the foreground process but not the
        # background one. Capturing these would prevents process
        # from getting killed and these signals are input to plugin
        # and handling in there
        with ignore_user_entered_signals():
            # call executable with necessary input
            check_call(
                [
                    "session-manager-plugin",
                    start_session_response,
                    region_name,
                    "StartSession",
                ],
                env=env,
            )
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            print("SessionManagerPlugin is not present", file=sys.stderr)
