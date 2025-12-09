#!/usr/bin/env python3
"""Push memory efficiency CSV data to PostgreSQL.

This script reads mem-eff.csv and pushes it to a PostgreSQL table.
The table structure supports dynamic version columns.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

import psycopg2
from psycopg2.extras import execute_values


def read_csv_data(csv_file: Path):
    """Read CSV file and return headers and data rows.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Tuple of (version headers, list of row dictionaries)
    """
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # First column is 'size', rest are version numbers
        version_columns = headers[1:]
        
        rows = []
        for row in reader:
            row_dict = {'size': int(row[0])}
            for i, version in enumerate(version_columns, 1):
                row_dict[f"v{version.replace('.', '_')}"] = float(row[i])
            rows.append(row_dict)
    
    return version_columns, rows


def get_existing_columns(conn, table_name: str):
    """Get existing column names from the specified table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            """,
            (table_name,)
        )
        result = cur.fetchall()
        if result is None:
            return set()
        return {row[0] for row in result}


def create_or_update_table(conn, table_name: str, version_columns: List[str]):
    """Create table or add missing version columns dynamically.
    
    Args:
        conn: PostgreSQL connection
        table_name: Name of the table
        version_columns: List of version strings (e.g., ['7.2', '8.0', '8.1'])
    """
    with conn.cursor() as cur:
        # Check if table exists
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
            """,
            (table_name,)
        )
        result = cur.fetchone()
        table_exists = result[0] if result else False
        
        if not table_exists:
            # Create new table
            version_cols = [f"v{v.replace('.', '_')} DECIMAL(15,6)" for v in version_columns]
            columns_def = ["size INTEGER PRIMARY KEY"] + version_cols + ["updated_at TIMESTAMPTZ DEFAULT NOW()"]
            
            create_sql = f"""
                CREATE TABLE {table_name} (
                    {', '.join(columns_def)}
                )
            """
            cur.execute(create_sql)
            print(f"Created table '{table_name}' with columns: size, {', '.join([f'v{v.replace('.', '_')}' for v in version_columns])}")
        else:
            # Check for missing version columns
            existing_columns = get_existing_columns(conn, table_name)
            
            for version in version_columns:
                col_name = f"v{version.replace('.', '_')}"
                if col_name not in existing_columns:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} DECIMAL(15,6)"
                    cur.execute(alter_sql)
                    print(f"Added new column: {col_name}")
    
    conn.commit()


def upsert_data(conn, table_name: str, rows: List[Dict[str, Any]], dry_run: bool = False):
    """Insert or update data in the table.
    
    Args:
        conn: PostgreSQL connection
        table_name: Name of the table
        rows: List of row dictionaries
        dry_run: If True, only show what would be inserted
        
    Returns:
        Number of rows processed
    """
    if not rows:
        print("No data to process")
        return 0
    
    if dry_run:
        print(f"Would upsert {len(rows)} rows:")
        for i, row in enumerate(rows[:3]):
            print(f"  [{i+1}] {row}")
        if len(rows) > 3:
            print(f"  ... and {len(rows) - 3} more")
        return len(rows)
    
    # Get all column names from first row (excluding 'size')
    all_columns = list(rows[0].keys())
    version_columns = [col for col in all_columns if col != 'size']
    
    # Build UPSERT statement
    columns_str = ', '.join(all_columns)
    values_placeholders = ', '.join(['%s'] * len(all_columns))
    
    # Build UPDATE clause for conflict resolution
    update_assignments = ', '.join([f"{col} = EXCLUDED.{col}" for col in version_columns])
    update_assignments += ", updated_at = NOW()"
    
    upsert_sql = f"""
        INSERT INTO {table_name} ({columns_str}) 
        VALUES %s
        ON CONFLICT (size) 
        DO UPDATE SET {update_assignments}
    """
    
    # Convert rows to tuples in correct column order
    row_tuples = [tuple(row[col] for col in all_columns) for row in rows]
    
    print(f"Upserting {len(row_tuples)} rows into {table_name}...")
    with conn.cursor() as cur:
        execute_values(cur, upsert_sql, row_tuples)
        affected_count = cur.rowcount
    
    conn.commit()
    print(f"Successfully upserted {affected_count} rows")
    return affected_count


def main():
    parser = argparse.ArgumentParser(
        description="Push memory efficiency CSV data to PostgreSQL"
    )
    parser.add_argument(
        "--csv-file",
        default="mem-eff.csv",
        help="Path to CSV file (default: mem-eff.csv)"
    )
    parser.add_argument("--host", help="PostgreSQL host")
    parser.add_argument("--port", default=5432, type=int, help="PostgreSQL port")
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--username", help="Database username")
    parser.add_argument("--password", help="Database password")
    parser.add_argument(
        "--table-name",
        default="mem-efficiency-by-version",
        help="PostgreSQL table name (default: mem-efficiency-by-version)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be inserted without actually inserting"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run:
        if not all([args.host, args.database, args.username, args.password]):
            parser.error(
                "--host, --database, --username, and --password are required unless --dry-run is specified"
            )
    
    csv_file = Path(args.csv_file)
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read CSV data
    print(f"Reading data from {csv_file}...")
    version_columns, rows = read_csv_data(csv_file)
    print(f"Found {len(rows)} rows with versions: {', '.join(version_columns)}")
    
    if args.dry_run:
        print("\n[DRY RUN MODE]")
        upsert_data(None, args.table_name, rows, dry_run=True)
        return
    
    # Connect to PostgreSQL
    try:
        print(f"\nConnecting to PostgreSQL at {args.host}:{args.port}...")
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            database=args.database,
            user=args.username,
            password=args.password,
            connect_timeout=30,
            sslmode="require"
        )
        print("Connected successfully")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create or update table schema
        create_or_update_table(conn, args.table_name, version_columns)
        
        # Upsert data
        upsert_data(conn, args.table_name, rows)
        
        print(f"\n✓ Successfully pushed data to table '{args.table_name}'")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
