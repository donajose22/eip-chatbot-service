from mysql.connector import connect
from src.mySqlConnection import mySqlConnection
from config.config import global_config

config = global_config
host = config["eda_ip_tracker_host"]
port = config["eda_ip_tracker_port"]
username = config["eda_ip_tracker_username"]
password = config["eda_ip_tracker_password"]
db = config["eda_ip_tracker_database"]

def create_flowsteps_query(ticket_id, supplier, recipient):
    query = f"""
    SELECT fs.id, fs.dmsId, fs.altId, fs.mappingId, fsm.description, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.updatedAt, fs.eta
    FROM FlowStepMapping fsm, FlowStep fs
    INNER JOIN (
    SELECT fs.supplier, fs.recipient, subq1.maxRev, MAX(fs.pass) as maxPass, MAX(fs.startedAt) as maxStart
    FROM FlowStep fs
    INNER JOIN (
        SELECT supplier, recipient, MAX(rev) AS maxRev
        FROM FlowStep
        WHERE dmsId = '{ticket_id}' OR altId = '{ticket_id}' 
        GROUP BY supplier, recipient
    ) subq1 ON fs.supplier = subq1.supplier AND fs.recipient = subq1.recipient AND fs.rev = subq1.maxRev 
    WHERE fs.dmsId = '{ticket_id}' OR fs.altId = '{ticket_id}' 
    group by fs.supplier, fs.recipient
    ) AS subq2 ON fs.supplier = subq2.supplier AND fs.recipient = subq2.recipient AND fs.rev = subq2.maxRev AND fs.pass = subq2.maxPass 
    WHERE (fs.dmsId = '{ticket_id}' OR fs.altId = '{ticket_id}') AND fsm.id = fs.mappingId AND fs.supplier = '{supplier}' AND fs.recipient = '{recipient}';
    """

    return query

def get_ticket_details(ticket_id):

    print("**************************GETTING TICKET STATUS********************************************")

    mySql = mySqlConnection(host, port, username, password, db)

    ticket_status_query = f'''
    SELECT fs.id, fs.dmsId, fs.altId, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.updatedAt, fs.eta
    FROM FlowStep fs
    INNER JOIN (
    SELECT fs.supplier, fs.recipient, subq1.maxRev, MAX(fs.pass) as maxPass, MAX(fs.startedAt) as maxStart
    FROM FlowStep fs
    INNER JOIN (
        SELECT supplier, recipient, MAX(rev) AS maxRev
        FROM FlowStep
        WHERE dmsId = '{ticket_id}' OR altId = '{ticket_id}' 
        GROUP BY supplier, recipient
    ) subq1 ON fs.supplier = subq1.supplier AND fs.recipient = subq1.recipient AND fs.rev = subq1.maxRev 
    WHERE fs.dmsId = '{ticket_id}' OR fs.altId = '{ticket_id}' 
    group by fs.supplier, fs.recipient
    ) AS subq2 ON fs.supplier = subq2.supplier AND fs.recipient = subq2.recipient AND fs.rev = subq2.maxRev AND fs.pass = subq2.maxPass AND fs.startedAt = subq2.maxStart
    WHERE (fs.dmsId = '{ticket_id}' OR fs.altId = '{ticket_id}') ;
    '''
    
    response = """
    """

    query_results = mySql.execute_query(ticket_status_query)

    if(query_results == []): 
        return None

    dmsid = query_results[0][1]
    altid = query_results[0][2]
    response = f"""
        <h2>Ticket <b>DMS Id: {dmsid} Alt Id: {altid}</b></h2> 
        <ol>
        """

    for res in query_results:
        id = res[0]
        dmsid = res[1]
        altid = res[2]
        supplier = res[3]
        recipient = res[4]
        rev = res[5]
        pas = res[6]
        status = res[7]
        updatedAt = res[8]
        eta = res[9]

        response += f"""
        <li>
        <b>Supplier: {supplier}, Recipient: {recipient}</b> <br/>
        - <b>Revision:</b> {rev} 
        <b>Pass:</b> {pas} <br/>
        - <b>Status:</b> {status} <br/>
        - <b>Updated At:</b> {updatedAt} <br/>
        - <b>ETA:</b> {eta} <br/>
        <br/>

        <table>
            <b>
            <tr>
                <th>SNo</th>
                <th>Step Description</th>
                <th>Status</th>
                <th>Updated At</th>
                <th>ETA</th>
            </tr>
            </b>
        """

        flowsteps_query = create_flowsteps_query(ticket_id, supplier, recipient)

        flowsteps_results = mySql.execute_query(flowsteps_query)
        
        step = 1
        for flowstep in flowsteps_results:
            description = flowstep[4]
            status = flowstep[9]
            updated_at = flowstep[10]
            eta = flowstep[11]
            response += f"""
            <tr>
                <td>{step}</td>
                <td>{description}</td>
                <td>{status}</td>
                <td>{updated_at}</td>
                <td>{eta}</td>
            </tr>
            """
            step+=1
        response += "</table></li> <br>"
    response += "</ol>"
    return response

