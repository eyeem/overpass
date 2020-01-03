import boto3
import logging
import os
import yaml


LOGGER = logging.getLogger(__name__)


def create_kube_config(kube_filepath, eks_api, cluster_name, user_name='lambda'):
    # We assume that when the Lambda container is reused, a kubeconfig file exists.
    # If it does not exist, it creates the file.
    if not os.path.exists(kube_filepath):
        LOGGER.info(f"{kube_filepath} not present. Creating one")
        # Get data from EKS API
        cluster_info = eks_api.describe_cluster(name=cluster_name)
        LOGGER.debug("describe_cluster API call finished")
        certificate = cluster_info['cluster']['certificateAuthority']['data']
        endpoint = cluster_info['cluster']['endpoint']
        LOGGER.debug("Got the cluster information")

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
                        'user': user_name
                    },
                'name': 'lambda'
            }]

        kube_content['current-context'] = 'lambda'
        kube_content['Kind'] = 'config'
        kube_content['users'] = [
            {
                'name': user_name,
                'user': {
                    'name': user_name
                }
            }]

        # Write kubeconfig
        with open(kube_filepath, 'w') as outfile:
            LOGGER.debug(kube_content)
            yaml.dump(kube_content, outfile, default_flow_style=False)
        LOGGER.info(f"Done creating the {kube_filepath}")
