from os import environ


def get_environment() -> str:
    """
    The `ENV` environment variable's value represents the deployment
    environment (dev, stage, prod, etc..).  This method gets the `ENV`
    environment variable's value
    """
    VALID_ENVS = ["dev", "stage", "prod"]

    env_environment_var = environ.get("ENV")
    if env_environment_var is None:
        environment = "dev"  # default environment
    elif env_environment_var in VALID_ENVS:
        environment = env_environment_var
    else:
        valid_envs_str = ",".join(VALID_ENVS)
        raise SystemExit(
            f"Must set environment variable `ENV` to one of {valid_envs_str}"
        )

    return environment
