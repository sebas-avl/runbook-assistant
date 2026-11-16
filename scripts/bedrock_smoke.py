import json
import os

import boto3

REGION = os.environ["AWS_REGION"]
EMBEDDING_MODEL_ID = os.environ["EMBEDDING_MODEL_ID"]

client = boto3.client("bedrock-runtime", region_name=REGION)

response = client.invoke_model(
    modelId=EMBEDDING_MODEL_ID,
    body=json.dumps({"inputText": "hello"}),
)

result = json.loads(response["body"].read())
print(len(result["embedding"]))