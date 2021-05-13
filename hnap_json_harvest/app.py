import os
import json
import requests
import boto3
import smart_open
import urllib.request
import xml.dom.minidom
import logging
import datetime

from botocore.exceptions import ClientError
from xml.dom import minidom

def lambda_handler(event, context):
    """
    AWS Lambda Entry
    """
    print(event)
    
    """PROD SETTINGS"""
    #base_url = "https://maps.canada.ca/geonetwork"
    #gn_q_query = "/srv/eng/q"
    #gn_change_api_url = "/srv/api/0.1/records/status/change"
    #gn_json_record_url = "/srv/api/0.1/records"
    #bucket_location = "ca-central-1"
    #bucket = "hnap-test-bucket"
    
    """DEV SETTINGS"""
    base_url = "https://hnap-harv-bucket.s3.amazonaws.com"
    gn_q_query = "/q_xml_small.xml"
    gn_change_api_url = "/change.json"
    gn_json_record_url = "https://open.canada.ca/data/api/action/package_show?id="
    bucket_location = None
    bucket = "hnap-test-bucket1"
    
    """ 
    Used for `sam local invoke -e payload.json` for local testing
    For actual use, comment out the two lines below 
    """
    
    if "body" in event:
        event = json.loads(event["body"])
        
    """ 
    Parse query string parameters 
    """
        
    try:
        runtype = event["queryStringParameters"]["runtype"]
    except:
        runtype = False
        
    try:
        if datetime_valid(event["queryStringParameters"]["fromDateTime"]):
            fromDateTime = event["queryStringParameters"]["fromDateTime"]
        else:
            fromDateTime = False
    except:
        fromDateTime = False
    
    """ 
    Construct the body of the response object 
    """
    
    if runtype and fromDateTime:
        message = "Cannot use runtype and fromDateTime together"
    elif runtype == "full":
        message = "Reloading all JSON records..."
        uuid_list = get_full_uuids_list(base_url + gn_q_query)
        err_msg = harvest_uuids(uuid_list, gn_json_record_url, bucket, bucket_location)

    elif fromDateTime:
        message = "Reloading JSON records from: " + fromDateTime + "..."
        uuid_list = get_fromDateTime_uuids_list(base_url + gn_change_api_url, fromDateTime)
        err_msg = harvest_uuids(uuid_list, gn_json_record_url, bucket, bucket_location)
    else:
        fromDateTime = datetime.datetime.utcnow().now() - datetime.timedelta(minutes=11)
        fromDateTime = fromDateTime.isoformat()[:-7] + 'Z'
        message = "Default setting. Harvesting JSON records from: " + fromDateTime + "..."
        uuid_list = get_fromDateTime_uuids_list(base_url + gn_change_api_url, fromDateTime)
        err_msg = harvest_uuids(uuid_list, gn_json_record_url, bucket, bucket_location)
        
    if not err_msg:
        message += "..." + str(len(uuid_list)) + " record(s) harvested into " + bucket
    else:
        message += "... some error occured. View logs"
            
    response = {
        "statusCode": "200",
        "headers": {"Content-type": "application/json"},
        "body": json.dumps(
            {
                "statusCode": "200",
                "message": message,
                
            },
            indent = 4
        ),
    }
    return response

def datetime_valid(dt_str):
    """
    Check to see if user supplied a valid datetime 
    in ISO:8601 UTC time with +00:00 or 'Z' 
    https://stackoverflow.com/a/61569783
    
    """
    try:
        datetime.datetime.fromisoformat(dt_str)
    except:
        try:
            datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            print("fromDateTime is not a valid ISO:8601 UTC datetime with +00:00 or 'Z' ")
            return False
        return True
    return True
    
def convert_to_datetime(dt_str):
    """
    Check to see if user supplied a valid datetime 
    in ISO:8601 UTC time with +00:00 or 'Z' 
    https://stackoverflow.com/a/61569783
    
    """
    
    try:
        dt_str = datetime.datetime.fromisoformat(dt_str)
    except:
        try:
            dt_str = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            print("fromDateTime is not a valid ISO:8601 UTC datetime with +00:00 or 'Z' ")
            return False
        return dt_str
    return dt_str
    
def get_full_uuids_list(gn_q_query):
    """ Get a full list of all uuids
    :param gn_q_query: URL of the GeoNetwork 'q' search
    See https://geonetwork-opensource.org/manuals/3.10.x/en/api/q-search.html
    :return: a full list of uuids to harvest
    """
    
    uuid_list = []
    
    try:
        str_data = urllib.request.urlopen(gn_q_query).read()
        xmldoc = minidom.parseString(str_data)
        
        metadatas = xmldoc.getElementsByTagName("metadata")
        print("XML has: %i metadata records" % len(metadatas))
        
        for metadata in metadatas:
            uuid = metadata.getElementsByTagName("uuid")[0]
            uuid_list.append(uuid.firstChild.data)
        
        return uuid_list
    except:
        print("Could not load the GeoNetwork 3.6 'q' search.")
        print("Cannot complete a full load of the dataset")
        print("Could not access: ", gn_q_query)
        return uuid_list
        
def get_fromDateTime_uuids_list(gn_change_query, fromDateTime):
    """ Get a list of insert/deleted/modified uuids from fromDateTime
    :param gn_change_query: URL of the GeoNetwork change api
    :param fromDateTime: datetime of when to harvest
    :return: a list of uuids to harvest
    """
    
    uuid_list = []
    
    try:
        #Use the build in fromDateTime functionality in the GN change API
        #TO TEST gn_change_query = gn_change_query + "?fromDateTime=" + fromDateTime
        
        str_data = json.loads(urllib.request.urlopen(gn_change_query).read())
        #print (str_data['records'])
        
        for metadata in str_data['records']:
            lastdatetime = metadata['lastModifiedTime']
            if convert_to_datetime(lastdatetime) >= convert_to_datetime(fromDateTime):
                uuid = metadata['uuid']
                uuid_list.append(uuid)
            
        print("Using the fromDateTime provided: %s, there are: %i metadata records to harvest" % (fromDateTime, len(uuid_list)))
            
        return uuid_list
    except:
        print("Could not load the GeoNetwork 3.6 change api.")
        print("Cannot complete a load of the dataset")
        print("Could not access or properly parse: ", gn_change_query)
        return uuid_list
    
def create_bucket(bucket_name, region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_json_file(file_name, bucket, json_data, object_name=None):
    """Upload a json file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param json_data: stream of json data to write
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3 = boto3.resource('s3')
    try:
        s3object = s3.Object(bucket, file_name)
        response = s3object.put(Body=(bytes(json.dumps(json_data.decode('utf-8')).encode('UTF-8'))))
    except ClientError as e:
        logging.error(e)
        return False
    return True

def harvest_uuids(uuid_list, gn_json_record_url, bucket, bucket_location):
    """ Harvests GeoNetwork JSON file into s3_bucket_name
    
    :param uuid_list: list of uuids to upload
    :param gn_json_record_url: base path to the geonetwork record api
    :param bucket: bucket to upload to
    :return: accumulated error messages
    """
    
    error_msg = None
    
    if create_bucket(bucket, bucket_location):
        count = 0
        for uuid in uuid_list:
            try:
                uuid_filename = uuid + ".json"
                #print(gn_json_record_url + uuid)
                str_data = urllib.request.urlopen(gn_json_record_url + uuid).read()
                if upload_json_file(uuid_filename, bucket, str_data):
                    count += 1
            except ClientError as e:
                logging.error(e)
                error_msg += e
        print("Uploaded", count, " records")
    else:
        error_msg = "Could not create S3 bucket: " + bucket

    return error_msg