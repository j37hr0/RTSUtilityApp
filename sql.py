from decouple import config
import pymssql
import sys

#TODO: refactor connection class methods into inherited classes for each app function

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

    def get_batches(self, job_id):
        if job_id == "":
            print("No job id provided")
            return None
        else:
            self.make_connection(database="Qsmacker")
            self.cursor.execute(f"SELECT * FROM RTUBatch WHERE JobID = {job_id} ORDER BY insertDate DESC")
            batches = self.cursor.fetchall()
            if batches == None:
                print("No batches found")
                return None
            else:
                self.close_connection()
                return batches

    def get_totals(self, job_id):
        if job_id == "":
            print("No job id provided")
            return None
        else:
            self.make_connection(database="Qsmacker")
            self.cursor.execute(f"SELECT distinct count(*) as 'Machines' FROM RTUBatch WHERE JobID = {job_id}")
            machineCount = self.cursor.fetchall()
            self.close_connection()
            self.make_connection(database="Qsmacker")
            self.cursor.execute(f"""
                                select count(j.Description) as 'Commands'
                                from QSmacker..Job j
                                inner join QSmacker..RTUBatch b on j.ID = b.JobId
                                inner join QSmacker..Command c on b.ID = c.RTUBatchId
                                where c.CommandStatusId = 7
                                and j.JobStatusId = 1
                                and b.BatchStatusId = 1
                                and j.id = {job_id}
                                """)
            commandCount = self.cursor.fetchall()
            if machineCount == None:
                print("No batches found")
                return None
            else:
                self.close_connection()
                machineCount.append(commandCount[0])
                print(machineCount)
                return machineCount

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
                return "no job"
            else:
                job = [job['id'], job['Description'], job['Email']]
                print(job)
                batches = self.get_batches(job[0])
                removeKeys = ['id', 'jobid', 'BatchTypeId', 'currentBatch', 'removedFromQueue','userId', 'hasChildBatch','parentBatchId'] 
                for key in removeKeys:
                    for batch in batches:
                        batch.pop(key, None)
                if batches == None:
                    print("No batches found SQL")
                    return None
                else:
                    job.append(batches)
                self.close_connection()
                return job
            

            #Failed codes order: Command, Batch, Job
    def fail_job(self, job_id, CommandFail = 4, BatchFail = 4, JobFail = 3):
        if job_id == "":
            print("No job id provided")
            return None
        else:
            self.make_connection(database="Qsmacker")
            self.cursor.execute(f"""
                                declare @FailedCommandStatusID int = {CommandFail}
                                declare @FailedBatchStatusID int = {BatchFail}
                                declare @FailedJobStatusID int = {JobFail}
                                declare @JobID int = {job_id}
                                
                                select j.id JobID, b.id BatchID, c.id CommandID
                                into #JobsRTUsBatches
                                from job j
                                join RTUBatch b on b.JobId = j.id
                                join Command c on c.RTUBatchId = b.id
                                join CommandStatus cs on cs.id = c.CommandStatusId
                                where j.id = @JobID

                                update Job
                                set Job.JobStatusId = @FailedJobStatusID
                                from Job
                                join #JobsRTUsBatches on job.id = #JobsRTUsBatches.JobID

                                update RTUBatch
                                Set RTUBatch.BatchStatusId = @FailedBatchStatusID
                                From RTUBatch
                                join #JobsRTUsBatches on RTUBatch.id = #JobsRTUsBatches.BatchID

                                update Command
                                Set Command.CommandStatusId = @FailedCommandStatusID
                                From Command
                                Join #JobsRTUsBatches b on b.CommandID = Command.id

                                drop table #JobsRTUsBatches
                                """)
            self.connection.commit()
            self.close_connection()
            return True
        

    def find_branch_default_machine_status(self, branch):
        if branch == "":
            print("No branch provided")
            return "no branch"
        else:
            self.make_connection(database="Realcontrol")
            self.cursor.execute(f"""select b.ID as 'BranchID', b.BranchName, c.CustomerName from tblBranch b
                                  inner join tblCustomers c on c.ID = b.CustomerID
                                  where BranchName = '{branch}'""")
            branch = [self.cursor.fetchone()]
            print(f"the value of branch is {branch}")
            if branch == [None]:
                print("No branch found")
                return "no branch"
            else:
                self.close_connection()
                self.make_connection(database="Realcontrol")
                self.cursor.execute(f"""select count(*) as 'HasDefaultMachine' from tblRTUDetails
                                      where BranchID = {branch[0]['BranchID']} and RefNo like '%DEFAULT%'""")
                defaultMachine = self.cursor.fetchone()
                branch.append(defaultMachine)
                print(branch)
                return branch


    def insert_default_machine_sql(self, branchID):
        self.make_connection(database="Realcontrol")
        self.cursor.execute(f"""
                            Declare @BranchID Int = {branchID}
                            Declare @AgentID Int
                            Declare @SerialNumber Int
                            Declare @RefNo Varchar(20)
                            Declare @strTypeID Int
                            Declare @ModelID Int

                            Set @AgentID = (Select ID From tblAgents Where [Description] = 'RTS STOCK')
                            Set @SerialNumber = 0 - (Select max(ID) + 1 From tblRTUDetails)

                            If @SerialNumber is null
                            Begin
                            Set @SerialNumber = 1
                            End
                            Set @strTypeID = (select min(ID) from [dbo].[tblRTUType])
                            Set @ModelID = (select min(ID) from [dbo].[tblRTUModel])
                            Set @RefNo = (select convert(varchar(42), @BranchID) + '_DEFAULT')

                            Insert Into tblRTUDetails(AgentID,BranchID,SerialNumber,CellNumber,SIMNumber,RefNo,strTypeID,ModelID)
                            Select @AgentID,@BranchID,@SerialNumber,@RefNo,@RefNo,@RefNo,@strTypeID,@ModelID
                            """)
        return True
    
    def audit_rtu_by_refno(self, refno):
        if refno == "":
            print("No refno provided")
            return "no refno"
        else:
            self.make_connection(database="Realcontrol")
            self.cursor.execute(f"""
                                select * from tblRTUDetails_AuditExact (nolock)
                                where IDOriginal = (select ID from tblRTUDetails where RefNo = '{refno}')
                                order by id desc
                                """)
            rtu = self.cursor.fetchall()
            if rtu == [None]:
                print("No RTU found")
                return "no refno"
            else:
                self.close_connection()
                return rtu
        
    def audit_rtu_by_serialno(self, serialno):
        if serialno == "":
            print("No refno provided")
            return "no refno"
        else:
            self.make_connection(database="Realcontrol")
            self.cursor.execute(f"""
                                select * from tblRTUDetails_AuditExact (nolock)
                                where IDOriginal = (select ID from tblRTUDetails where SerialNumber = {serialno})
                                order by id desc
                                """)
            rtu = self.cursor.fetchall()
            if rtu == [None]:
                print("No RTU found")
                return "no refno"
            else:
                self.close_connection()
                return rtu
            
    def audit_branch(self, branch):
        if branch == "":
            print("No Branch provided")
            return "no branch"
        else:
            self.make_connection(database="Realcontrol")
            self.cursor.execute(f"""
                                select * from tblBranch_AuditExact
                                where IDOriginal = (select ID from tblBranch where BranchName = '{branch}')
                                order by id desc
                                """)
            branchResults = self.cursor.fetchall()
            if branchResults == [None]:
                print("No Branch found")
                return "no branch"
            else:
                self.close_connection()
                return branchResults
            
    def audit_customer(self, customer):
        if customer == "":
            print("No Customer provided")
            return "no customer"
        else:
            self.make_connection(database="Realcontrol")
            self.cursor.execute(f"""select * from tblRTUDetails where RefNo like '{customer}'""")
            customerResults = self.cursor.fetchall()
            if customerResults == [None]:
                print("No Customer found")
                return "no customer"
            else:
                self.close_connection()
                return customerResults
            
    def get_rts_users(self):
        self.make_connection(database="Realcontrol")
        self.cursor.execute("""
                            select id, email from tblusers
                            where (email like '%@realtelematics.co.za%'
                            or email like '%@realtimesolutions.co.za%')
                            and email not like '%za.%'
                            """)
        rts_users = self.cursor.fetchall()
        self.close_connection()
        return rts_users