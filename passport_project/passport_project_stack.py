from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class PassportProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Create IAM role with permissions to access DynamoDB and CloudWatch
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

        # Create DynamoDB table
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

        # Create Lambda function
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

        # Create API Gateway REST API
        api = apigateway.RestApi(self, "PassportServerlessAPI")

        # Define API Gateway resources and methods
        query_resource = api.root.add_resource("queries")
        query_resource.add_method("GET", apigateway.LambdaIntegration(lambda_function))
        query_resource.add_method("POST", apigateway.LambdaIntegration(lambda_function))
