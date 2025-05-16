import MySQLdb
from dotenv import load_dotenv
from typing import Optional, Any, List, Dict, Union, Tuple
load_dotenv()
import os

class ConnDatabase:
    """A class to manage MySQL database connections using environment variables.

    Args:
        database_name (str): The name of the database to connect to.
    
    Raises:
        EnvironmentError: If required database environment variables are not set.
    """

    def __init__(self, database_name: str) -> None:
        """Initialize the database connection using environment variables."""
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USERNAME")
        db_password = os.getenv("DB_PASSWORD")

        if not all([db_host, db_user, db_password]):
            raise EnvironmentError(
                "Missing database configuration. "
                "Please set DB_HOST, DB_USERNAME, and DB_PASSWORD in the .env file."
            )

        self.database_name = database_name
        self.connection = MySQLdb.connect(
            host=db_host,
            user=db_user,
            passwd=db_password,
            db=database_name,
            autocommit=True,
        )
        self.cursor = self.connection.cursor()

    def close(self) -> None:
        """Close the database connection and cursor."""
        self.cursor.close()
        self.connection.close()

    def _validate_table_name(self, table_name: str) -> None:
        """Validate a table name to prevent SQL injection (basic example).
        
        Args:
            table_name: The table name to validate.
        
        Raises:
            ValueError: If the table name contains invalid characters.
        """
        # if not table_name.replace("_", "").replace("/", "").isalnum():
        #     raise ValueError(f"Invalid table name: {table_name}")
        pass

    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL query safely.

        Args:
            query: The SQL query to execute.
            params: Optional parameters for the query (prevents SQL injection).
        
        Raises:
            MySQLdb.Error: If the query execution fails.
        """
        try:
            self.cursor.execute(query, params or ())
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Database error: {e}") from e

    def fetchone(self, query: str, params: Optional[tuple] = None) -> tuple:
        """Execute a query and fetch a single result.
        
        Args:
            query: The SQL query to execute.
            params: Optional parameters for the query.
        
        Returns:
            The first row of the result, or None if no results.
        """
        self.execute(query, params)
        return self.cursor.fetchone()
    
    def fetchall(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a query and fetch a single result.
        
        Args:
            query: The SQL query to execute.
            params: Optional parameters for the query.
        
        Returns:
            The first row of the result, or None if no results.
        """
        self.execute(query, params)
        return self.cursor.fetchall()

    def create_if_not_exists(self, table_name: str, schema: str) -> None:
        """Create a table if it does not already exist.
        
        Args:
            table_name: The name of the table to create.
            schema: The table schema (e.g., "id INT, name VARCHAR(255)").
        
        Raises:
            ValueError: If the table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        self._validate_table_name(table_name)
        self.execute(f"CREATE TABLE IF NOT EXISTS `{table_name}` ({schema});")

    def create_new_table(self, table_name: str, schema: str) -> None:
        """Create a new table, dropping it first if it exists.
        
        Args:
            table_name: The name of the table to create.
            schema: The table schema (e.g., "id INT, name VARCHAR(255)").
        
        Raises:
            ValueError: If the table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        self._validate_table_name(table_name)
        self.drop(table_name)
        self.execute(f"CREATE TABLE `{table_name}` ({schema});")

    def drop(self, table_name: str) -> None:
        """Drop a table if it exists.
        
        Args:
            table_name: The name of the table to drop.
        
        Raises:
            ValueError: If the table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        self._validate_table_name(table_name)
        self.execute(f"DROP TABLE IF EXISTS `{table_name}`;")

    def entry_count(self, table_name: str, condition: Optional[str] = None, condition_values: Optional[tuple] = None) -> int:
        """Return the number of entries in a table.
        
        Args:
            table_name: The name of the table to count.
            condition: WHERE condition string (use %s for parameters)
            condition_values: Tuple of values for condition placeholders
        
        Returns:
            The number of rows in the table.
        
        Raises:
            ValueError: If the table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        self._validate_table_name(table_name)
        
        query = f"SELECT COUNT(*) FROM `{table_name}`"
        if condition:
            query += f" WHERE {condition}"
        result = self.fetchone(query, condition_values)
        return result[0] if result else 0


    def show_tables(self) -> List[str]:
        """Return a list of all table names in the current database.
        
        Returns:
            List[str]: A list of table names.
        
        Raises:
            MySQLdb.Error: If the query fails.
        """
        try:
            result = self.fetchall("SHOW TABLES;")
            return [entry[0] for entry in result]  # List comprehension
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Failed to fetch tables: {e}") from e

    def show_columns(self, table_name: str) -> List[str]:
        """Return a list of column names for the specified table.
        
        Args:
            table_name (str): The name of the table.
        
        Returns:
            List[str]: A list of column names.
        
        Raises:
            ValueError: If the table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        self._validate_table_name(table_name)    
        try:
            query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s;
            """
            result = self.fetchall(query, (table_name,))  # Parameterized query
            return [entry[0] for entry in result]
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Failed to fetch columns: {e}") from e
        
    def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
    ) -> Optional[int]:
        """Insert a new record into the specified table using a dictionary.
        
        Args:
            table_name: Name of the table to insert into.
            data: Dictionary where keys are column names and values are data to insert.
        
        Returns:
            Optional[int]: The last inserted row ID (if applicable), or None if failed.
        
        Raises:
            ValueError: If dictionary is empty or table name is invalid.
            MySQLdb.Error: If the query fails.
        """
        # Validate input
        if not data:
            raise ValueError("Data dictionary cannot be empty.")
        self._validate_table_name(table_name)

        # Extract fields and values from dictionary
        fields = list(data.keys())
        values = tuple(data.values())

        # Build parameterized query
        fields_str = "`, `".join(fields)
        placeholders = ", ".join(["%s"] * len(fields))
        query = f"INSERT INTO `{table_name}` (`{fields_str}`) VALUES ({placeholders})"

        try:
            self.execute(query, values)
            return self.cursor.lastrowid
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Insert failed: {e}") from e
            
    
    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        condition: str,
        condition_values: Optional[tuple] = None
    ) -> int:
        """Update records in the specified table based on a condition.
        
        Args:
            table_name: Name of the table to update
            data: Dictionary of {column: value} pairs to update
            condition: WHERE condition string (use %s for parameters)
            condition_values: Tuple of values for condition placeholders
            
        Returns:
            int: Number of affected rows
            
        Raises:
            ValueError: If data is empty or table name is invalid
            MySQLdb.Error: If the query fails
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty.")
        self._validate_table_name(table_name)

        # Build SET clause
        set_fields = [f"`{k}`=%s" for k in data.keys()]
        set_values = list(data.values())
        
        # Combine all values (SET values + condition values)
        all_values = (*set_values, *(condition_values or ()))
        
        query = f"UPDATE `{table_name}` SET {', '.join(set_fields)} WHERE {condition}"
        
        try:
            self.execute(query, all_values)
            return self.cursor.rowcount
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Update failed: {e}") from e


    def upsert(
        self,
        table_name: str,
        data: Dict[str, Any],
        condition_fields: Union[str, List[str]]
    ) -> int:
        """Update record if exists, otherwise insert (upsert operation).
        
        Args:
            table_name: Name of the table
            data: Dictionary of {column: value} pairs
            condition_fields: Single field or list of fields to check for existing record
            
        Returns:
            int: Last inserted ID if created, or rowcount if updated
            
        Raises:
            ValueError: If data is empty or condition fields missing
            MySQLdb.Error: If the operation fails
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty.")
            
        # Convert single field to list for consistent processing
        if isinstance(condition_fields, str):
            condition_fields = [condition_fields]
            
        # Check all condition fields exist in data
        missing_fields = [field for field in condition_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Condition fields missing in data: {', '.join(missing_fields)}")
        
        self._validate_table_name(table_name)
        
        # Prepare condition values and where clause
        condition_values = [data[field] for field in condition_fields]
        where_parts = [f"`{field}`=%s" for field in condition_fields]
        where_clause = " AND ".join(where_parts)
        count_query = f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_clause}"
        
        try:
            self.execute(count_query, condition_values)
            exists = self.cursor.fetchone()[0] > 0
            
            if exists:
                # Build condition for update
                # Remove condition fields from update data to avoid duplicate set
                update_data = {k: v for k, v in data.items() if k not in condition_fields}
                return self.update(table_name, update_data, where_clause, condition_values)
            else:
                return self.insert(table_name, data)
                
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Upsert operation failed: {e}") from e
    

    def select_one(
        self,
        table_name: str,
        fields: Union[List[str], str] = "*",
        condition: Optional[str] = None,
        condition_values: Optional[Tuple[Any, ...]] = None,
        return_as: str = "dict"  # 'dict' or 'tuple'
    ) -> Optional[Dict[str, Any]]:
        """Select a single record from the specified table.
        
        Args:
            table_name: Name of the table to query
            fields: List of field names or "*" for all fields
            condition: WHERE clause (use %s for placeholders)
            condition_values: Tuple of values for condition placeholders
            return_as: Return format ('dict' or 'tuple')
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary of {field: value} or None if not found
            
        Raises:
            ValueError: If table name is invalid
            MySQLdb.Error: If the query fails
        """
        self._validate_table_name(table_name)
        
        # Handle fields selection
        fields_str = self._format_fields(fields)
        
        # Build query
        query = f"SELECT {fields_str} FROM `{table_name}`"
        if condition:
            query += f" WHERE {condition}"
        
        try:
            self.execute(query, condition_values)
            row = self.cursor.fetchone()
            if not row:
                return None
                
            # Convert to dictionary if fields were specified
            if return_as == "dict" and isinstance(fields, list):
                return dict(zip(fields, row))
            return row  # For "*" queries, return raw tuple
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Select failed: {e}") from e

    def select_all(
        self,
        table_name: str,
        fields: Union[List[str], str] = "*",
        condition: Optional[str] = None,
        condition_values: Optional[Tuple[Any, ...]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        return_as: str = "dict"  # 'dict' or 'tuple'
    ) -> List[Union[Dict[str, Any], Tuple[Any, ...]]]:
        """Select multiple records from the specified table with various options.
        
        Args:
            table_name: Name of the table to query
            fields: List of field names or "*" for all fields
            condition: WHERE clause (use %s for placeholders)
            condition_values: Tuple of values for condition placeholders
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field to sort by
            descending: Sort in descending order
            return_as: Return format ('dict' or 'tuple')
            
        Returns:
            List of records in specified format
            
        Raises:
            ValueError: For invalid parameters
            MySQLdb.Error: If the query fails
        """
        self._validate_table_name(table_name)
        
        # Handle fields selection
        fields_str = self._format_fields(fields)
        
        # Build query
        query = f"SELECT {fields_str} FROM `{table_name}`"
        
        # WHERE clause
        if condition:
            query += f" WHERE {condition}"
        
        # ORDER BY clause
        if order_by:
            self._validate_field_name(order_by)
            query += f" ORDER BY `{order_by}`"
            if descending:
                query += " DESC"
        
        # LIMIT/OFFSET clause
        if limit is not None:
            query += f" LIMIT {limit}"
            if offset is not None:
                query += f" OFFSET {offset}"
        
        try:
            self.execute(query, condition_values)
            rows = self.cursor.fetchall()
            
            # Format results
            if return_as == "dict" and isinstance(fields, list):
                return [dict(zip(fields, row)) for row in rows]
            return rows
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Select failed: {e}") from e

    def _format_fields(self, fields: Union[List[str], str]) -> str:
        """Format fields list into SQL string."""
        if isinstance(fields, str) and fields == "*":
            return "*"
        if isinstance(fields, list):
            return "`" + "`, `".join(fields) + "`"
        raise ValueError("Fields must be list of strings or '*'")

    def _validate_field_name(self, field_name: str) -> None:
        """Basic validation for field names to prevent SQL injection."""
        # if not field_name.replace("_", "").isalnum():
        #     raise ValueError(f"Invalid field name: {field_name}")
        pass
    
    def delete_one(
        self,
        table_name: str,
        condition: str,
        condition_values: Optional[Tuple[Any, ...]] = None
    ) -> bool:
        """Delete a single record from the specified table.
        
        Args:
            table_name: Name of the table to delete from
            condition: WHERE condition (use %s for placeholders)
            condition_values: Tuple of values for condition placeholders
            
        Returns:
            bool: True if a row was deleted, False otherwise
            
        Raises:
            ValueError: If table name is invalid or condition is empty
            MySQLdb.Error: If the query fails
        """
        self._validate_table_name(table_name)
        
        if not condition.strip():
            raise ValueError("Condition cannot be empty")
        
        query = f"DELETE FROM `{table_name}` WHERE {condition} LIMIT 1"
        
        try:
            self.execute(query, condition_values)
            return self.cursor.rowcount > 0
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Delete failed: {e}") from e
    
    def delete_all(
        self,
        table_name: str,
        condition: Optional[str] = None,
        condition_values: Optional[Tuple[Any, ...]] = None,
        batch_size: Optional[int] = None
    ) -> int:
        """Delete all records matching the condition (or all records if no condition).
        
        Args:
            table_name: Table to delete from
            condition: Optional WHERE clause (use %s for placeholders)
            condition_values: Values for condition placeholders
            batch_size: Optional limit for batch deletion (safety measure)
            
        Returns:
            int: Number of rows deleted
            
        Raises:
            ValueError: For invalid table name or dangerous conditions
            MySQLdb.Error: If the query fails
        """
        self._validate_table_name(table_name)
        
        # Safety check for unprotected mass deletion
        if condition is None and batch_size is None:
            raise ValueError(
                "Unconditioned mass deletion blocked. "
                "Either provide a condition or set batch_size."
            )
        
        base_query = f"DELETE FROM `{table_name}`"
        if condition:
            base_query += f" WHERE {condition}"
        if batch_size:
            base_query += f" LIMIT {batch_size}"
        
        total_deleted = 0
        
        try:
            while True:
                self.execute(base_query, condition_values)
                deleted = self.cursor.rowcount
                total_deleted += deleted
                
                # Stop if batch deletion completed
                if batch_size is None or deleted < batch_size:
                    break
                    
            return total_deleted
            
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to delete records: {e}") from e
        
    def select_with_join(
        self,
        table_name: str,
        joins: List[Dict[str, str]],
        fields: Union[List[str], str] = "*",
        condition: Optional[str] = None,
        condition_values: Optional[Tuple[Any, ...]] = None,
        join_type: str = "INNER",
        return_as: str = "dict"
    ) -> List[Union[Dict[str, Any], Tuple[Any, ...]]]:
        """
        Perform SELECT query with JOIN operations.
        
        Args:
            table_name: Main table name
            joins: List of join specifications as dicts with keys:
                   - 'table': joined table name
                   - 'on': join condition
            fields: Fields to select (list or "*")
            condition: WHERE condition
            condition_values: Values for WHERE placeholders
            join_type: JOIN type (INNER, LEFT, RIGHT, FULL)
            return_as: Return format ('dict' or 'tuple')
        
        Returns:
            List of results in specified format
        """
        self._validate_table_name(table_name)
        fields_str = self._format_fields(fields)
        
        # Build JOIN clauses
        join_clauses = []
        for join in joins:
            self._validate_table_name(join['table'])
            join_clauses.append(
                f"{join_type} JOIN `{join['table']}` ON {join['on']}"
            )
        
        query = f"SELECT {fields_str} FROM `{table_name}` " + \
                " ".join(join_clauses)
        
        if condition:
            query += f" WHERE {condition}"
        
        try:
            self.execute(query, condition_values)
            rows = self.cursor.fetchall()
            
            if return_as == "dict" and isinstance(fields, list):
                return [dict(zip(fields, row)) for row in rows]
            return rows
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Join query failed: {e}") from e
        
    def select_with_group(
        self,
        table_name: str,
        group_fields: List[str],
        aggregate_fields: List[Dict[str, str]],
        condition: Optional[str] = None,
        condition_values: Optional[Tuple[Any, ...]] = None,
        having: Optional[str] = None,
        having_values: Optional[Tuple[Any, ...]] = None,
        return_as: str = "dict"
    ) -> List[Union[Dict[str, Any], Tuple[Any, ...]]]:
        """
        Perform SELECT query with GROUP BY.
        
        Args:
            table_name: Table name
            group_fields: Fields to group by
            aggregate_fields: List of aggregate specs as dicts with:
                             - 'field': field name
                             - 'func': aggregate function (COUNT, SUM, etc.)
                             - 'alias': result column alias
            condition: WHERE condition
            condition_values: Values for WHERE placeholders
            having: HAVING condition
            having_values: Values for HAVING placeholders
            return_as: Return format ('dict' or 'tuple')
        
        Returns:
            List of grouped results
            )
        """
        self._validate_table_name(table_name)
        
        # Build field selection
        select_fields = group_fields.copy()
        for agg in aggregate_fields:
            select_fields.append(
                f"{agg['func']}({agg['field']}) AS {agg['alias']}"
            )
        fields_str = ", ".join(select_fields)
        
        query = f"SELECT {fields_str} FROM `{table_name}`"
        
        if condition:
            query += f" WHERE {condition}"
        
        query += f" GROUP BY {', '.join(group_fields)}"
        
        if having:
            query += f" HAVING {having}"
        
        try:
            # Combine condition and having values
            all_values = ()
            if condition_values:
                all_values += condition_values
            if having_values:
                all_values += having_values
            
            self.execute(query, all_values if all_values else None)
            rows = self.cursor.fetchall()
            
            if return_as == "dict":
                column_names = group_fields + [agg['alias'] for agg in aggregate_fields]
                return [dict(zip(column_names, row)) for row in rows]
            return rows
        except MySQLdb.Error as e:
            raise MySQLdb.Error(f"Group query failed: {e}") from e
    
    def set_primary_key(
        self,
        table_name: str,
        primary_key: Union[str, List[str]],
        drop_existing: bool = False,
        constraint_name: Optional[str] = None
    ) -> bool:
        """Set or modify the primary key constraint for a table.
        
        Args:
            table_name: Name of the table to modify
            primary_key: Column name or list of column names for composite key
            drop_existing: Whether to drop existing primary key first
            constraint_name: Optional name for the constraint (for dropping)
            
        Returns:
            bool: True if the operation succeeded, False otherwise
            
        Raises:
            ValueError: For invalid table/column names
            MySQLdb.Error: If the operation fails
        """
        self._validate_table_name(table_name)
        
        # Validate primary key columns
        if isinstance(primary_key, str):
            columns = [primary_key]
        else:
            columns = primary_key
            
        for col in columns:
            self._validate_field_name(col)
        
        try:
            # Drop existing primary key if requested
            if drop_existing:
                drop_sql = "ALTER TABLE `{table_name}` DROP PRIMARY KEY"
                if constraint_name:
                    drop_sql = f"ALTER TABLE `{table_name}` DROP CONSTRAINT `{constraint_name}`"
                self.execute(drop_sql.format(table_name=table_name))
            
            # Add new primary key
            columns_str = "`, `".join(columns)
            self.execute(
                f"ALTER TABLE `{table_name}` "
                f"ADD PRIMARY KEY (`{columns_str}`)"
            )
            return True
            
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(
                f"Failed to set primary key: {e}. "
                "Note: You may need to ensure columns are NOT NULL first."
            ) from e

    def remove_primary_key(
        self,
        table_name: str,
        constraint_name: Optional[str] = None
    ) -> bool:
        """Remove the primary key constraint from a table.
        
        Args:
            table_name: Name of the table to modify
            constraint_name: Optional name if the constraint was named
            
        Returns:
            bool: True if the operation succeeded
        """
        self._validate_table_name(table_name)
        
        try:
            if constraint_name:
                self.execute(
                    f"ALTER TABLE `{table_name}` "
                    f"DROP CONSTRAINT `{constraint_name}`"
                )
            else:
                self.execute(
                    f"ALTER TABLE `{table_name}` "
                    "DROP PRIMARY KEY"
                )
            return True
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to remove primary key: {e}") from e

    def combine_tables(
        self,
        new_table: str,
        old_tables: List[str],
        preserve_ids: bool = False,
        where_clause: Optional[str] = None,
        where_values: Optional[tuple] = None,
        chunk_size: Optional[int] = None
    ) -> int:
        """Combine multiple tables with identical structure into a new table.
        
        Args:
            new_table: Name of the table to create
            old_tables: List of source tables to combine
            preserve_ids: Whether to include the 'id' column
            where_clause: Optional WHERE condition for source tables
            where_values: Values for WHERE placeholders
            chunk_size: Process in chunks of this size (for large tables)
            
        Returns:
            int: Total number of rows combined
            
        Raises:
            ValueError: If input validation fails
            MySQLdb.Error: If the operation fails
        """
        # Validate inputs
        if not old_tables:
            raise ValueError("No source tables provided")
        
        self._validate_table_name(new_table)
        for table in old_tables:
            self._validate_table_name(table)
        
        # Get common columns
        common_columns = self._get_common_columns(old_tables)
        if not preserve_ids and 'id' in common_columns:
            common_columns.remove('id')
        
        if not common_columns:
            raise ValueError("No common columns found between tables")
        
        columns_str = "`, `".join(common_columns)
        placeholders = ", ".join(["%s"] * len(common_columns))
        
        try:
            # Create empty target table
            self.drop(new_table)
            self.execute(
                f"CREATE TABLE `{new_table}` AS "
                f"SELECT `{columns_str}` FROM `{old_tables[0]}` "
                "WHERE 1=0"  # Creates structure without data
            )
            
            total_rows = 0
            
            # Process each source table
            for table in old_tables:
                base_query = f"SELECT `{columns_str}` FROM `{table}`"
                if where_clause:
                    base_query += f" WHERE {where_clause}"
                
                if chunk_size:
                    offset = 0
                    while True:
                        chunk_query = (
                            f"{base_query} "
                            f"LIMIT {chunk_size} OFFSET {offset}"
                        )
                        self.execute(
                            f"INSERT INTO `{new_table}` "
                            f"SELECT `{columns_str}` FROM ({chunk_query}) tmp",
                            where_values
                        )
                        rows_added = self.cursor.rowcount
                        total_rows += rows_added
                        offset += chunk_size
                        if rows_added < chunk_size:
                            break
                else:
                    self.execute(
                        f"INSERT INTO `{new_table}` "
                        f"SELECT `{columns_str}` FROM ({base_query}) tmp",
                        where_values
                    )
                    total_rows += self.cursor.rowcount
            
            return total_rows
            
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to combine tables: {e}") from e

    def _get_common_columns(self, tables: List[str]) -> List[str]:
        """Get columns common to all specified tables."""
        if not tables:
            return []
        
        common_columns = None
        
        for table in tables:
            current_columns = set(self.show_columns(table))
            if common_columns is None:
                common_columns = current_columns
            else:
                common_columns &= current_columns
                if not common_columns:
                    break
        
        return sorted(common_columns) if common_columns else []
    

    def duplicate_table(
        self,
        source_table: str,
        new_table: str,
        copy_data: bool = True,
        copy_structure: bool = True,
        include_indexes: bool = True,
        where_clause: Optional[str] = None,
        where_values: Optional[tuple] = None,
        chunk_size: Optional[int] = None
    ) -> int:
        """Create a copy of an existing table with optional data.
        
        Args:
            source_table: Name of the table to copy
            new_table: Name of the new table
            copy_data: Whether to copy table contents
            copy_structure: Whether to copy table structure
            include_indexes: Whether to include indexes/constraints
            where_clause: Optional condition for filtering data
            where_values: Values for WHERE placeholders
            chunk_size: Process in chunks (for large tables)
            
        Returns:
            int: Number of rows copied (if copy_data=True)
            
        Raises:
            ValueError: For invalid table names or parameters
            MySQLdb.Error: If the operation fails
        """
        # Validate inputs
        self._validate_table_name(source_table)
        self._validate_table_name(new_table)
        
        if source_table == new_table:
            raise ValueError("Source and destination tables cannot be the same")
        if not (copy_data or copy_structure):
            raise ValueError("Must copy either structure or data or both")
            
        try:
            rows_copied = 0
            
            # Drop new table if exists
            self.drop(new_table)
            
            # Copy table structure
            if copy_structure:
                if include_indexes:
                    # Copy with all constraints and indexes
                    self.execute(
                        f"CREATE TABLE `{new_table}` LIKE `{source_table}`"
                    )
                else:
                    # Basic structure without indexes
                    self.execute(
                        f"CREATE TABLE `{new_table}` AS "
                        f"SELECT * FROM `{source_table}` WHERE 1=0"
                    )
            
            # Copy data
            if copy_data and copy_structure:
                base_query = f"SELECT * FROM `{source_table}`"
                if where_clause:
                    base_query += f" WHERE {where_clause}"
                
                if chunk_size:
                    offset = 0
                    while True:
                        chunk_query = (
                            f"{base_query} "
                            f"LIMIT {chunk_size} OFFSET {offset}"
                        )
                        self.execute(
                            f"INSERT INTO `{new_table}` {chunk_query}",
                            where_values
                        )
                        rows_added = self.cursor.rowcount
                        rows_copied += rows_added
                        offset += chunk_size
                        if rows_added < chunk_size:
                            break
                else:
                    self.execute(
                        f"INSERT INTO `{new_table}` {base_query}",
                        where_values
                    )
                    rows_copied = self.cursor.rowcount
            elif copy_data:
                raise ValueError("Cannot copy data without copying structure")
            
            return rows_copied
            
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to duplicate table: {e}") from e


    def clone_table_structure(self, source: str, new_table: str) -> None:
        """Convenience method for structure-only copy"""
        return self.duplicate_table(source, new_table, copy_data=False)

    def rename_table(
        self,
        current_name: str,
        new_name: str,
        overwrite: bool = False,
    ) -> bool:
        """Rename a database table with safety checks and options.
        
        Args:
            current_name: Current table name
            new_name: New table name
            overwrite: If True, will drop the target table if it exists
            
        Returns:
            bool: True if rename succeeded, False if skipped (when overwrite=False and target exists)
            
        Raises:
            ValueError: For invalid table names or structure mismatch
            MySQLdb.Error: For database errors during operation
        """
        # Validate table names
        self._validate_table_name(current_name)
        self._validate_table_name(new_name)
        
        if current_name == new_name:
            return True  # No-op
        
        try:
            # Check if new table exists
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = %s
            """, (new_name,))
            target_exists = self.cursor.fetchone()[0] > 0
            
            if target_exists:
                if not overwrite:
                    return False
                self.drop(new_name)
            
            # Perform the rename
            self.execute(f"RENAME TABLE `{current_name}` TO `{new_name}`")
            return True
        
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to rename table: {e}") from e
    
    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        default: Optional[Any] = None,
        not_null: bool = False,
        after_column: Optional[str] = None,
        check_exists: bool = True
    ) -> bool:
        """Add a new column to an existing table.
        
        Args:
            table_name: Name of the table to modify
            column_name: Name of the new column
            column_type: Data type (e.g., 'VARCHAR(255)', 'INT', 'TEXT')
            default: Optional default value
            not_null: Whether the column should be NOT NULL
            after_column: Optional column to position this after
            check_exists: Check if column exists before adding
            
        Returns:
            bool: True if column was added, False if it already exists (when check_exists=True)
            
        Raises:
            ValueError: For invalid parameters
            MySQLdb.Error: For database errors
        """
        # Validate inputs
        self._validate_table_name(table_name)
        self._validate_field_name(column_name)
        
        if not column_type.strip():
            raise ValueError("Column type cannot be empty")
        
        if after_column:
            self._validate_field_name(after_column)
        
        try:
            # Check if column already exists
            if check_exists:
                self.cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s 
                    AND column_name = %s
                """, (table_name, column_name))
                if self.cursor.fetchone()[0] > 0:
                    return False
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}"
            
            if not_null:
                alter_sql += " NOT NULL"
            
            if default is not None:
                alter_sql += f" DEFAULT %s"
                # For string defaults, we need to quote them
                if isinstance(default, str) and not default.startswith("CURRENT_"):
                    default_value = f"'{default}'"
                else:
                    default_value = str(default)
                alter_sql = alter_sql.replace("%s", default_value)
            
            if after_column:
                alter_sql += f" AFTER `{after_column}`"
            
            self.execute(alter_sql)
            return True
            
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to add column: {e}") from e
        
    def drop_column(self, table_name: str, column_name: str,) -> bool:
        """Drop a column in the table.
        
        Args:
            table_name: Name of the table to modify
            column_name: Name of the column to drop
        
        Returns:
            bool: True if column was dropped
        """
        if column_name not in self.show_columns(table_name):
            # Do not need to drop if not exist
            return True
        try:
            self.execute(f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`")
            return True
        except MySQLdb.Error as e:
            self.connection.rollback()
            raise MySQLdb.Error(f"Failed to drop column: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure resources are closed when exiting the context."""
        self.close()

        