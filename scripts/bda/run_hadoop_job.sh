#!/usr/bin/env bash
# ProductPulse — Authentic Hadoop Streaming MapReduce Execution Runner
set -e

echo "=== 1. Configuring Single-Node HDFS ==="
cat << 'EOF' > /opt/hadoop/etc/hadoop/core-site.xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://127.0.0.1:9000</value>
  </property>
</configuration>
EOF

cat << 'EOF' > /opt/hadoop/etc/hadoop/hdfs-site.xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.permissions.enabled</name>
    <value>false</value>
  </property>
</configuration>
EOF

echo "=== 2. Formatting HDFS NameNode ==="
hdfs namenode -format -force -nonInteractive

echo "=== 3. Starting NameNode & DataNode Services ==="
hdfs namenode &
NN_PID=$!
sleep 5

hdfs datanode &
DN_PID=$!
sleep 8

echo "=== 4. Awaiting SafeMode Exit ==="
hdfs dfsadmin -safemode wait

echo "=== 5. Ingesting 25k Reviews into HDFS ==="
hdfs dfs -mkdir -p /productpulse/input
hdfs dfs -put /app/data/raw/sample_reviews_cell_phones_25k.jsonl /productpulse/input/

echo "=== 6. Verifying Input File in HDFS ==="
hdfs dfs -ls -h /productpulse/input/sample_reviews_cell_phones_25k.jsonl

echo "=== 7. Executing Genuine Hadoop Streaming MapReduce Job ==="
START_TIME=$(date +%s)
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -D stream.num.map.output.key.fields=2 \
  -files /app/scripts/bda/aspect_mapper.py,/app/scripts/bda/aspect_reducer.py \
  -input /productpulse/input/sample_reviews_cell_phones_25k.jsonl \
  -output /productpulse/output \
  -mapper "python aspect_mapper.py" \
  -reducer "python aspect_reducer.py"
JOB_STATUS=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "=== 8. MapReduce Job Completed in ${ELAPSED}s with Exit Status: ${JOB_STATUS} ==="

echo "=== 9. Inspecting Output Directory in HDFS ==="
hdfs dfs -ls -h /productpulse/output

echo "=== 10. Extracting Output from HDFS to Local Workspace ==="
rm -rf /app/data/bda/hadoop_output
hdfs dfs -get /productpulse/output /app/data/bda/hadoop_output

echo "=== 11. Head of MapReduce Aggregation Output (HDFS part-00000) ==="
head -n 20 /app/data/bda/hadoop_output/part-00000

echo "=== 12. Total Output Rows Count ==="
wc -l /app/data/bda/hadoop_output/part-00000

kill $DN_PID $NN_PID 2>/dev/null || true
exit $JOB_STATUS
