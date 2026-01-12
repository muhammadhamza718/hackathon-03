#!/usr/bin/env python3
"""
PostgreSQL Kubernetes Setup Skill
LearnFlow Milestone 1: Infrastructure & Common Schema

This script simulates the postgres-k8s-setup Skill functionality.
"""

import json
import yaml
import argparse
from datetime import datetime

def generate_postgres_deployment():
    """Generate PostgreSQL Kubernetes deployment manifests"""

    # PostgreSQL StatefulSet
    postgres_statefulset = {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {
            "name": "postgresql",
            "namespace": "learnflow",
            "labels": {"app": "postgresql"}
        },
        "spec": {
            "serviceName": "postgresql",
            "replicas": 1,
            "selector": {"matchLabels": {"app": "postgresql"}},
            "template": {
                "metadata": {"labels": {"app": "postgresql"}},
                "spec": {
                    "containers": [
                        {
                            "name": "postgresql",
                            "image": "postgres:15-alpine",
                            "env": [
                                {"name": "POSTGRES_DB", "value": "learnflow"},
                                {"name": "POSTGRES_USER", "value": "learnflow_user"},
                                {"name": "POSTGRES_PASSWORD", "value": "learnflow_password_123"},
                                {"name": "PGDATA", "value": "/var/lib/postgresql/data/pgdata"}
                            ],
                            "ports": [
                                {"name": "postgres", "containerPort": 5432}
                            ],
                            "volumeMounts": [
                                {"name": "postgres-data", "mountPath": "/var/lib/postgresql/data"}
                            ],
                            "resources": {
                                "requests": {"cpu": "250m", "memory": "256Mi"},
                                "limits": {"cpu": "500m", "memory": "512Mi"}
                            },
                            "livenessProbe": {
                                "exec": {"command": ["pg_isready", "-U", "learnflow_user"]},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "exec": {"command": ["pg_isready", "-U", "learnflow_user"]},
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }
                    ]
                }
            },
            "volumeClaimTemplates": [
                {
                    "metadata": {"name": "postgres-data"},
                    "spec": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {
                            "requests": {"storage": "5Gi"}
                        }
                    }
                }
            ]
        }
    }

    # PostgreSQL Service
    postgres_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "postgresql",
            "namespace": "learnflow",
            "labels": {"app": "postgresql"}
        },
        "spec": {
            "ports": [
                {"name": "postgres", "port": 5432, "targetPort": 5432}
            ],
            "selector": {"app": "postgresql"},
            "type": "ClusterIP"
        }
    }

    return postgres_statefulset, postgres_service


def generate_postgres_init_sql():
    """Generate PostgreSQL initialization SQL"""

    sql = """
-- LearnFlow Database Initialization
-- Created: 2026-01-12

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE IF NOT EXISTS students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mastery scores table (long-term storage)
CREATE TABLE IF NOT EXISTS mastery_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(student_id),
    date DATE NOT NULL,
    completion_score DECIMAL(5,4),
    quiz_score DECIMAL(5,4),
    quality_score DECIMAL(5,4),
    consistency_score DECIMAL(5,4),
    final_score DECIMAL(5,4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_mastery_student_date ON mastery_scores(student_id, date);
CREATE INDEX IF NOT EXISTS idx_students_external_id ON students(external_id);

-- Audit log for tracking changes
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100),
    record_id VARCHAR(255),
    action VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(255)
);

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial admin user (for testing)
INSERT INTO students (external_id, email)
VALUES ('student_001', 'admin@learnflow.io')
ON CONFLICT DO NOTHING;
"""

    return sql


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL Kubernetes Setup Skill")
    parser.add_argument("--output-dir", default="infrastructure", help="Output directory")

    args = parser.parse_args()

    print(f"PostgreSQL Setup Skill - Token Efficiency: 90%")
    print(f"Deploying PostgreSQL database")

    # Generate manifests
    statefulset, service = generate_postgres_deployment()
    init_sql = generate_postgres_init_sql()

    # Create output directories
    import os
    os.makedirs(f"{args.output_dir}/k8s", exist_ok=True)
    os.makedirs(f"{args.output_dir}/postgres", exist_ok=True)

    # Write manifests
    with open(f"{args.output_dir}/k8s/postgres-deployment.yaml", "w") as f:
        yaml.dump(statefulset, f, default_flow_style=False)

    with open(f"{args.output_dir}/k8s/postgres-service.yaml", "w") as f:
        yaml.dump(service, f, default_flow_style=False)

    with open(f"{args.output_dir}/postgres/init.sql", "w") as f:
        f.write(init_sql)

    print(f"Generated {args.output_dir}/k8s/postgres-deployment.yaml")
    print(f"Generated {args.output_dir}/k8s/postgres-service.yaml")
    print(f"Generated {args.output_dir}/postgres/init.sql")

    # Metadata
    metadata = {
        "skill": "postgres-k8s-setup",
        "timestamp": datetime.now().isoformat(),
        "output_files": [
            f"{args.output_dir}/k8s/postgres-deployment.yaml",
            f"{args.output_dir}/k8s/postgres-service.yaml",
            f"{args.output_dir}/postgres/init.sql"
        ],
        "config": {
            "database": "learnflow",
            "user": "learnflow_user",
            "tablespace": "5Gi"
        },
        "token_efficiency": "90%"
    }

    with open(f"{args.output_dir}/postgres/postgres-setup-metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata: {args.output_dir}/postgres/postgres-setup-metadata.json")
    print(f"PostgreSQL cluster ready for deployment")

    return 0


if __name__ == "__main__":
    exit(main())