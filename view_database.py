import sqlite3
import os


DATABASE = "telemetry.db"


print("Current working directory:")
print(os.getcwd())

print("\nDatabase location:")
print(os.path.abspath(DATABASE))


connection = sqlite3.connect(DATABASE)

cursor = connection.cursor()


# Check whether the telemetry table exists

cursor.execute("""

SELECT name
FROM sqlite_master
WHERE type='table'

""")

tables = cursor.fetchall()

print("\nTables found:")
print(tables)


# Count total records

cursor.execute("""

SELECT COUNT(*)
FROM telemetry

""")

count = cursor.fetchone()[0]

print(f"\nTotal telemetry records: {count}")


# Get latest records

cursor.execute("""

SELECT
    id,
    vehicle_id,
    timestamp,
    speed_kmh,
    engine_rpm,
    gear

FROM telemetry

ORDER BY id DESC

LIMIT 20

""")


rows = cursor.fetchall()


print("\nLATEST TELEMETRY RECORDS\n")


if not rows:

    print("No telemetry records found.")

else:

    for row in rows:

        print(row)


connection.close()