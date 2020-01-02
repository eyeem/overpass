import os
os.environ["CLUSTER_NAME"] = "test-cluster"
import yaml
from unittest.mock import MagicMock, call
from handler import handle_create, handle_delete
from overpass.kube import KubeWrapper, create_kube_config

k8s_response = {'Kind': 'config', 'apiVersion': 'v1',
    'clusters': [
    {'cluster': {'certificate-authority-data': 'certificate-data', 'server': 'endpoint-url'},
    'name': 'kubernetes'}],
     'contexts': [{'context': {'cluster': 'kubernetes', 'user': 'test-user'}, 'name': 'lambda'}],
     'current-context': 'lambda', 'users': [{'name': 'test-user', 'user': {'name': 'test-user'}}]}

with open("/tmp/kubeconfigpath-test", "w") as f:
        yaml.dump(k8s_response, f)

def test_handler_create():
    resource_properties = {
    "yaml": "---\n{apiVersion: v1,kind: Namespace, metadata: { annotations: {}, labels: {}, name: nightly}}\n---\n{apiVersion: apps/v1, kind: StatefulSet, metadata: {name: mysqldb, labels: {app: mysqldb}}, spec: {replicas: 1, selector: {matchLabels: {app: mysqldb}}, template: {metadata: {labels: {app: mysqldb}}, spec: {containers: [{name: mysqldb, image: 'mysql:latest', ports: [{containerPort: 3306, name: mysql}]}]}}}}",
    "namespace": "nightly"
    }
    documents = list(yaml.safe_load_all(resource_properties['yaml']))
    kube_wrapper = KubeWrapper("test-cluster", "eu-west-1", "MockAuth", "/tmp/kubeconfigpath-test")
    kube_wrapper.create_k8s_entity = MagicMock(return_value=dict())
    handle_create.__wrapped__({'ResourceProperties': resource_properties}, dict(), kube_wrapper)
    namespace_create_call = call('namespace', documents[0], 'nightly', 'nightly')
    stateful_set_create_call = call('statefulset', documents[1], 'mysqldb', 'nightly')
    kube_wrapper.create_k8s_entity.assert_has_calls([namespace_create_call, stateful_set_create_call])

def test_handler_delete():
    resource_properties = {
    "yaml": "---\n{apiVersion: v1,kind: Namespace, metadata: { annotations: {}, labels: {}, name: nightly}}\n---\n{apiVersion: apps/v1, kind: StatefulSet, metadata: {name: mysqldb, labels: {app: mysqldb}}, spec: {replicas: 1, selector: {matchLabels: {app: mysqldb}}, template: {metadata: {labels: {app: mysqldb}}, spec: {containers: [{name: mysqldb, image: 'mysql:latest', ports: [{containerPort: 3306, name: mysql}]}]}}}}",
    "namespace": "nightly"
    }
    documents = list(yaml.safe_load_all(resource_properties['yaml']))
    kube_wrapper = KubeWrapper("test-cluster", "eu-west-1", "MockAuth", "/tmp/kubeconfigpath-test")
    kube_wrapper.delete_k8s_entity = MagicMock(return_value=dict())
    handle_delete.__wrapped__({'ResourceProperties': resource_properties}, dict(), kube_wrapper)
    namespace_delete_call = call('namespace', 'nightly', 'nightly')
    stateful_set_delete_call = call('statefulset', 'mysqldb', 'nightly')
    kube_wrapper.delete_k8s_entity.assert_has_calls([namespace_delete_call, stateful_set_delete_call])
