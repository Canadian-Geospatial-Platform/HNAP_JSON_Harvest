# HNAP JSON Harvesting Lambda

This AWS Lambda function harvests HNAP files in JSON format from the GeoNetwork v3.6 catalog and exports them into an S3 bucket.

## High-level description

Use an AWS cron to run every `10` minutes and overwrite any existing JSON files with the same UUID. Note: running every `10` minutes will overlap with 1). This is intentional and will capture an edge case where a Lambda cold start of a few milliseconds will not capture a full 10 minute window.

1) Default behaviour (no additional params in GET): use the GeoNetwork 'change' API to obtain a feed records that are new, modified, deleted or had their child/parent changed. This program will look backwards `11` minutes.

2) Special case: reload all JSON records
    `?runtype=full`

2.1) Special case: insert a specific JSON record

    `?runtype=insert_uuid&uuid=$SOME_UUID`

2.2) Special case: delete a specific JSON record

    `?runtype=delete_uuid&uuid=$SOME_UUID`

3.1) Special case: load all records since a specific dateTime in ISO 8601

    `?fromDateTime=yyyy-MM-ddTHH:mm:ssZ`

    E.g., `?fromDateTime=2021-04-29T00:00:00Z`

3.2) Special case: load all records up to a specific dateTime in ISO 8601

    `?toDateTime=yyyy-MM-ddTHH:mm:ssZ`

    E.g., `?toDateTime=2021-04-29T00:00:00Z`

3.3) Special case: load all records between specific dateTimes in ISO 8601

    `?fromDateTime=yyyy-MM-ddTHH:mm:ssZ&toDateTime=yyyy-MM-ddTHH:mm:ssZ`

    E.g., `?fromDateTime=2021-04-29T00:00:00Z&toDateTime=2021-09-29T00:00:00Z`

4) If GeoNetwork (https://maps.canada.ca/geonetwork) is inaccessible then exit.

Note: runtype and fromDateTime cannot be used together

## Deploy the HNAP JSON Harvesting Lambda application

To deploy to AWS Lambda, use Cloud9 and the Serverless Application Model Command Line Interface (SAM CLI). SAM CLI is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To build and deploy this application, we first need to create public-private ssh-key.

In the AWS Cloud9 bash shell:

### Step 1 - Generate SSH Key for Github

In the Cloud9 terminal:
`ssh-keygen -t rsa`
[Enter] [Enter] [Enter]
`cat /home/ec2-user/.ssh/id_rsa.pub`

Copy the string starting from `ssh-rsa` into you GitHub account > Settings > SSH and GPG keys > New SSH key > Title: Any title > Key: copied key > Add SSH Key

### Step 2 - Clone the repo

Clone this project to Cloud9 from the bash shell:

`git clone git@github.com:Canadian-Geospatial-Platform/HNAP_JSON_Harvest.git`

### Step 3 - Build and test the application

Build the application

```bash
cd HNAP_JSON_Harvest
sam build
```

Test the build using the `payload.json` file included in the 'events' folder. 

Hint: remove the underscore '_' to get desired behaviour
```json
{
    "queryStringParameters":
    {
        "_runtype": "full",
        "_verbose": "true",
	"_uuid": 8b882aa3-f8ef-4d88-8541-059260e04e4a,
        "_fromDateTime": "2021-05-04T00:00:00Z",
        "_toDateTime": "2021-12-30T12:14:45Z"
    }
}
```

```bash
sam local invoke -e payload.json
```

The response should appear similar to:
```bash
{'queryStringParameters': {'_runtype': 'full', 'fromDateTime': '2008-08-30T01:45:36.123Z'}}
XML has: 5 metadata records
Uploaded 5  records
END RequestId: -ID-
REPORT RequestId: -ID-  Init Duration: 1.02 ms  Duration: 2137.28 ms    Billed Duration: 2200 ms        Memory Size: 128 MB    Max Memory Used: 128 MB
{"statusCode": "200", "headers": {"Content-type": "application/json"}, "body": "{\n    \"statusCode\": \"200\",\n    \"message\": \"Reloading all JSON records......5 record(s) harvested into SOME_BUCKET\"\n}
```

### Step 4 - Create an Amazon Elastic Container Registry

Go to the Amazon ECR service and press "Create repository" and create a new Private ECR. The URI similar to "XYZ.dkr.ecr.us-east-1.amazonaws.com/your_ECR_name" will be used in step 5 of deployment.

### Step 5 - Deploy to AWS

```bash
sam deploy --guided
```

Stack Name: hnap_json_harvest_yyyymmdd

AWS Region: ca-central-1

Image Repository: Image ECR URI from Step 4

Confirm: y
Confirm: y
Confirm: y
Confirm: y
[Enter]
[Enter]

After this, sam will build the CloudFormation stack and deploy the ECR.

```
CloudFormation stack changeset
-------------------------------------------------------------------------------------------------------------------------
Operation                      LogicalResourceId              ResourceType                   Replacement                  
-------------------------------------------------------------------------------------------------------------------------
+ Add                          HnapJsonHarvestFunctionHnapJ   AWS::Lambda::Permission        N/A                          
                               sonHarvestPermissionProd                                                                   
+ Add                          HnapJsonHarvestFunctionRole    AWS::IAM::Role                 N/A                          
+ Add                          HnapJsonHarvestFunction        AWS::Lambda::Function          N/A                          
+ Add                          ServerlessRestApiDeployment7   AWS::ApiGateway::Deployment    N/A                          
+ Add                          ServerlessRestApiProdStage     AWS::ApiGateway::Stage         N/A                          
+ Add                          ServerlessRestApi              AWS::ApiGateway::RestApi       N/A                          
-------------------------------------------------------------------------------------------------------------------------
```

A final question will ask if you want to deploy the changeset.

Confirm: y

```
CloudFormation events from changeset
-------------------------------------------------------------------------------------------------------------------------
ResourceStatus                 ResourceType                   LogicalResourceId              ResourceStatusReason         
-------------------------------------------------------------------------------------------------------------------------
CREATE_IN_PROGRESS             AWS::IAM::Role                 HnapJsonHarvestFunctionRole    -                            
CREATE_IN_PROGRESS             AWS::IAM::Role                 HnapJsonHarvestFunctionRole    Resource creation Initiated  
CREATE_COMPLETE                AWS::IAM::Role                 HnapJsonHarvestFunctionRole    -                            
CREATE_IN_PROGRESS             AWS::Lambda::Function          HnapJsonHarvestFunction        -                            
CREATE_IN_PROGRESS             AWS::Lambda::Function          HnapJsonHarvestFunction        Resource creation Initiated  
CREATE_COMPLETE                AWS::Lambda::Function          HnapJsonHarvestFunction        -                            
CREATE_IN_PROGRESS             AWS::ApiGateway::RestApi       ServerlessRestApi              -                            
CREATE_IN_PROGRESS             AWS::ApiGateway::RestApi       ServerlessRestApi              Resource creation Initiated  
CREATE_COMPLETE                AWS::ApiGateway::RestApi       ServerlessRestApi              -                            
CREATE_IN_PROGRESS             AWS::Lambda::Permission        HnapJsonHarvestFunctionHnapJ   Resource creation Initiated  
                                                              sonHarvestPermissionProd                                    
CREATE_IN_PROGRESS             AWS::ApiGateway::Deployment    ServerlessRestApiDeployment   -                            
                                                                                                                 
CREATE_IN_PROGRESS             AWS::Lambda::Permission        HnapJsonHarvestFunctionHnapJ   -                            
                                                              sonHarvestPermissionProd                                    
CREATE_IN_PROGRESS             AWS::ApiGateway::Deployment    ServerlessRestApiDeployment   Resource creation Initiated  
                                                                                                                 
CREATE_COMPLETE                AWS::ApiGateway::Deployment    ServerlessRestApiDeployment   -                            
                                                                                                                 
CREATE_IN_PROGRESS             AWS::ApiGateway::Stage         ServerlessRestApiProdStage     -                            
CREATE_IN_PROGRESS             AWS::ApiGateway::Stage         ServerlessRestApiProdStage     Resource creation Initiated  
CREATE_COMPLETE                AWS::ApiGateway::Stage         ServerlessRestApiProdStage     -                            
CREATE_COMPLETE                AWS::Lambda::Permission        HnapJsonHarvestFunctionHnapJ   -                            
                                                              sonHarvestPermissionProd                                    
CREATE_COMPLETE                AWS::CloudFormation::Stack     APP_NAME            -                            
-------------------------------------------------------------------------------------------------------------------------

CloudFormation outputs from deployed stack
---------------------------------------------------------------------------------------------------------------------------
Outputs                                                                                                                   
---------------------------------------------------------------------------------------------------------------------------
Key                 HnapJsonHarvestApi                                                                                    
Description         API Gateway endpoint URL for Prod stage for HNAP JSON Harvesting function                             
Value               **API PATH**               

Key                 HnapJsonHarvestFunctionIamRole                                                                        
Description         Implicit IAM Role created for HNAP JSON Harvesting function                                           
Value               **API_ARN**           

Key                 HnapJsonHarvestFunction                                                                               
Description         HNAP JSON Harvesting Lambda Function ARN                                                              
Value               **LAMBDA_ARN**                                                                                 
---------------------------------------------------------------------------------------------------------------------------
```
### Updating the microservice

`sam deploy`
or
`sam deploy --guided`

Should return: `Successfully created/updated stack - APP_NAME in ca-central-1`

### Deleting the microservice

`aws cloudformation delete-stack --stack-name <<stack-name>>`
    
### Converting AWS SAM template to CloudFormation template

Validate to ensure template.yaml is valid

```
sam validate
```
If the validate returns an error is detected, it may be necessary to specify the URI of the container image. 
In the template.yaml, add the ImageURI. E.g.,
```
Properties:
    PackageType: Image
          #ImageUri: XYZ.XYZ.XYZ.ca-central-1.amazonaws.com/CONTAINER-NAME
```

Install prerequisites libraries

```
pip install aws-sam-translator docopt
pip install pyyaml
git clone https://github.com/aws/serverless-application-model.git
pip install -r serverless-application-model/requirements/base.txt
pip install cfn-flip
```

First, convert the SAM template (yaml) to CF template (json). Note: there is currently no way to convert to yaml directly.

```
python serverless-application-model/bin/sam-translate.py --template-file=template.yaml --output-template=output.json
```

Next convert the CF template (json) to CF template (yaml). The output can be used to 

```
cfn-flip -i json -o yaml output.json output.yaml
```
    
