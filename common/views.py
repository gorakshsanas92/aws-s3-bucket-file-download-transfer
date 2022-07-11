from django.shortcuts import render
import psycopg2


# Create database connection.
def connection():
    conn = psycopg2.connect(
        database="database_name", 
        user='username', 
        password='password', 
        host='host_name', 
        port= '5432'
    )

    return conn
    #Creating a cursor object using the cursor() method
    # return conn.cursor()


def target_db_connection():
    conn = psycopg2.connect(
        database="target_aws", 
        user='postgres', 
        password='Gaurav#1992', 
        host='127.0.0.1', 
        port= '5432'
    )

    return conn
    #Creating a cursor object using the cursor() method
    # return conn.cursor()
