import os
import yaml
os.environ["CLUSTER_NAME"] = "test-cluster"
import botocore.session
from botocore.stub import Stubber
from overpass.kube import create_kube_config


def test_kubeconfig_creation():
    file_path = "/tmp/kubeconfig-test"
    eks = botocore.session.get_session().create_client('eks', region_name='eu-west-1')
    k8s_response = {'cluster': {
     'certificateAuthority': {
       'data': "certificate-data"
     },
     'endpoint': "endpoint-url"
    }}
    expected_response = {'Kind': 'config', 'apiVersion': 'v1',
    'clusters': [
    {'cluster': {'certificate-authority-data': 'certificate-data', 'server': 'endpoint-url'},
    'name': 'kubernetes'}],
     'contexts': [{'context': {'cluster': 'kubernetes', 'user': 'test-user'}, 'name': 'lambda'}],
     'current-context': 'lambda', 'users': [{'name': 'test-user', 'user': {'name': 'test-user'}}]}
    actual_response = None
    with Stubber(eks) as stubber:
        stubber.add_response('describe_cluster', k8s_response)
        if os.path.exists(file_path):
            os.remove(file_path)
        create_kube_config(file_path, eks, "test-cluster", user_name="test-user")
        with open(file_path) as f:
            actual_response = yaml.safe_load(f)
            print(actual_response)
    assert(expected_response == actual_response)
