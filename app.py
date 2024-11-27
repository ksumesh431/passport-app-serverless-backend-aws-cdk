#!/usr/bin/env python3
import os

import aws_cdk as cdk

from passport_project.passport_project_stack import PassportProjectStack


app = cdk.App()
PassportProjectStack(
    app,
    "PassportProjectStack",
    env=cdk.Environment(account="316770681739", region="ca-central-1"),
)

app.synth()
