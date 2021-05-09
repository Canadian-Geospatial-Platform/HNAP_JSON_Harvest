# HNAP JSON Harvesting Lambda

This AWS Lambda function harvests HNAP files in JSON format from the GeoNetwork v3.6 catalog and exports them into an S3 bucket.

## High-level description

Use an AWS cron to run every `10` minutes and overwrite any existing JSON files with the same UUID. Note: running every `10` minutes will overlap with 1). This is intentional and will capture an edge case where a Lambda cold start of a few milliseconds will not capture a full 10 minute window.

1) Default behaviour (no additional params in GET): use the GeoNetwork 'change' API to obtain a feed records that are new, modified, deleted or had their child/parent changed. This program will look backwards `11` minutes.

2) Special case: reload all JSON records
    `?runtype=full`

3) Special case: load all records since a specific dateTime using ISO 8601
    `?fromDateTime=yyyy-MM-ddTHH:mm:ssZ`

    E.g., `?fromDateTime=2021-04-29T00:00:00Z`

4) If GeoNetwork (https://maps.canada.ca/geonetwork) is inaccessible then exit.

Note: runtype and fromDateTime cannot be used together

## Deploy the HNAP JSON Harvesting Lambda application

To deploy to AWS Lambda, use Cloud9 and the Serverless Application Model Command Line Interface (SAM CLI). SAM CLI is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To build and deploy this application, we first need to create public-private ssh-key.

In the AWS Cloud9 bash shell:

### Step 1 - Generate SSH Key for Github

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
sam build
```

Test the build using the `payload.json` file included in the hnap_json_harvest folder

```bash
sam local invoke -e payload.json
```
### Step 4 - Create an Amazon Elastic Container Registry

`todo`

### Step 5 - Deploy to AWS

```bash
sam deploy --guided
```

Stack Name: hnap_json_harvest_yyyymmdd
AWS Region: `todo`
Image Repository: Image ECR URI from Step 4

Confirm: y
Confirm: y
Confirm: y
Confirm: y
[Enter]
[Enter]

