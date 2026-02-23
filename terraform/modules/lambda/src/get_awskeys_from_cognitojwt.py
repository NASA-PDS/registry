import json
import boto3
import os
import sys
import time
import requests
from jose import jwt, jwk
from jose.utils import base64url_decode
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Initialize AWS Cognito Idenity Provider (IdP) and Cognito Identity clients
    cognito_idp_client = boto3.client('cognito-idp')
    cognito_identity_client = boto3.client('cognito-identity')

    # Environment variables for Cognito User Pool ID, Identity Pool ID, allowed cognito user groups (comma-separated values)
    # and Token signing Key URL for validation
    COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
    COGNITO_IDENTITY_POOL_ID = os.environ['COGNITO_IDENTITY_POOL_ID']
    COGNITO_ALLOWED_GROUPS = os.environ['COGNITO_ALLOWED_GROUPS']
    COGNITO_JWKS_URL = os.environ['COGNITO_JWKS_URL']

    # Extract tokens from the HTTP headers
    access_token = event['headers'].get('Authorization')
    id_token = event['headers'].get('IDToken')
    print(access_token)
    print(id_token)
    # If no tokens are provided, assume the default read-only role
    if not access_token or not id_token:
        return {
            'statusCode': 401,
            'body': json.dumps('Unauthorized: Invalid Credentials.')
        }

    # Strip Bearer prefix
    if access_token.startswith("Bearer "):
        access_token = access_token.split(" ")[1]

    # Token Verification
    valid_token = validate_jwt_token(id_token, COGNITO_JWKS_URL)
    if not valid_token:
        return {
            'statusCode': 401,
            'body': json.dumps('Unauthorized: Invalid JWT Token.')
        }

    try:
        # Retrive user information using the access token
        user_info = cognito_idp_client.get_user(AccessToken=access_token)
        username = user_info['Username']

        # List the groups the user belongs to
        user_groups = cognito_idp_client.admin_list_groups_for_user(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=username
        )['Groups']

        # Check if user is part of any allowed groups
        if not user_groups or not any(group['GroupName'] in COGNITO_ALLOWED_GROUPS for group in user_groups):
            return {
                'statusCode': 403,
                'body': json.dumps('Unauthorized: Your user is not part of any read-write groups!')
            }

        # Get the role ARN associated with the user's group
        role_arn = get_role_arn_for_group(user_groups)
        print(role_arn)
        identity_id_response = cognito_identity_client.get_id(
            IdentityPoolId=COGNITO_IDENTITY_POOL_ID,
            Logins={
                f'cognito-idp.us-west-2.amazonaws.com/' + COGNITO_USER_POOL_ID: id_token
            }
        )
        identity_id = identity_id_response['IdentityId']

        # Get temporary creds for AWS
        credentials = get_cognito_credentials(identity_id, id_token, COGNITO_USER_POOL_ID)
        print(credentials)
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

    # Return the creds in response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'AccessKeyId': credentials['AccessKeyId'],
            'SecretAccessKey': credentials['SecretKey'],
            'SessionToken': credentials['SessionToken']
        })
    }


# Retrive the role ARN from the user's group
def get_role_arn_for_group(groups):
    for group in groups:
        if 'RoleArn' in group:
            return group['RoleArn']
    return None


# Retrieve temp AWS credentials for a Cognito Idenity
def get_cognito_credentials(identity_id, id_token, COGNITO_USER_POOL_ID):
    try:
        cognito_identity_client = boto3.client('cognito-identity')
        response = cognito_identity_client.get_credentials_for_identity(
            IdentityId=identity_id,
            Logins={
                f'cognito-idp.{COGNITO_USER_POOL_ID.split("_")[0]}.amazonaws.com/' + COGNITO_USER_POOL_ID: id_token
                # 'cognito-idp.us-west-2.amazonaws.com/' + COGNITO_USER_POOL_ID: id_token
            }
        )

        credentials = response.get('Credentials', {})
        if not credentials:
            raise KeyError("Credentials not found in the response.")

        return credentials

    except ClientError as e:
        raise RuntimeError(f"Error retrieving credentials: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")


# Validate JWT Token
def validate_jwt_token(token, JWSK_URL):
    try:
        # Download the JWSK
        response = requests.get(JWSK_URL)
        if response.status_code != 200:
            raise ValueError("Unable to download JWSK")

        jwsk = response.json()
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']

        # Search for the kid in the downloaded JWSK
        public_key = None
        for key in jwsk['keys']:
            if kid == key.get('kid', ''):
                public_key = jwk.construct(key)
                break

        if public_key is None:
            raise ValueError("No keys found in JWSK.")

        # Decode the JWT
        message, encoded_signature = str(token).rsplit('.', 1)
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))

        if not public_key.verify(message.encode('utf-8'), decoded_signature):
            return False

        # Decode the token and validate claims
        claims = jwt.decode(token, public_key, algorithms=['RS256'], options={"verify_aud": False})
        if 'exp' in claims and claims['exp'] < int(time.time()):
            raise ValueError("Token has expired")

        return True

    except ClientError as e:
        raise RuntimeError(f"Error validating credentials: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")