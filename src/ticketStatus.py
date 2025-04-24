from src.logger import Logger
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
    WHERE (fs.dmsId = '{ticket_id}' OR fs.altId = '{ticket_id}') AND fsm.id = fs.mappingId AND fs.supplier = '{supplier}' AND fs.recipient = '{recipient}' AND fs.status != 'completed';
    """

    return query

def get_ticket_details(ticket_id):

    Logger().getLogger().info("**************************GETTING TICKET STATUS********************************************")

    try:
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

        query_results = mySql.execute_query(ticket_status_query)

    except Exception as e:
        Logger().getLogger().error("ERROR:ticketStatus:get_ticket_details:MySQL: "+str(e))

    if(query_results == []): 
        return None

    dmsid = query_results[0][1]
    altid = query_results[0][2]
    response = f"""
        <h2>Ticket <b>DMS Id: <a href="https://hsdes.intel.com/appstore/DMS/ticket/{dmsid}" target="_blank">{dmsid}</a> Alt Id: {altid}</b></h2> 
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
        display_status = status
        if(status=="process"):
            display_status="in process"
        updatedAt = res[8]
        eta = res[9]

        response += f"""
        <li>
        <b>Supplier: </b>{supplier}, <b>Recipient: </b>{recipient} <br/>
        - <b>Revision:</b> {rev} 
        <b>Pass:</b> {pas} <br/>
        - <b>Status:</b> {display_status} <br/>
        - <b>Updated At:</b> {updatedAt} <br/>
        - <b>ETA:</b> {eta} <br/>
        """


        flowsteps_query = create_flowsteps_query(ticket_id, supplier, recipient)
        try:
            flowsteps_results = mySql.execute_query(flowsteps_query)
        except Exception as e:
            Logger().getLogger().error("ERROR:ticketStatus:get_ticket_details:MySQL: "+str(e))
            raise e
        
        if(flowsteps_results == []):
            response += "<h3>Ticket Complete</h3>"
            continue
        
        response += """
        <br/>
        <table>
            <b>
            <tr>
                <th>SNo</th>
                <th>Step Description</th>
                <th>Status</th>
            </tr>
            </b>
        """
        step = 1
        for flowstep in flowsteps_results:
            description = flowstep[4]
            status = flowstep[9]
            display_status = status
            if(status=="process"):
                display_status="in process"
            updated_at = flowstep[10]
            eta = flowstep[11]
            

            response += f"""
            <tr class={status}>
                <td>{step}</td>
                <td>{description}</td>
                <td>{display_status}</td>
            </tr>
            """
            step+=1
        response += "</table></li> <br>"
    response += "</ol>"
    return response

