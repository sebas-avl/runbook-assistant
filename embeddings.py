import json
import os
from functools import cache

import boto3
from botocore.config import Config


@cache
def get_client():
    config = Config(retries={"max_attempts": 10, "mode": "adaptive"})
    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ["AWS_REGION"],
        config=config,
    )

def embed_text(text:str) -> list[float]:
    response = get_client().invoke_model(
        modelId = os.environ["EMBEDDING_MODEL_ID"],
        body = json.dumps({"inputText":text}),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]