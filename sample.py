import duckdb

con = duckdb.connect("test/test.db")

tables = con.execute("SHOW ALL TABLES").fetchall()
print("TABLES:\n")
print(tables)
print("\n")

dlt_loads = con.execute("SELECT * FROM strava._dlt_loads").fetchall()
print("DLT_LOADS:\n")
print(dlt_loads)
print("\n")

dlt_pipeline_state = con.execute("SELECT * FROM strava._dlt_pipeline_state").fetchall()
print("DLT_PIPELINE_STATE:\n")
print(dlt_pipeline_state)
print("\n")

dlt_version = con.execute("SELECT * FROM strava._dlt_version").fetchall()
print("DLT_VERSION:\n")
print(dlt_version)
print("\n")
