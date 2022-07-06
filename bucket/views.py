import csv
import re
from django.shortcuts import render
from django.http import JsonResponse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import os
import tqdm
import boto3
from botocore.exceptions import ClientError

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


def get_bucket_files_array(bucket_name):
    session =create_session()
    #Then use the session to get the resource
    s3 = session.resource('s3')
    my_bucket = s3.Bucket(bucket_name)
    bucket_files = []
    for my_bucket_object in my_bucket.objects.all():
        bucket_files.append(my_bucket_object.key)
    
    return bucket_files


def create_directory(file_name, bucket_name):
    try:
        isdir = os.path.isdir(f"media/{bucket_name}") 
        if not isdir:
            os.mkdir(f"media/{bucket_name}")

        if '/' in file_name:
            string_array = file_name.split('/')
            folder_path = f"media/{bucket_name}"
            for folder in string_array[0:-1]:
                if(len(string_array) > 2):
                    if not os.path.isdir(f"{folder_path}/{folder}"):
                        os.mkdir(f"{folder_path}/{folder}")
                        folder_path += f"/{folder}"
                else:
                    if not os.path.isdir(f"{folder_path}/{folder}"):
                        os.mkdir(f"media/{bucket_name}/{folder}")
                        folder_path += f"/{folder}"

    except Exception as e:
        print("--->", e)



# Download bucket file
def download_bucket_file(request):
    if request.method == "POST":
        try:

            if request.POST.get('file_name') == "all":

                response = download_files(request.POST.get('bucket_name'))

                if response:
                    return JsonResponse({ "status": "success", "message": "Files downloaded successfully!" })

                return JsonResponse({"status": "error","message": "Something went wrong!"})

            else:
                # Download Single File 
                session = create_session()

                s3 = session.resource('s3')
                my_bucket = s3.Bucket(request.POST.get('bucket_name'))
                
                # Create folder
                create_directory(request.POST.get('file_name'), request.POST.get('bucket_name'))

                # Store file
                my_bucket.download_file(
                    request.POST.get('file_name'),
                    f"media/{request.POST.get('bucket_name')}/{request.POST.get('file_name')}"
                )

                return JsonResponse({ "status": "success", "message": "File downloaded successfully!" })

        except Exception as e:
                return JsonResponse({"status": "error","message": str(e)})



def download_one_file(bucket: str, client: boto3.client, s3_file: str):
    """
    Download a single file from S3
    Args:
        bucket (str): S3 bucket where images are hosted
        output (str): Dir to store the images
        client (boto3.client): S3 client
        s3_file (str): S3 object name
    """

    create_directory(s3_file, bucket)

    # my_bucket.download_file(
    #     s3_file,
    #     f"media/{bucket}/{s3_file}"
    # )

    client.download_file(
        Bucket=bucket, Key=s3_file, Filename=f"media/{bucket}/{s3_file}"
    )


def download_files(bucket_name):
    try:
        # Creating only one session and one client
        session = create_session()
        client = session.client("s3")

        files_to_download = get_bucket_files_array(bucket_name)
        
        # The client is shared between threads
        func = partial(download_one_file, bucket_name, client)

        # List for storing possible failed downloads to retry later
        failed_downloads = []

        with tqdm.tqdm(desc="Downloading images from S3", total=len(files_to_download)) as pbar:
            with ThreadPoolExecutor(max_workers=32) as executor:
                # Using a dict for preserving the downloaded file for each future, to store it as a failure if we need that
                futures = {
                    executor.submit(func, file_to_download, session): file_to_download for file_to_download in files_to_download
                }
                for future in as_completed(futures):
                    if future.exception():
                        failed_downloads.append(futures[future])
                    pbar.update(1)
        if len(failed_downloads) > 0:
            print("Some downloads have failed. Saving ids to csv")
            with open(
                os.path.join('media', "failed_downloads.csv"), "w", newline=""
            ) as csvfile:
                wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                wr.writerow(failed_downloads)
        
        return True

    except Exception as e:
        print(e)
        return False


def copy_one_file(bucket_name, client, file_name, target_bucket_name):
    
    try:
        copy_source = {
            'Bucket': bucket_name,
            'Key': file_name
        }

        bucket = client.Bucket(target_bucket_name)
        bucket.copy(copy_source, file_name)

        return True

    except Exception as e:
        print(e)
        return False



# Copy file from one bucket to another bucket
def copy_files(request):
    if request.method == "POST":
        #Creating S3 Resource From the Session.
        session = create_session()
        client = session.resource('s3')

        try:
            if request.POST.get('file_name') == "all":

                files_to_copy = get_bucket_files_array(request.POST.get('bucket_name'))

                func = partial(copy_one_file, request.POST.get('bucket_name'), client)

                failed_copys = []

                with tqdm.tqdm(
                    desc=f"Copy images from {request.POST.get('bucket_name')} to {request.POST.get('target_bucket_name')}", 
                    total=len(files_to_copy)) as pbar:
                    with ThreadPoolExecutor(max_workers=32) as executor:
                        # Using a dict for preserving the downloaded file for each future, to store it as a failure if we need that
                        futures = {
                            executor.submit(
                                func, 
                                file_to_copy, 
                                request.POST.get('target_bucket_name')
                            ): file_to_copy for file_to_copy in files_to_copy
                        }
                        for future in as_completed(futures):
                            if future.exception():
                                failed_copys.append(futures[future])
                            pbar.update(1)
                        
                if len(failed_copys) > 0:
                    print("Some copy have failed. Saving ids to csv")
                    with open(
                        os.path.join('media', "failed_copys.csv"), "w", newline=""
                    ) as csvfile:
                        wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                        wr.writerow(failed_copys)
                
                return JsonResponse({"status": "success", "message": "All Files are copied"})
                    
            else:

                #Create a Soucre Dictionary That Specifies Bucket Name and Key Name of the Object to Be Copied
                response = copy_one_file(
                    request.POST.get('bucket_name'), 
                    client, 
                    request.POST.get('file_name'), 
                    request.POST.get('target_bucket_name')
                )

                if response:
                    # Printing the Information That the File Is Copied.
                    return JsonResponse({"status": "success", "message": "Single File is copied"})
                
                else:
                    return JsonResponse({"status": "error","message": "Oops..Something went wrong!"})
        
        except Exception as e:
            return JsonResponse({"status": "error","message": str(e)})