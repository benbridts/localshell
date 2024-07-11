# LocalShell
LocalShell for AWS CloudShell

This is a minimum proof of concept to start (and keep alive) a cloud shell session
in a VPC.

What works:
- Starting a CloudShell session in a VPC from the CLI (using the standard SDK
  to resolve credentials, consider setting AWS_PROFILE if you want to use a
  different profile).

What does not work:
- Using AWS Credentials in the CloudShell environment (if you do not log into the
  environment from the console). This support is not planned

# Usage
You need to have the Session Manager Plugin installed for this to work.
https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

This has only been tested with `poetry`, but you should be able to install this
with `pip` or `pipx` too

You can also set some command line options. See `localshell --help`

## Poetry
1. Clone this repository
2. `poetry install`
2. `poetry run -- localshell`

## Pip(x)
1. `pipx install git+https://github.com/benbridts/localshell.git`
2. `localshell`

# FAQ
## Is this a good idea?
No, use this at your own risk. You're on your own if this breaks, or AWS decides
to yell at you.
