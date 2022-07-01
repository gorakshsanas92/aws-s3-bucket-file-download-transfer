from django.urls import path
from . import views

urlpatterns = [
    path('', views.bucket, name='bucket'),
    path('get-bucket-files/<str:bucket_name>', views.get_bucket_files, name='get-bucket-files'),
    path('download-bucket-file', views.download_bucket_file, 
        name='download-bucket-file'),
    path('copy-file', views.copy_files, name='copy-file'),
]
