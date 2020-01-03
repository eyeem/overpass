import os


class Config:
    # Configure your cluster name and region here
    KUBE_FILEPATH = os.environ.get('KUBE_FILEPATH', '/tmp/kubeconfig')
    CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
    if CLUSTER_NAME is None:
        raise RuntimeError("CLUSTER_NAME env variable is not set")
    REGION = os.environ.get('AWS_REGION', 'eu-west-1')
    AUTH_BACKEND = os.environ.get('AUTH_BACKEND', 'AwsSTS')


CONFIG = Config()
