import boto3

session = boto3.Session()
creds = session.get_credentials()
print(f"export AWS_ACCESS_KEY_ID=\"{creds.access_key}\"\n "
      f"export AWS_SECRET_ACCESS_KEY=\"{creds.secret_key}\"\n "
      f"export AWS_SESSION_TOKEN=\"{creds.token}\"\n")
