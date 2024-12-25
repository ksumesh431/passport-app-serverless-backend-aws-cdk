import boto3
import json
import logging
import uuid
import re
from botocore.exceptions import ClientError
from datetime import datetime, timezone

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
    return build_response(404, {"message": "Not Found"})


def build_response(status_code, body=None):
    """
    Helper function to build the standard API Gateway response with CORS headers.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # CORS header
        },
        "body": json.dumps(body),
    }


def is_valid_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone, country_code):
    """Validate phone number"""
    # Remove country code and any non-digit characters
    phone_digits = "".join(filter(str.isdigit, phone.replace(country_code, "")))
    return len(phone_digits) == 10 and phone_digits.isdigit()


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
        phone = body.get("phone")
        country_code = body.get("countryCode")
        category = body.get("category")
        subcategory = body.get("subCategory")  # Note: Changed from sub-category

        if not all([name, email, query, phone, country_code, category, subcategory]):
            return build_response(400, {"message": "All fields are required"})

        # Validate email
        if not is_valid_email(email):
            return build_response(400, {"message": "Invalid email format"})

        # Validate phone
        if not is_valid_phone(phone, country_code):
            return build_response(400, {"message": "Invalid phone number format"})

        # Generate a unique ID for the query
        query_id = str(uuid.uuid4())

        # Get current timestamp in ISO format using timezone-aware datetime
        timestamp = datetime.now(timezone.utc).isoformat()

        # Save the query to DynamoDB
        table.put_item(
            Item={
                "id": query_id,
                "name": name,
                "email": email,
                "query": query,
                "phone": f"{country_code}{phone}",
                "category": category,
                "subcategory": subcategory,
                "timestamp": timestamp
            }
        )

        return build_response(
            200, {"message": "Query submitted successfully.", "id": query_id}
        )

    except ClientError as e:
        logger.error("DynamoDB error: %s", e.response["Error"]["Message"])
        return build_response(500, {"message": "Internal Server Error"})

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return build_response(500, {"message": "Internal Server Error"})
