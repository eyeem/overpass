import base64
import re

import boto3
from botocore.signers import RequestSigner
from overpass.auth.auth_base import AuthBase


class AwsStsAuth(AuthBase):
    METHOD = 'GET'
    EXPIRES = 60
    EKS_HEADER = 'x-k8s-aws-id'
    EKS_PREFIX = 'k8s-aws-v1.'
    STS_URL = 'sts.amazonaws.com'
    STS_ACTION = 'Action=GetCallerIdentity&Version=2011-06-15'

    def __init__(self, cluster_id):
        self.cluster_id = cluster_id
        # For some stupid reason, the region has to be us-east-1 even though STS is region-agnostic :-/
        self.region = 'us-east-1'

    def get_token(self):
        """
        Return bearer token
        """
        session = boto3.session.Session()
        # Get ServiceID required by class RequestSigner
        client = session.client("sts", region_name=self.region)
        service_id = client.meta.service_model.service_id

        signer = RequestSigner(
            service_id,
            session.region_name,
            'sts',
            'v4',
            session.get_credentials(),
            session.events
        )

        params = {
            'method': self.METHOD,
            'url': 'https://' + self.STS_URL + '/?' + self.STS_ACTION,
            'body': {},
            'headers': {
                self.EKS_HEADER: self.cluster_id
            },
            'context': {}
        }

        signed_url = signer.generate_presigned_url(
            params,
            region_name=self.region,
            expires_in=self.EXPIRES,
            operation_name=''
        )
        return self.EKS_PREFIX + re.sub(r'=*', '', base64.urlsafe_b64encode(signed_url.encode('utf-8')).decode('utf-8'))
