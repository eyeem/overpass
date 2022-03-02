import logging
from kubernetes import client, config
from overpass.auth import AwsStsAuth, MockAuth
from overpass.config import CONFIG

LOGGER = logging.getLogger(__name__)
#logging.getLogger("urllib3").setLevel(logging.DEBUG)
#logging.getLogger('kubernetes').setLevel(logging.DEBUG)

class KubeWrapper:
    def __init__(self, cluster_name, region, auth_backend, config_file_path):
        self.client = self._init_client(cluster_name, region, auth_backend, config_file_path)

    def _get_token(self, cluster_name, region, auth_backend):
        if auth_backend == 'AwsSTS':
            return AwsStsAuth(cluster_name).get_token()
        elif auth_backend == 'MockAuth':
            return MockAuth().get_token()
        else:
            raise RuntimeError(f"{auth_backend} is not implemented")

    def _init_client(self, cluster_name, region, auth_backend, config_file_path):
        token = self._get_token(cluster_name, region, auth_backend)
        LOGGER.debug("Succesfully retrieved token for authentication with kube api server")
        config.load_kube_config(config_file_path)
        configuration = client.Configuration()
        #configuration.debug = True
        configuration.api_key['authorization'] = token
        configuration.api_key_prefix['authorization'] = 'Bearer'
        return client.ApiClient(configuration)

    def create_k8s_entity(self, kind, body, name, namespace):
        if kind == 'deployment':
            api_instance = client.AppsV1Api(self.client)
            return api_instance.create_namespaced_deployment(body=body, namespace=namespace)
        elif kind == 'namespace':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.create_namespace(body)
        elif kind == 'service':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.create_namespaced_service(body=body, namespace=namespace)
        elif kind == 'statefulset':
            api_instance = client.AppsV1Api(self.client)
            return api_instance.create_namespaced_stateful_set(namespace=namespace, body=body)
        elif kind == 'configmap':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.create_namespaced_config_map(namespace=namespace, body=body)
        elif kind == 'secret':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.create_namespaced_secret(namespace=namespace, body=body)
        elif kind == 'serviceaccount':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.create_namespaced_service_account(namespace=namespace, body=body)
        else:
            raise RuntimeError("The kind %s for name %s is not supported by this lambda yet." % (kind,name))

    def update_k8s_entity(self, kind, body, name, namespace):
        self.delete_k8s_entity(kind, name, namespace)
        return self.create_k8s_entity(kind, body, name, namespace)

    def delete_k8s_entity(self, kind, name, namespace):
        if kind == 'deployment':
            api_instance = client.AppsV1Api(self.client)
            return api_instance.delete_namespaced_deployment(namespace=namespace, name=name)
        elif kind == 'namespace':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.delete_namespace(name=name)
        elif kind == 'service':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.delete_namespaced_service(namespace=namespace, name=name)
        elif kind == 'statefulset':
            api_instance = client.AppsV1Api(self.client)
            api_instance.delete_namespaced_stateful_set(namespace=namespace, name=name)
        elif kind == 'configmap':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.delete_namespaced_config_map(namespace=namespace, name=name)
        elif kind == 'secret':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.delete_namespaced_secret(namespace=namespace, name=name)
        elif kind == 'serviceaccount':
            api_instance = client.CoreV1Api(self.client)
            return api_instance.delete_namespaced_service_account(namespace=namespace, name=name)
        else:
            raise RuntimeError("The kind %s for name %s is not supported by this lambda yet." % (kind,name))
