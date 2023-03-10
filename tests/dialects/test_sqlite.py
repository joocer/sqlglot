from tests.dialects.test_dialect import Validator


class TestSQLite(Validator):
    dialect = "sqlite"

    def test_ddl(self):
        self.validate_identity("INSERT OR ABORT INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR FAIL INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR IGNORE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR REPLACE INTO foo (x, y) VALUES (1, 2)")
        self.validate_identity("INSERT OR ROLLBACK INTO foo (x, y) VALUES (1, 2)")

        self.validate_all(
            "CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)",
            write={"sqlite": "CREATE TABLE foo (id INTEGER PRIMARY KEY ASC)"},
        )
        self.validate_all(
            """
            CREATE TABLE "Track"
            (
                CONSTRAINT "PK_Track" FOREIGN KEY ("TrackId"),
                FOREIGN KEY ("AlbumId") REFERENCES "Album" ("AlbumId")
                    ON DELETE NO ACTION ON UPDATE NO ACTION,
                FOREIGN KEY ("AlbumId") ON DELETE CASCADE ON UPDATE RESTRICT,
                FOREIGN KEY ("AlbumId") ON DELETE SET NULL ON UPDATE SET DEFAULT
            )
            """,
            write={
                "sqlite": """CREATE TABLE "Track" (
  CONSTRAINT "PK_Track" FOREIGN KEY ("TrackId"),
  FOREIGN KEY ("AlbumId") REFERENCES "Album"("AlbumId") ON DELETE NO ACTION ON UPDATE NO ACTION,
  FOREIGN KEY ("AlbumId") ON DELETE CASCADE ON UPDATE RESTRICT,
  FOREIGN KEY ("AlbumId") ON DELETE SET NULL ON UPDATE SET DEFAULT
)""",
            },
            pretty=True,
        )
        self.validate_all(
            "CREATE TABLE z (a INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT)",
            read={
                "mysql": "CREATE TABLE z (a INT UNIQUE PRIMARY KEY AUTO_INCREMENT)",
            },
            write={
                "sqlite": "CREATE TABLE z (a INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT)",
                "mysql": "CREATE TABLE z (a INT UNIQUE PRIMARY KEY AUTO_INCREMENT)",
                "postgres": "CREATE TABLE z (a INT GENERATED BY DEFAULT AS IDENTITY NOT NULL UNIQUE PRIMARY KEY)",
            },
        )
        self.validate_all(
            """CREATE TABLE "x" ("Name" NVARCHAR(200) NOT NULL)""",
            write={
                "sqlite": """CREATE TABLE "x" ("Name" TEXT(200) NOT NULL)""",
                "mysql": "CREATE TABLE `x` (`Name` VARCHAR(200) NOT NULL)",
            },
        )

    def test_sqlite(self):
        self.validate_all(
            "CURRENT_DATE",
            read={
                "": "CURRENT_DATE",
                "snowflake": "CURRENT_DATE()",
            },
        )
        self.validate_all(
            "CURRENT_TIME",
            read={
                "": "CURRENT_TIME",
                "snowflake": "CURRENT_TIME()",
            },
        )
        self.validate_all(
            "CURRENT_TIMESTAMP",
            read={
                "": "CURRENT_TIMESTAMP",
                "snowflake": "CURRENT_TIMESTAMP()",
            },
        )
        self.validate_all(
            "SELECT DATE('2020-01-01 16:03:05')",
            read={
                "snowflake": "SELECT CAST('2020-01-01 16:03:05' AS DATE)",
            },
        )
        self.validate_all(
            "SELECT CAST([a].[b] AS SMALLINT) FROM foo",
            write={
                "sqlite": 'SELECT CAST("a"."b" AS INTEGER) FROM foo',
                "spark": "SELECT CAST(`a`.`b` AS SHORT) FROM foo",
            },
        )
        self.validate_all(
            "EDITDIST3(col1, col2)",
            read={
                "sqlite": "EDITDIST3(col1, col2)",
                "spark": "LEVENSHTEIN(col1, col2)",
            },
            write={
                "sqlite": "EDITDIST3(col1, col2)",
                "spark": "LEVENSHTEIN(col1, col2)",
            },
        )
        self.validate_all(
            "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
            write={
                "spark": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname",
                "sqlite": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname",
            },
        )
        self.validate_all("x", read={"snowflake": "LEAST(x)"})
        self.validate_all("MIN(x)", read={"snowflake": "MIN(x)"}, write={"snowflake": "MIN(x)"})
        self.validate_all(
            "MIN(x, y, z)",
            read={"snowflake": "LEAST(x, y, z)"},
            write={"snowflake": "LEAST(x, y, z)"},
        )

    def test_datediff(self):
        self.validate_all(
            "DATEDIFF(a, b, 'day')",
            write={"sqlite": "CAST((JULIANDAY(a) - JULIANDAY(b)) AS INTEGER)"},
        )
        self.validate_all(
            "DATEDIFF(a, b, 'hour')",
            write={"sqlite": "CAST((JULIANDAY(a) - JULIANDAY(b)) * 24.0 AS INTEGER)"},
        )
        self.validate_all(
            "DATEDIFF(a, b, 'year')",
            write={"sqlite": "CAST((JULIANDAY(a) - JULIANDAY(b)) / 365.0 AS INTEGER)"},
        )

    def test_hexadecimal_literal(self):
        self.validate_all(
            "SELECT 0XCC",
            write={
                "sqlite": "SELECT x'CC'",
                "mysql": "SELECT x'CC'",
            },
        )

    def test_window_null_treatment(self):
        self.validate_all(
            "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks",
            write={
                "sqlite": "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks"
            },
        )

    def test_longvarchar_dtype(self):
        self.validate_all(
            "CREATE TABLE foo (bar LONGVARCHAR)",
            write={"sqlite": "CREATE TABLE foo (bar TEXT)"},
        )
