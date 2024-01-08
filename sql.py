from decouple import config
import pymssql
import sys

server = config("PYMSSQL_SERVER")
user = config("PYMSSQL_USER")
passwd = config("PYMSSQL_PASSWORD")
db = config("PYMSSQL_DB")

class Connection:
    def __init__(self):
        self.server = server
        self.user = user
        self.passwd = passwd
        self.db = db
        self.connection = None
        self.cursor = None

    def make_connection(self, database=db):
        self.connection = pymssql.connect(server, user, passwd, database)
        self.cursor = self.connection.cursor(as_dict=True)

    def close_connection(self):
        self.connection.close()

    def find_user(self, email):
        if email == "":
            print("No email provided")
            return None
        if ("@realtelematics.co.za" not in email) and ("@realtimesolutions.co.za" not in email):
            return "not employee"
        else:
            self.make_connection()
            self.cursor.execute("SELECT * FROM tblusers WHERE email like %s", (email))
            user = self.cursor.fetchone()
            if user == None:
                print("No user found")
                return "no user"
            else:
                user = user['ID']
                self.close_connection()
                return user
    
    def find_permissions_by_user_id(self, id):
        if id == "":
            print("No ID provided")
            return None
        else:
            self.make_connection()
            self.cursor.execute("SELECT UserID, PermissionValue, Description FROM tblUserPermissions WHERE userID = %s", (id))
            permissions = self.cursor.fetchall()
            if permissions != []:
                return permissions
            else:
                self.close_connection()
                return None
            

    #7639 for prod, 6380 for dev jethro
    #1241 for prod, 2157 for dev user perms
    def update_permissions(self, id):
        self.make_connection()
        self.cursor.execute(f"""
                              Insert Into tblUserPermissions
                              Select 6380, {id}, AreaID, PermissionValue, [Description]
                              From tblUserPermissions Where UserID = 2157
                            """)
        if self.cursor.rowcount == 18:
            print("Permissions updated")
            self.connection.commit()
            self.close_connection()
            return True
        else:
            self.close_connection()
            print("Permissions not updated")
            return False

    def find_job(self, jobname):
        if jobname == "":
            print("No job name provided")
            return None
        else:
            self.make_connection(database="Qsmacker")
            self.cursor.execute(f"SELECT * FROM Job WHERE Description like '{jobname}'")
            job = self.cursor.fetchone()
            print(job)
            if job == None:
                print("No job found SQL")
                return None
            else:
                job = [job['id'], job['Description']]
                self.close_connection()
                return job
            
