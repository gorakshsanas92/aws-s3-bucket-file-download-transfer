from django.shortcuts import render
from django.http import JsonResponse
import os
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

# Create your views here.

def bucket(request):
    bucket_list = get_buckets_client()
    
    context = {
        "bucket_list": bucket_list
    }
    return render(request, 'bucket/index.html', context)


def create_session():
    # stores configuration state and allows you to create service clients and resources.
    session = boto3.session.Session(
        aws_access_key_id="aws_access_key_id", 
        aws_secret_access_key="aws_secret_access_key"
    )

    return session

# Get bucket list
def get_buckets_client():
    session =create_session()
    s3_client = session.client('s3')
    try:
        response = s3_client.list_buckets()
        buckets =[]
        for bucket in response['Buckets']:
            buckets += {bucket["Name"]}

    except ClientError:
        print("Couldn't get buckets.")
        raise
    else:
        return buckets


# Get perticular bucket files
def get_bucket_files(request, bucket_name):
    session =create_session()
    #Then use the session to get the resource
    s3 = session.resource('s3')
    my_bucket = s3.Bucket(bucket_name)
    bucket_files = []
    for my_bucket_object in my_bucket.objects.all():
        bucket_files.append({
            "name": my_bucket_object.key
        })
    
    return JsonResponse({ "files": bucket_files })


# Download bucket file
def download_bucket_file(request):
    if request.method == "POST":
        try:
            session =create_session()

            s3 = session.resource('s3')
            my_bucket = s3.Bucket(request.POST.get('bucket_name'))

            # Create folder with same name as bucket 
            isdir = os.path.isdir(f"media/{request.POST.get('bucket_name')}") 
            if not isdir:
                os.mkdir(f"media/{request.POST.get('bucket_name')}")
            
            # Create sub folders of buckets
            if '/' in request.POST.get('file_name'):
                string_array = request.POST.get('file_name').split('/')
                folder_path = f"media/{request.POST.get('bucket_name')}"
                for folder in string_array[0:-1]:
                    if not os.path.isdir(f"{folder_path}/{folder}"):
                        os.mkdir( f"media/{request.POST.get('bucket_name')}/{folder}")
                        folder_path += f"/{folder}"

            # Store file
            my_bucket.download_file(
                request.POST.get('file_name'),
                f"media/{request.POST.get('bucket_name')}/{request.POST.get('file_name')}"
            )

            return JsonResponse({ "status": "success", "message": "File downloaded successfully!" })

        except Exception as e:
                return JsonResponse({"status": "error","message": str(e)})


# Copy file from one bucket to another bucket
def copy_files(request):
    if request.method == "POST":
        try:
            #Creating S3 Resource From the Session.

            session = create_session()

            s3 = session.resource('s3')

            #Create a Soucre Dictionary That Specifies Bucket Name and Key Name of the Object to Be Copied
            copy_source = {
                'Bucket': request.POST.get('bucket_name'),
                'Key': request.POST.get('file_name')
            }

            bucket = s3.Bucket(request.POST.get('target_bucket_name'))

            bucket.copy(copy_source, request.POST.get('file_name'))

            # Printing the Information That the File Is Copied.
            return JsonResponse({"status": "success", "message": "Single File is copied"})
        
        except Exception as e:
            return JsonResponse({"status": "error","message": str(e)})
    