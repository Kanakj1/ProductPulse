#!/usr/bin/env bash
# ProductPulse — Authentic Apache Hive 3.1.3 Analytics Execution Runner
set -e

echo "=========================================================="
echo "ProductPulse: Apache Hive 3.1.3 Analytics Pipeline"
echo "=========================================================="

cat << 'EOF' > /opt/hive/conf/hive-site.xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configuration>
  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:derby:;databaseName=/opt/hadoop/metastore_db;create=true</value>
  </property>
  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>org.apache.derby.jdbc.EmbeddedDriver</value>
  </property>
  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/tmp/warehouse</value>
  </property>
  <property>
    <name>mapreduce.map.memory.mb</name>
    <value>2048</value>
  </property>
  <property>
    <name>mapreduce.reduce.memory.mb</name>
    <value>2048</value>
  </property>
  <property>
    <name>mapreduce.map.java.opts</name>
    <value>-Xmx1536m</value>
  </property>
  <property>
    <name>mapreduce.reduce.java.opts</name>
    <value>-Xmx1536m</value>
  </property>
</configuration>
EOF

export HADOOP_HEAPSIZE=2048
export HADOOP_CLIENT_OPTS="-Xmx2048m"
unset HIVE_OPTS

mkdir -p /tmp/warehouse /tmp/hive /tmp/hadoop
chmod -R 777 /tmp/warehouse /tmp/hive /tmp/hadoop

# 1. Metastore Initialization
echo "`date '+%Y-%m-%d %H:%M:%S'` [INFO] Initializing Derby metastore schema..."
schematool -dbType derby -initSchema || true

# 2. Smoke Test
echo "`date '+%Y-%m-%d %H:%M:%S'` [INFO] Verifying Hive CLI connectivity..."
hive -e "SHOW DATABASES;"

# 3. Full HQL Execution
echo "`date '+%Y-%m-%d %H:%M:%S'` [INFO] Executing scripts/bda/hive_analytics.hql..."
START_TIME=$(date +%s)
hive -f /app/scripts/bda/hive_analytics.hql 2>&1 | tee /app/data/bda/hive_job_execution.log

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "`date '+%Y-%m-%d %H:%M:%S'` [SUCCESS] Full HQL suite completed in ${ELAPSED}s."

# 4. Exporting Individual Queries to CSV with Headers
echo "`date '+%Y-%m-%d %H:%M:%S'` [INFO] Exporting analytical query outputs to CSV..."
python /app/scripts/bda/export_hive_results.py

echo "=========================================================="
echo "`date '+%Y-%m-%d %H:%M:%S'` [SUCCESS] All 5 Hive Analytics Queries Exported:"
echo "----------------------------------------------------------"
wc -l /app/data/bda/hive_query*.csv
echo "=========================================================="
