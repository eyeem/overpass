import os


def test_config_loading():
    os.environ["CLUSTER_NAME"] = "test-cluster"
    from overpass.config import CONFIG
    assert CONFIG.KUBE_FILEPATH == '/tmp/kubeconfig'
    assert CONFIG.CLUSTER_NAME == "test-cluster"
    assert CONFIG.AUTH_BACKEND == "AwsSTS"
    assert CONFIG.REGION == "eu-west-1"
    assert CONFIG.KUBE_USER == "lambda"


def test_config_loading_error():
    try:
        from overpass.config import CONFIG
    except RuntimeError as ex:
        assert ex.__cause__ == "CLUSTER_NAME env variable is not set"
