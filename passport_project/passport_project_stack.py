from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
)
from constructs import Construct


class PassportProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # IAM role with permissions to access DynamoDB and CloudWatch
        role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonDynamoDBFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchFullAccessV2"
                ),
            ],
        )

        # DynamoDB table
        queries_table = dynamodb.Table(
            self,
            "QueriesTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            table_name="queries",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Use RETAIN for production
        )

        # Lambda function (code in lambda directory)
        lambda_function = lambda_.Function(
            self,
            "PassportBackendFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset("lambda"),
            handler="index.lambda_handler",
            role=role,
            environment={
                "QUERIES_TABLE_NAME": queries_table.table_name,
            },
        )

        # Grant the Lambda function permissions to write to the DynamoDB table
        queries_table.grant_write_data(lambda_function)

        # API Gateway REST API
        api = apigateway.RestApi(self, "PassportServerlessAPI")

        # Define API Gateway resources and methods
        query_resource = api.root.add_resource("queries")

        # Enable CORS for the resource
        query_resource.add_method(
            "GET", 
            apigateway.LambdaIntegration(lambda_function),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    },
                )
            ]
        )

        query_resource.add_method(
            "POST", 
            apigateway.LambdaIntegration(lambda_function),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True
                    },
                )
            ]
        )

        # Add CORS to the OPTIONS method for preflight requests
        query_resource.add_method(
            "OPTIONS",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,GET,POST'"
                        },
                    )
                ],
                passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_MATCH,
                request_templates={"application/json": '{"statusCode": 200}'},
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                    },
                )
            ],
        )
