from mysql.connector import connect

class mySqlConnection():

    def __init__(self, host, port, username, password, db):
        try:
            self.myDb = connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=db
            )
            print("**********Connected to MySQL DB**********")
            
        except Exception as e:
            print(e)
            if self.myDb is not None:
                self.myDb.close()

    def execute_query(self, query):
        try:
            cursor = self.myDb.cursor()
            cursor.execute(query)
            
            # Commit the transaction if it's an INSERT, UPDATE, or DELETE query
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                self.myDb.commit()
                print("**********Query Executed and Changes Committed Successfully**********")
                results = cursor.lastrowid
            else:
                results = cursor.fetchall()
                print("---Query Executed Successfully--- "+query)
            return results
        except Exception as e:
            raise Exception("mySQL:execute_query:"+str(e))
