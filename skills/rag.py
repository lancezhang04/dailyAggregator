import json
import os

import numpy as np
from dotenv import load_dotenv

from apis.openai_api import OpenAIClient
from skills import SKILLS_MAP

load_dotenv()


class ToolsRAG:
    tool_vectors: np.ndarray
    tools: list[dict]

    tools_file_path: str
    vectors_file_path: str
    client: OpenAIClient

    def __init__(
        self,
        tools_file_path: str = "tools.json",
        vectors_file_path: str = "tool_vectors.npy",
    ):
        self.tools_file_path = tools_file_path
        self.vectors_file_path = vectors_file_path
        self.client = OpenAIClient()

        self.load_tools_and_vectors()

    def retrieve_tools_from_description(self, description: str, k: int = 5):
        embedding = self.client.embed_text(description)[0]
        similarities = np.dot(self.tool_vectors, embedding)

        top_k_indices = np.argsort(similarities)[-k:][::-1]
        return [self.tools[i] for i in top_k_indices]

    def load_tools_and_vectors(self) -> None:
        if not os.path.exists(self.tools_file_path):
            raise ValueError(f"Tools file {self.tools_file_path} does not exist.")

        with open(self.tools_file_path, "r") as f:
            descriptions = json.load(f)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in descriptions
        ]

        if os.path.exists(self.vectors_file_path):
            self.tool_vectors = np.load(self.vectors_file_path)
            return

        print("Cannot find tool vectors file, generating new vectors...")
        with open(self.tools_file_path, "r") as f:
            tools = json.load(f)
        tools = [f"{t['name']} - {t['description']}" for t in tools]

        self.tool_vectors = self.client.embed_text(tools)
        np.save(self.vectors_file_path, self.tool_vectors)
