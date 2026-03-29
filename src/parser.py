from pydantic import BaseModel, Field
from typing import List, Optional, Any
from litellm import completion
import os
import json

class TestCase(BaseModel):
    input: Any
    expected_output: Any

class ParsedProblem(BaseModel):
    goal: str
    constraints: List[str]
    test_cases: List[TestCase]
    description: str

class ProblemParser:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def parse(self, input_text: str) -> ParsedProblem:
        prompt = f"""
        Convert the following problem description into a structured JSON task.
        Extract the goal, constraints, and provide at least 3 relevant test cases.
        
        Input:
        {input_text}
        
        Output format:
        {{
            "goal": "...",
            "constraints": ["...", "..."],
            "test_cases": [
                {{"input": ..., "expected_output": ...}},
                ...
            ],
            "description": "..."
        }}
        """
        
        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        return ParsedProblem(**data)
