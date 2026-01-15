#!/bin/bash
# Kafka Topic Setup Script for Mastery Engine
# This script creates required Kafka topics for event processing

set -e

# Configuration
KAFKA_BROKER=${KAFKA_BROKER:-"localhost:9092"}
REPLICATION_FACTOR=${REPLICATION_FACTOR:-1}
PARTITIONS=${PARTITIONS:-3}

echo "🔧 Setting up Kafka topics for Mastery Engine..."
echo "Broker: $KAFKA_BROKER"
echo "Partitions: $PARTITIONS"
echo "Replication Factor: $REPLICATION_FACTOR"
echo ""

# Wait for Kafka to be available
echo "⏳ Waiting for Kafka to be available..."
until kafka-topics.sh --bootstrap-server $KAFKA_BROKER --list &> /dev/null; do
    echo "   Kafka not ready, waiting..."
    sleep 2
done
echo "✅ Kafka is ready!"

# Topic: mastery.requests (input events)
echo "🔄 Creating mastery.requests topic..."
kafka-topics.sh --create \
    --bootstrap-server $KAFKA_BROKER \
    --topic mastery.requests \
    --partitions $PARTITIONS \
    --replication-factor $REPLICATION_FACTOR \
    --config retention.ms=604800000 \
    --config cleanup.policy=compact \
    --if-not-exists

# Topic: mastery.results (processed results)
echo "🔄 Creating mastery.results topic..."
kafka-topics.sh --create \
    --bootstrap-server $KAFKA_BROKER \
    --topic mastery.results \
    --partitions $PARTITIONS \
    --replication-factor $REPLICATION_FACTOR \
    --config retention.ms=604800000 \
    --config cleanup.policy=compact \
    --if-not-exists

# Topic: mastery.dlq (dead letter queue)
echo "🔄 Creating mastery.dlq topic..."
kafka-topics.sh --create \
    --bootstrap-server $KAFKA_BROKER \
    --topic mastery.dlq \
    --partitions $PARTITIONS \
    --replication-factor $REPLICATION_FACTOR \
    --config retention.ms=2592000000 \
    --config cleanup.policy=delete \
    --if-not-exists

# Topic: mastery.events (raw events log)
echo "🔄 Creating mastery.events topic..."
kafka-topics.sh --create \
    --bootstrap-server $KAFKA_BROKER \
    --topic mastery.events \
    --partitions $PARTITIONS \
    --replication-factor $REPLICATION_FACTOR \
    --config retention.ms=2592000000 \
    --config cleanup.policy=delete \
    --if-not-exists

echo ""
echo "✅ All topics created successfully!"
echo ""

# List topics to verify
echo "📋 Verifying topics:"
kafka-topics.sh --bootstrap-server $KAFKA_BROKER --list | grep mastery || echo "   No mastery topics found"

echo ""
echo "📊 Topic Details:"
for topic in mastery.requests mastery.results mastery.dlq mastery.events; do
    echo "   $topic:"
    kafka-topics.sh --bootstrap-server $KAFKA_BROKER --describe --topic $topic 2>/dev/null | grep -E "(PartitionCount|ReplicationFactor|Config)" || echo "      (details not available)"
done

echo ""
echo "🎉 Kafka setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start Dapr: dapr run --app-id mastery-engine --app-port 8005 --dapr-http-port 3500"
echo "  2. Start Mastery Engine: cd src && uvicorn main:app --reload --port 8005"
echo "  3. Test event ingestion:"
echo "     curl -X POST http://localhost:8005/api/v1/mastery/ingest \\"
echo "       -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"event_type\":\"exercise.completed\",\"student_id\":\"student_123\",\"data\":{\"exercise_id\":\"ex_1\",\"difficulty\":\"medium\",\"time_spent_seconds\":120,\"completion_rate\":0.9,\"correctness\":0.85}}'"

# Save topic configuration to file for reference
cat > kafka_topics.md << EOF
# Kafka Topics Configuration

## mastery.requests
- Purpose: Input events from learning agents
- Retention: 7 days
- Cleanup: Compact (keep latest per key)

## mastery.results
- Purpose: Processed mastery updates
- Retention: 7 days
- Cleanup: Compact

## mastery.dlq
- Purpose: Failed events for manual review
- Retention: 30 days
- Cleanup: Delete

## mastery.events
- Purpose: Complete event log
- Retention: 30 days
- Cleanup: Delete

## Consumer Group
- Group ID: mastery-engine-v1
- Processing: At-least-once with idempotency
EOF

echo "📋 Configuration saved to kafka_topics.md"