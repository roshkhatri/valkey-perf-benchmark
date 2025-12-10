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
from psycopg2 import sql
from psycopg2.extras import execute_values


def read_csv_data(csv_file: Path):
    """Read CSV file and convert to tall/long format.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Tuple of (version headers, list of row dictionaries in tall format)
    """
    with open(csv_file, 'r') as f:
        reader = csv.reader(f, delimiter=' ')
        headers = next(reader)
        
        # First column is 'size', rest are version numbers
        version_columns = headers[1:]
        
        rows = []
        for row in reader:
            size = int(row[0])
            # Create one row per version (tall format)
            for i, version in enumerate(version_columns, 1):
                rows.append({
                    'size': size,
                    'version': version,
                    'value': float(row[i])
                })
    
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
            # Create new table in tall format
            create_sql = sql.SQL("""
                CREATE TABLE {} (
                    size INTEGER NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    value DECIMAL(15,6) NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (size, version)
                )
            """).format(sql.Identifier(table_name))
            
            cur.execute(create_sql)
            print(f"Created table '{table_name}' in tall format with columns: size, version, value, updated_at")
            
            # Create index for better query performance
            index_sql = sql.SQL("CREATE INDEX {} ON {} (version, size)").format(
                sql.Identifier(f"idx_{table_name}_version_size"),
                sql.Identifier(table_name)
            )
            cur.execute(index_sql)
        else:
            print(f"Table '{table_name}' already exists")
    
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
    
    # Build UPSERT statement for tall format
    upsert_sql = sql.SQL("""
        INSERT INTO {} (size, version, value) 
        VALUES %s 
        ON CONFLICT (size, version) 
        DO UPDATE SET 
            value = EXCLUDED.value,
            updated_at = NOW()
    """).format(sql.Identifier(table_name))
    
    # Convert rows to tuples: (size, version, value)
    row_tuples = [(row['size'], row['version'], row['value']) for row in rows]
    
    print(f"Upserting {len(row_tuples)} rows into {table_name}...")
    with conn.cursor() as cur:
        execute_values(cur, upsert_sql.as_string(conn), row_tuples)
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
    
    # Get unique sizes for reporting
    sizes = sorted(set(row['size'] for row in rows))
    print(f"Found {len(sizes)} sizes and {len(version_columns)} versions: {', '.join(version_columns)}")
    print(f"Total rows in tall format: {len(rows)}")
    
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
