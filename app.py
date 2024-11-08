import aws_cdk as cdk
import src.utils as utils

from src.network_stack import NetworkStack
from src.ecs_stack import EcsStack
from src.service_stack import LoadBalancedServiceStack
from src.load_balancer_stack import LoadBalancerStack
from src.service_props import ServiceProps

# get the environment
environment = utils.get_environment()
stack_name_prefix = f"schematic-{environment}"

cdk_app = cdk.App()
context_vars = cdk_app.node.try_get_context(environment)
fully_qualified_domain_name = context_vars["FQDN"]
subdomain, domain = fully_qualified_domain_name.split(".", 1)
vpc_cidr = context_vars["VPC_CIDR"]
certificate_arn = context_vars["CERTIFICATE_ARN"]
env_tags = context_vars["TAGS"]

# recursively apply tags to all stack resources
if env_tags:
    for key, value in env_tags.items():
        cdk.Tags.of(cdk_app).add(key, value)

# Generate stacks
network_stack = NetworkStack(cdk_app, f"{stack_name_prefix}-network", vpc_cidr)

ecs_stack = EcsStack(
    cdk_app, f"{stack_name_prefix}-ecs", network_stack.vpc, fully_qualified_domain_name
)

# From AWS docs https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-connect-concepts-deploy.html
# The public discovery and reachability should be created last by AWS CloudFormation, including the frontend
# client service. The services need to be created in this order to prevent an time period when the frontend
# client service is running and available the public, but a backend isn't.
load_balancer_stack = LoadBalancerStack(
    cdk_app, f"{stack_name_prefix}-load-balancer", network_stack.vpc
)

app_service_props = ServiceProps(
    "schematic-app",
    443,
    4096,
    "ghcr.io/sage-bionetworks/schematic:v0.1.90-beta",
    {},
    "schematic-dev-DockerFargateStack/dev/ecs",
)

app_service_stack = LoadBalancedServiceStack(
    cdk_app,
    f"{stack_name_prefix}-app",
    network_stack.vpc,
    ecs_stack.cluster,
    app_service_props,
    load_balancer_stack.alb,
    certificate_arn,
    health_check_path="/health",
    health_check_interval=5,
)

cdk_app.synth()
