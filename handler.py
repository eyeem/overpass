import logging
from functools import wraps
import yaml
import boto3
from crhelper import CfnResource
from kubernetes.client.rest import ApiException
from overpass.config import CONFIG
from overpass.kube import create_kube_config, KubeWrapper


LOGGER = logging.getLogger(__name__)

# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level='DEBUG', boto_level='WARN')

try:
    create_kube_config(CONFIG.KUBE_FILEPATH, boto3.client('eks', region_name=CONFIG.REGION), CONFIG.CLUSTER_NAME)
except Exception as ex:
    helper.init_failure(ex)


def authenticate(func):
    @wraps(func)
    def wrapped(event, context):
        kube_wrapper = KubeWrapper(CONFIG.CLUSTER_NAME, CONFIG.REGION, CONFIG.AUTH_BACKEND, CONFIG.KUBE_FILEPATH)
        return func(event, context, kube_wrapper)
    return wrapped


@helper.create
@authenticate
def handle_create(event, context, kube_wrapper):
    LOGGER.info("Got Create")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        kind = str.lower(document['kind'])
        name = document['metadata']['name']
        LOGGER.info("ready to create a namespaced %s with name %s.....", kind, name)
        try:
            kube_wrapper.create_k8s_entity(kind, document, name, namespace)
        except ApiException as exc:
            if exc.status == 409: #Resource might have been already created
                kube_wrapper.update_k8s_entity(kind, document, name, namespace)
            else:
                raise exc
    return "ok"


@helper.update
@authenticate
def handle_update(event, context, kube_wrapper):
    LOGGER.info("Got Update")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        kind = str.lower(document['kind'])
        name = document['metadata']['name']
        LOGGER.info("ready to update a namespaced %s..... with name %s", kind, name)
        kube_wrapper.update_k8s_entity(kind, document, namespace, name)
    return "ok"


@helper.delete
@authenticate
def handle_delete(event, context, kube_wrapper):
    LOGGER.info("Got Delete")
    properties = event.get('ResourceProperties', {})
    documents = yaml.safe_load_all(properties['yaml'])
    namespace = properties['namespace']
    for document in documents:
        name = document['metadata']['name']
        kind = str.lower(document['kind'])
        try:
            kube_wrapper.delete_k8s_entity(kind, name, namespace)
        except ApiException as ex:
            if ex.status != 404:
                pass
            else:
                raise ex
    return "ok"


def handler(event, context):
    LOGGER.debug("Starting execution...")
    helper(event, context)
