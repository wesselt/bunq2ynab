# bunq2ynab Deployment Guide

This guide provides instructions on how to deploy the `bunq2ynab` application using the AWS Serverless Application Model (SAM) CLI. Before proceeding, ensure you meet all prerequisites.

## Prerequisites

- **AWS Account**: Ensure you have an AWS account. If you do not have one, sign up at [https://aws.amazon.com](https://aws.amazon.com).
- **AWS CLI**: The AWS Command Line Interface (CLI) must be installed and configured on your system.
- **AWS SAM CLI**: The AWS Serverless Application Model (SAM) CLI must be installed on your system.

### Installing AWS CLI

Follow the instructions at [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) to install the SAM CLI on your operating system. Or follow below:


To install the AWS CLI on a Linux or macOS system, use the following commands, I put them in the `/opt/` folder:

```sh
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

After installation, configure the AWS CLI with your credentials:

```sh
aws configure
```

Enter your AWS Access Key ID, Secret Access Key, and default region when prompted.

### Installing AWS SAM CLI

Follow the instructions at [AWS SAM CLI Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) to install the SAM CLI on your operating system.

## Deploying bunq2ynab

Once the prerequisites are installed and configured, follow these steps to deploy the `bunq2ynab` application.

1. **Clone the Repository**

   If you haven't already, clone the `bunq2ynab` repository to your local machine:

   ```sh
   git clone https://github.com/wesselt/bunq2ynab.git
   cd bunq2ynab
   ```

3. **Remove the Metadata block**

   To deploy it as your own you will need to remove the Metadata block from the `template.yaml` file
   
   ```yaml
    Metadata:
        AWS::ServerlessRepo::Application:
            Name: bunq-ynab-aws-lambda
            Description: Desc
            Author: Wessel Troost and Javy de Koning and Nick Strijbos
            ReadmeUrl: README.md
            SpdxLicenseId: GPL-2.0-only
            LicenseUrl: LICENSE
            Labels: ["Bunq", "Ynab"]
            HomePageUrl: https://github.com/wesselt/bunq2ynab
            SemanticVersion: 0.0.0
            SourceCodeUrl: https://github.com/wesselt/bunq2ynab
    ```

2. **Build the Application**

   Use the SAM CLI to build your application:
   >With the `--use-container` flag you will need Docker

   ```sh
   sam build --use-container
   ```

3. **Deploy the Application**

   Deploy your application to AWS using the SAM CLI. This step will package and deploy your application to AWS, creating all the necessary resources.

   ```sh
   sam deploy --guided
   ```

   Follow the prompts in the guided deployment process. You will be asked to specify a stack name, AWS region, and any parameters required by your template. You can also choose whether to allow SAM CLI to create IAM roles for your application.

4. **Verify Deployment**

   Once deployment is complete, verify that the application is functioning as expected. You can use the AWS Management Console or AWS CLI to check the resources created by the SAM deployment.
