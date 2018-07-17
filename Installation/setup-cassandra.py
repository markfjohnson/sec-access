from cassandra.cluster import Cluster
cluster = Cluster(["node-0-server.cassandra.autoip.dcos.thisdcos.directory",
                   "node-1-server.cassandra.autoip.dcos.thisdcos.directory",
                   "node-2-server.cassandra.autoip.dcos.thisdcos.directory"])
session = cluster.connect()
KEYSPACE = "SEC_DATA"
rows = session.execute("SELECT keyspace_name FROM system_schema.keyspaces")
if KEYSPACE in [row[0] for row in rows]:
    print("dropping existing keyspace...")
    session.execute("DROP KEYSPACE " + KEYSPACE)

print("creating SEC keyspace...")
session.execute("""
        CREATE KEYSPACE %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)

print("setting keyspace...")
session.set_keyspace(KEYSPACE)
print("creating table...")
session.execute("""
        CREATE TABLE sec_index (
            company text,
            rss_link text,
            xbrl_link text,
            published date,
            form_type text,
            rpt_period date,
            full_rss text,
            PRIMARY KEY (company,published)
        )
        """)
print("SEC Cassandra Tables created")
