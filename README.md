Overpass   [![Build Status](https://travis-ci.org/eyeem/overpass.svg?branch=master)](https://travis-ci.org/eyeem/overpass)
========

Overpass allows you to deploy to kubernetes clusters from the Cloudformation templates. Overpass deploys a lambda function in AWS which can be invoked with Kubernetes resource templates via the cloudformation. 

Right now, overpass only supports actions on EKS clusters.

**Development**
-----------

Overpass uses [pipenv](https://github.com/pypa/pipenv) for development and packaging. Refer the Pipfile for required dependencies. 


**Deploying**
----

> serverless deploy  -r <AWS_REGION> -s \<ENV>


**Configuration**

The overpass creates the necessary IAM roles for executing the lambda. You might have to alter the security groups and other VPC related config in the `aws-config.yml`. There is a template provided to give guidance about what is required to setup the Lambda. There are also other environment variables that overpass supports:

 Name | Default | Required? | Description 
------|-----|------|------------
CLUSTER_NAME | None | Yes | Name of the EKS cluster to operate on
REGION | None | Yes | AWS Region
KUBE_FILEPATH | /tmp/kubeconfig | No | File path to store the generated kube config
AUTH_BACKEND | AwsSTS | No | Auth mechanism to use to connect securely to Kubernetes. Currently only STS is supported.
KUBE_USER | lambda | No | Username to use when connecting to Kubernetes. This is important and should be same as the name used while configuring access in Kubernetes


_**EKS Cluster Config**_ 

Set the environment variable CLUSTER_NAME with your target EKS cluster name.

After deploying the function to Lamda, note down the ARN for the lambda role that is created. This ARN needs to be configured in the 
kubernetes cluster to allow the Lambda to deploy/remove resources. 

* Create entry in `aws-auth configmap` in kubernetes to map the above ARN to a kubernetes user
```$xslt
    rolearn: arn:aws:iam::123123123123:role/<UNIQUE_ROLE_ID>
    username: lambda
```
* Create a `ClusteRole` and `ClusterRoleBinding` to authorize the above `lambda` user to perform actions on kubernetes
```$xslt
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: lambda-access
rules:
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["create", "delete"]

- apiGroups: ["", "extensions", "apps", "autoscaling"]
  resources: ["deployments", "replicasets", "pods","services","horizontalpodautoscalers","secrets","configmaps","events","deployments/rollback", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]

---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: lambda-user-role-binding

subjects:
- kind: User
  name: lambda
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: lambda-access
  apiGroup: rbac.authorization.k8s.io

```
  

**Testing**
-----------

There are some unit tests which exists, and it can be invoked by:
> pipenv shell pytest .

If you don't want to be bothered with the pipenv setup and rather would can use docker like:
> ./opts/test.sh

The end to end functioniality can be tested locally using the following command:

> serverless invoke local -f deploy -p test.json

whereas test.json can be as follows:

```json
{
  "RequestType": "Create",
  "ResponseURL": "https://pre-signed-s3-url-that-cloud-formation-generates",
  "StackId": "arn:aws:cloudformation:eu-west-1:123456789012:stack/MyStack/guid",
  "RequestId": "unique id for this create request",
  "ResourceType": "Custom::TestResource",
  "LogicalResourceId": "MyTestResource",
  "ResourceProperties": {
    "yaml": "---\n{apiVersion: v1,kind: Namespace, metadata: { annotations: {}, labels: {}, name: nightly}}\n---\n{apiVersion: apps/v1, kind: StatefulSet, metadata: {name: mysqldb, labels: {app: mysqldb}}, spec: {replicas: 1, selector: {matchLabels: {app: mysqldb}}, template: {metadata: {labels: {app: mysqldb}}, spec: {containers: [{name: mysqldb, image: 'mysql:latest', ports: [{containerPort: 3306, name: mysql}]}]}}}}",
    "namespace": "nightly"
  }
}
```

The above example mimics a Cloudformation Create action and deploys a mysql service into the kubernetes cloud into a custom namespace. Note: change the ResponseURL to a valid HTTP endpoint which accepts a POST.
