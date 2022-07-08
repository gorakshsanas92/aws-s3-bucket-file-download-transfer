from django.shortcuts import render
import psycopg2


# Create database connection.
def connection():
    conn = psycopg2.connect(
        database="d6epmn0ctf886k", 
        user='uaernok32on0g8', 
        password='p26ef991b2e1e5cb7b390d88eed2f9e2f34a22d2af99121591789b830ce1d5bb4', 
        host='ec2-3-218-160-76.compute-1.amazonaws.com', 
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
