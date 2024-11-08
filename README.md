
# Schematic AWS CDK app

AWS CDK app for deploying [Schematic](schematic.api.sagebionetworks.org).

# Prerequisites

AWS CDK projects require some bootstrapping before synthesis or deployment.
Please review the [bootstapping documentation](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_bootstrap)
before development.

# Dev Container

This repository provides a [dev container](https://containers.dev/) that includes all the tools
required to develop this AWS CDK app.

## Opening the project inside its dev container

With VS Code:

1. Clone this repo
2. File > Open Folder...
3. A prompt should invite you to open the project inside the dev container. If not, open VS Code
    Command Palette and select "Dev Containers: Open Folder in Container..."

With GitHub Codespaces:

1. From the main page of this repository, click on the button "Code" > Codespaces > Click on the
   button "Create codespace"

That's it! You are now inside the dev container and have access to all the development tools.

# Development

All the development tools are provided when developing inside the dev container
(see above). These tools include Python, AWS CLI, AWS CDK CLI, etc. These tools
also include a Python virtual environment where all the Python packages needed
are already installed.

If you decide the develop outside of the dev container, some of the development
tools can be installed by running:

```console
./tools/setup.sh
```

Development requires the activation of the Python virtual environment:

```
$ source .venv/bin/activate
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


# Testing

## Static Analysis

As a pre-deployment step we syntactically validate the CDK json, yaml and
python files with [pre-commit](https://pre-commit.com).

Please install pre-commit, once installed the file validations will
automatically run on every commit.  Alternatively you can manually
execute the validations by running `pre-commit run --all-files`.

Verify CDK to Cloudformation conversion by running [cdk synth]:

```console
cdk synth
```

The Cloudformation output is saved to the `cdk.out` folder

## Unit Tests

Tests are available in the tests folder. Execute the following to run tests:

```
python -m pytest tests/ -s -v
```


# Environments

Deployment context is set in the [cdk.json](cdk.json) file.  An `ENV` environment variable must be
set to tell the CDK which environment's variables to use when synthesising or deploying the stacks.
The deployment context is the place to set infrastructure variables.

Set an environment in cdk.json in `context` section of cdk.json:

```json
  "context": {
    "dev": {
        "VPC_CIDR": "10.254.192.0/24",
        "FQDN": "dev.schematic.io"
    },
    "prod": {
        "VPC_CIDR": "10.254.194.0/24",
        "FQDN": "prod.schematic.io"
    },
  }
```

For example, synthesis with the `prod` environment variables:

```console
ENV=prod cdk synth
```

# Certificates

Certificates to set up HTTPS connections should be created manually in AWS certificate manager.
This is not automated due to AWS requiring manual verification of the domain ownership.
Once created take the ARN of the certificate and add it to a context in cdk.json.

```json
  "context": {
    "dev": {
      "CERTIFICATE_ARN": "arn:aws:acm:us-east-1:XXXXXXXXX:certificate/76ed5a71-4aa8-4cc1-9db6-aa7a322ec077"
    }
  }
```

![ACM certificate](docs/acm-certificate.png)

# Secrets

Secrets can be manually created in the
[AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/create_secret.html)

To pass secrets to a container set the secrets manager `secret name`
when creating a ServiceProp objects:

```python
app_service_props = ServiceProps(
    "app", 443, 1024, f"ghcr.io/sage-bionetworks/app:v1.0", container_env_vars={},
    container_secret_name="app/dev/DATABASE"
)
```

For example, the KVs for `app/dev/DATABASE` could be:
```json
{
    "DATABASE_USER": "maria",
    "DATABASE_PASSWORD": "password"
}
```

> [!NOTE]
> Retrieving secrets requires access to the AWS Secrets Manager

# Deployment

## Bootstrap

There are a few items that need to be manually bootstrapped before deploying the application.

* Add secrets to the AWS Secrets Manager
* Create an [ACM certificate for the application](#Certificates) using the AWS Certificates Manager
* Add the Certificate ARN to the cdk.json
* Update references to the docker images in [app.py](app.py)
  (i.e. `ghcr.io/sage-bionetworks/app-xxx:<tag>`)
* (Optional) Update the `ServiceProps` objects in [app.py](app.py) with parameters specific to
  each container.

## Login with the AWS CLI

> [!NOTE]
> This and the following sections assume that you are working in the AWS account
> `org-sagebase-itsandbox` with the role `Developer` and that you are deploying
> to the `us-east-1` region. If this assumption is correct, you should be able
> to simply copy-paste the following commands, otherwise adapting the
> configuration should be straightforward.

Create the config file if it doesn't exist yet.

```console
mkdir ~/.aws && touch ~/.aws/config
```

As a Developer working in Sage IT Sandbox AWS account, add the following profile to the config file.

```ini
[profile itsandbox-dev]
sso_start_url = https://d-906769aa66.awsapps.com/start
sso_region = us-east-1
sso_account_id = XXXXXXXXX
sso_role_name = Developer
```

Login with the AWS CLI:

```console
aws --profile itsandbox-dev sso login
```


## Deploy

Deployment requires setting up an [AWS profile](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)
then executing the following command:

```console
AWS_PROFILE=itsandbox-dev AWS_DEFAULT_REGION=us-east-1 ENV=dev cdk deploy --all
```

## Force new deployment

```console
AWS_PROFILE=itsandbox-dev AWS_DEFAULT_REGION=us-east-1 aws ecs update-service \
  --cluster <cluster-name> \
  --service <service-name> \
  --force-new-deployment
```

# Execute a command from a container running on ECS

Once a container has been deployed successfully it is accessible for debugging using the
[ECS execute-command](https://docs.aws.amazon.com/cli/latest/reference/ecs/execute-command.html)

Example to get an interactive shell run into a container:

```console
AWS_PROFILE=itsandbox-dev AWS_DEFAULT_REGION=us-east-1 aws ecs execute-command \
  --cluster AppEcs-ClusterEB0386A7-BygXkQgSvdjY \
  --task a2916461f65747f390fd3e29f1b387d8 \
  --container app-mariadb \
  --command "/bin/sh" --interactive
```


# CI Workflow

This repo has been set up to use Github Actions CI to continuously deploy the application.

The workflow for continuous integration:

* Create PR from the git dev branch
* PR is reviewed and approved
* PR is merged
* CI deploys changes to the dev environment (dev.app.io) in the AWS dev account.
* Changes are promoted (or merged) to the git stage branch.
* CI deploys changes to the staging environment (stage.app.io) in the AWS prod account.
* Changes are promoted (or merged) to the git prod branch.
* CI deploys changes to the prod environment (prod.app.io) in the AWS prod account.
