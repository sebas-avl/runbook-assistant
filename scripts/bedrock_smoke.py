import json
import os

import boto3

REGION = os.environ["AWS_REGION"]
EMBEDDING_MODEL_ID = os.environ["EMBEDDING_MODEL_ID"]
TEXT_MODEL_ID = os.environ["TEXT_MODEL_ID"]

client = boto3.client("bedrock-runtime", region_name=REGION)

response = client.invoke_model(
    modelId=EMBEDDING_MODEL_ID,
    body=json.dumps({"inputText": "hello"}),
)

result = json.loads(response["body"].read())
print(len(result["embedding"]))

chat_response = client.converse(
    modelId=TEXT_MODEL_ID,
    messages=[{"role": "user", "content": [{"text": "Say hello in one short sentence."}]}],
)

print(chat_response["output"]["message"]["content"][0]["text"])