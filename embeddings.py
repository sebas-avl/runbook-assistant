import json
import os
from functools import cache

import boto3


@cache
def get_client():
    return boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])

def embed_text(text:str) -> list[float]:
    response = get_client().invoke_model(
        modelId = os.environ["EMBEDDING_MODEL_ID"],
        body = json.dumps({"inputText":text}),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]