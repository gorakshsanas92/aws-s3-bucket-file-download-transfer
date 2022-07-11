from celery import shared_task
from common.views import connection, target_db_connection
import datetime
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def insert_last_inserted_id(cursor, target_cursor):
    cursor.execute("SELECT id from models ORDER BY id DESC LIMIT 1")
    lastInsertedId = cursor.fetchone()
    cursor.execute("INSERT INTO last_inserted_id (id) VALUES (%s)", (lastInsertedId[0], ))
    target_cursor.commit()

def get_last_inserted_id(cursor, target_cursor):
    cursor.execute("SELECT id from last_inserted_id ORDER BY id DESC LIMIT 1")
    lastInsertedId = cursor.fetchone()
    if lastInsertedId:
        return lastInsertedId
    return None

def get_record(arg, cursor2):
    cursor2.execute(f'SELECT * FROM models where id = {arg[0]}')
    recordFound = cursor2.fetchone()
    if not recordFound:
        return arg


@shared_task
def get_records(flag=True, start=0, end=5):

    try:
        if flag:

            # db connection
            transfer_cursor = connection()
            target_cursor = target_db_connection()

            # Create cursor
            cursor = transfer_cursor.cursor()
            cursor2 = target_cursor.cursor()

            lastId = get_last_inserted_id(cursor2, target_cursor)

            # Get records
            if lastId:
                cursor.execute(f'''
                    SELECT * FROM models WHERE id > {lastId[0]} ORDER BY id DESC LIMIT {end} OFFSET {start}
                ''')
            else:
                cursor.execute(f'''
                    SELECT * FROM models ORDER BY id DESC LIMIT {end} OFFSET {start}
                ''')

            result = cursor.fetchall()
            args = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", get_record(i, cursor2)).decode('utf-8')
                        for i in result)

            if result:
                # sql = """
                #         INSERT INTO models 
                #             (id, user_id, upload_user_id, token, bucket, meta, created_at, updated_at) 
                #         VALUES 
                #             (%s,%s,%s,%s,%s,%s,%s,%s)
                #     """
                # for record in result:
                #     # Check Record Exist 
                #     cursor2.execute(f'SELECT * FROM models where id = {record[0]}')
                #     recordFound = cursor2.fetchone()

                #     if not recordFound:
                #         cursor2.execute(sql, record)
                #         target_cursor.commit()

                cursor2.execute("INSERT INTO models VALUES " + (args))
                target_cursor.commit()

                get_records(flag=True, start=start+end, end=5)

            else:
                
                insert_last_inserted_id(cursor2, target_cursor)
                get_records(flag=False)

        return "Done"
    
    except Exception as e:

        insert_last_inserted_id(cursor2, target_cursor)

        logger.warning('Error:'+str(datetime.datetime.now())+':'+str(e))
        return e
        
