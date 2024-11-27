import boto3
import json
import logging
import uuid
from botocore.exceptions import ClientError

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB client
dynamodb = boto3.resource("dynamodb")
table_name = "queries"  # Use the same name as in the stack
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Lambda handler for managing API Gateway requests.
    """
    logger.info("Event: %s", event)

    http_method = event.get("httpMethod")
    path = event.get("path")

    # Handle POST /queries
    if http_method == "POST" and path == "/queries":
        return handle_post(event)

    # Default response for unsupported paths or methods
    return {
        "statusCode": 404,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"message": "Not Found"}),
    }


def handle_post(event):
    """
    Handles POST requests to the /queries endpoint.
    """
    try:
        # Parse the request body
        body = json.loads(event["body"])
        name = body.get("name")
        email = body.get("email")
        query = body.get("query")

        if not name or not email or not query:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"message": "All fields are required: name, email, query."}
                ),
            }

        # Generate a unique ID for the query
        query_id = str(uuid.uuid4())

        # Save the query to DynamoDB
        table.put_item(
            Item={
                "id": query_id,
                "name": name,
                "email": email,
                "query": query,
            }
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"message": "Query submitted successfully.", "id": query_id}
            ),
        }

    except ClientError as e:
        logger.error("DynamoDB error: %s", e.response["Error"]["Message"])
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Internal Server Error"}),
        }

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Internal Server Error"}),
        }
