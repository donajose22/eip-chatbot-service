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
            print("*****************************************")
            print("Connected to MySQL DB")
            
        except Exception as e:
            print(e)
            if self.myDb is not None:
                self.myDb.close()

    def execute_query(self, query):
        try:
            cursor = self.myDb.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            print("*****************************************")
            print("Query Executed Successfully")
            return results
        except Exception as e:
            raise Exception("mySQL:execute_query:"+str(e))