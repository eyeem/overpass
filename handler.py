from __future__ import print_function
from crhelper import CfnResource
import logging

import os.path
import yaml
import boto3
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException

import auth

# Configure your cluster name and region here
KUBE_FILEPATH = '/tmp/kubeconfig'
CLUSTER_NAME = 'eyeem-eks-cluster-stage'
REGION = 'eu-west-1'

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level='INFO', boto_level='DEBUG')

try:
    # We assume that when the Lambda container is reused, a kubeconfig file exists.
    # If it does not exist, it creates the file.
    if not os.path.exists(KUBE_FILEPATH):
        logger.warning("KUBE_FILEPATH not present. Creating one")
        # Get data from EKS API
        eks_api = boto3.client('eks', region_name=REGION)
        cluster_info = eks_api.describe_cluster(name=CLUSTER_NAME)
        logger.warning("describe_cluster API call finished")
        certificate = cluster_info['cluster']['certificateAuthority']['data']
        endpoint = cluster_info['cluster']['endpoint']
        logger.warning("Got the cluster information")

        # Generating kubeconfig
        kube_content = dict()

        kube_content['apiVersion'] = 'v1'
        kube_content['clusters'] = [
            {
                'cluster':
                    {
                        'server': endpoint,
                        'certificate-authority-data': certificate
                    },
                'name': 'kubernetes'

            }]

        kube_content['contexts'] = [
            {
                'context':
                    {
                        'cluster': 'kubernetes',
                        'user': 'lambda'
                    },
                'name': 'lambda'
            }]

        kube_content['current-context'] = 'lambda'
        kube_content['Kind'] = 'config'
        kube_content['users'] = [
            {
                'name': 'lambda',
                'user': {
                    'name': 'lambda'
                }
            }]

        # Write kubeconfig
        with open(KUBE_FILEPATH, 'w') as outfile:
            yaml.dump(kube_content, outfile, default_flow_style=False)
        logger.warning("Done creating the KUBE_FILEPATH")
except Exception as e:
    helper.init_failure(e)


@helper.create
def create(event, context):
    token = _get_token()
    logger.info("Got Create")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        kind = str.lower(document['kind'])
        logger.info("ready to create a namespaced %s....." % kind)
        resp = _create_k8s_entity(kind, document, namespace, _init_k8s_client(token))
        logger.info(resp)
    return "ok"


@helper.update
def update(event, context):
    token = _get_token()
    logger.info("Got Update")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        kind = str.lower(document['kind'])
        name = document['metadata']['name']
        logger.info("ready to update a namespaced %s..... with name %s" % (kind, name))
        resp = _update_k8s_entity(kind, document, namespace, _init_k8s_client(token))
        logger.info(resp)
    return "ok"


@helper.delete
def delete(event, context):
    token = _get_token()
    logger.info("Got Delete")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        name = document['metadata']['name']
        kind = str.lower(document['kind'])
        try:
            _delete_k8s_entity(kind, name, namespace, _init_k8s_client(token))
        except ApiException as e:
            if e.status == 404:
                pass
            else:
                raise e
    return "ok"


def handler(event, context):
    logger.info("Starting execution...")
    helper(event, context)


def _get_token():
    # Get Token
    eks = auth.EKSAuth(CLUSTER_NAME)
    token = eks.get_token()
    logger.info("Got the token from the EKS cluster")
    # Configure
    config.load_kube_config(KUBE_FILEPATH)
    return token


def _init_k8s_client(token):
    configuration = client.Configuration()
    configuration.api_key['authorization'] = token
    configuration.api_key_prefix['authorization'] = 'Bearer'
    return client.ApiClient(configuration)


def _create_k8s_entity(kind, body, namespace, k8s_client):
    if kind == 'deployment':
        api_instance = client.AppsV1Api(k8s_client)
        return api_instance.create_namespaced_deployment(body=body, namespace=namespace)
    elif kind == 'namespace':
        api_instance = client.CoreV1Api(k8s_client)
        return api_instance.create_namespace(body)
    elif kind == 'service':
        api_instance = client.CoreV1Api(k8s_client)
        return api_instance.create_namespaced_service(body=body, namespace=namespace)
    elif kind == 'statefulset':
        api_instance = client.AppsV1Api(k8s_client)
        api_instance.create_namespaced_stateful_set(namespace=namespace, body=body)
    else:
        raise RuntimeError("The kind %s is not supported by this lambda yet.")


def _update_k8s_entity(kind, body, name, namespace, k8s_client):
    if kind == 'deployment':
        _delete_k8s_entity(kind, name, namespace, k8s_client)
        return _create_k8s_entity(kind, body, namespace, k8s_client)
    else:
        raise RuntimeError("The kind %s is not supported by this lambda yet.")


def _delete_k8s_entity(kind, name, namespace, k8s_client):
    if kind == 'deployment':
        api_instance = client.AppsV1Api(k8s_client)
        return api_instance.delete_namespaced_deployment(namespace=namespace, name=name)
    elif kind == 'namespace':
        api_instance = client.CoreV1Api(k8s_client)
        return api_instance.delete_namespace(name=name)
    elif kind == 'service':
        api_instance = client.CoreV1Api(k8s_client)
        return api_instance.delete_namespaced_service(namespace=namespace, name=name)
    elif kind == 'statefulset':
        api_instance = client.AppsV1Api(k8s_client)
        api_instance.delete_namespaced_stateful_set(namespace=namespace, name=name)
    else:
        raise RuntimeError("The kind %s is not supported by this lambda yet.")
