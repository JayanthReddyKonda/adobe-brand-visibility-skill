#!/usr/bin/env python3
"""
audit_db.py - Zero-dependency SQLite persistence for Brand AI-Readiness audits.
Stores historical audit runs, specialist execution traces, and finding records
using Python standard library sqlite3 only.
"""

import sys
import os
import json
import sqlite3
import argparse
from datetime import datetime, timezone


def get_connection(db_path="audit_history.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path="audit_history.db"):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site TEXT NOT NULL,
        audited_at TEXT NOT NULL,
        execution_time_seconds REAL DEFAULT 0.0,
        total_findings INTEGER DEFAULT 0,
        critical_count INTEGER DEFAULT 0,
        high_count INTEGER DEFAULT 0,
        medium_count INTEGER DEFAULT 0,
        low_count INTEGER DEFAULT 0,
        answerability_index REAL,
        raw_report TEXT
    );

    CREATE TABLE IF NOT EXISTS specialist_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_id INTEGER,
        specialist_name TEXT NOT NULL,
        site TEXT NOT NULL,
        status TEXT NOT NULL,
        executed_at TEXT NOT NULL,
        output_json TEXT,
        FOREIGN KEY(audit_id) REFERENCES audits(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_id INTEGER,
        finding_id TEXT,
        title TEXT NOT NULL,
        severity TEXT NOT NULL,
        confidence TEXT,
        cause_family TEXT,
        cause_id TEXT,
        evidence TEXT,
        suggested_action TEXT,
        FOREIGN KEY(audit_id) REFERENCES audits(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_audits_site ON audits(site);
    CREATE INDEX IF NOT EXISTS idx_findings_audit_id ON findings(audit_id);
    CREATE INDEX IF NOT EXISTS idx_specialist_runs_site ON specialist_runs(site);
    """)
    conn.commit()
    conn.close()


def save_audit_report(report_dict, db_path="audit_history.db"):
    if not isinstance(report_dict, dict):
        return None
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    site = report_dict.get("site", "unknown")
    audited_at = report_dict.get("audited_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    summary = report_dict.get("summary", {})
    metrics = report_dict.get("audit_metrics", {})
    exec_time = metrics.get("execution_time_seconds", 0.0)
    ans_index = metrics.get("answerability_index")
    raw_str = json.dumps(report_dict)

    cur.execute("""
    INSERT INTO audits (
        site, audited_at, execution_time_seconds, total_findings,
        critical_count, high_count, medium_count, low_count,
        answerability_index, raw_report
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site, audited_at, exec_time,
        summary.get("total_findings", 0),
        summary.get("critical", 0),
        summary.get("high", 0),
        summary.get("medium", 0),
        summary.get("low", 0),
        ans_index,
        raw_str
    ))
    audit_id = cur.lastrowid

    # Save specialist runs
    specialists = report_dict.get("specialists", {})
    for s_name, s_data in specialists.items():
        if isinstance(s_data, dict):
            cur.execute("""
            INSERT INTO specialist_runs (audit_id, specialist_name, site, status, executed_at, output_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                audit_id, s_name, site,
                s_data.get("status", "ok"),
                audited_at,
                json.dumps(s_data)
            ))

    # Save findings
    findings = report_dict.get("findings", [])
    for f in findings:
        if isinstance(f, dict):
            action = f.get("suggested_action", {})
            action_summary = action.get("summary") if isinstance(action, dict) else str(action)
            cur.execute("""
            INSERT INTO findings (
                audit_id, finding_id, title, severity, confidence,
                cause_family, cause_id, evidence, suggested_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                f.get("id"),
                f.get("title", "Finding"),
                f.get("severity", "medium"),
                f.get("confidence", "medium"),
                f.get("cause_family"),
                f.get("cause_id"),
                f.get("evidence", ""),
                action_summary
            ))

    conn.commit()
    conn.close()
    return audit_id


def save_specialist_run(specialist_name, site, result_dict, db_path="audit_history.db"):
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    executed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cur.execute("""
    INSERT INTO specialist_runs (audit_id, specialist_name, site, status, executed_at, output_json)
    VALUES (NULL, ?, ?, ?, ?, ?)
    """, (
        specialist_name, site,
        result_dict.get("status", "ok") if isinstance(result_dict, dict) else "unknown",
        executed_at,
        json.dumps(result_dict) if isinstance(result_dict, dict) else str(result_dict)
    ))
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def list_recent_audits(db_path="audit_history.db", limit=10):
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, site, audited_at, execution_time_seconds, total_findings, critical_count, high_count, answerability_index
    FROM audits ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description="Zero-dependency SQLite persistence for Brand AI-Readiness audits.")
    parser.add_argument("--db", default="audit_history.db", help="Path to SQLite database (default: audit_history.db)")
    parser.add_argument("--save", help="Path to JSON report file to store into SQLite")
    parser.add_argument("--list", action="store_true", help="List recent audit records from SQLite database")
    parser.add_argument("--limit", type=int, default=10, help="Number of records to list (default: 10)")
    args = parser.parse_args()

    if args.save:
        with open(args.save, "r", encoding="utf-8") as f:
            data = json.load(f)
        audit_id = save_audit_report(data, db_path=args.db)
        print(json.dumps({"status": "saved", "audit_id": audit_id, "db": args.db}))
    elif args.list:
        records = list_recent_audits(db_path=args.db, limit=args.limit)
        print(json.dumps(records, indent=2))
    else:
        init_db(args.db)
        print(json.dumps({"status": "initialized", "db": args.db}))


if __name__ == "__main__":
    main()

