import json
import sqlite3
import os
from pydantic import BaseModel
from typing import List, Any, Optional

class AttemptRecord(BaseModel):
    iteration: int
    approach: str
    code: str
    score: float
    passed: bool
    runtime: float
    output: Optional[str] = None

    def dict(self):
        return super().dict()

class StateStore:
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration INTEGER,
            approach TEXT,
            code TEXT,
            score REAL,
            passed BOOLEAN,
            runtime REAL,
            output TEXT
        )
        """)
        conn.commit()
        conn.close()

    def save_attempt(self, iteration: int, approach: str, code: str, score: float, passed: bool, runtime: float, output: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attempts (iteration, approach, code, score, passed, runtime, output)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (iteration, approach, code, score, passed, runtime, output))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

    def get_top_attempts(self, limit: int = 5) -> List[AttemptRecord]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT iteration, approach, code, score, passed, runtime, output FROM attempts ORDER BY score DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        attempts = []
        for row in rows:
            attempts.append(AttemptRecord(
                iteration=row[0],
                approach=row[1],
                code=row[2],
                score=row[3],
                passed=row[4],
                runtime=row[5],
                output=str(row[6])
            ))
        conn.close()
        return attempts
