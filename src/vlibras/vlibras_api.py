import requests
from pathlib import Path

class GlosaDictionary:
    def __init__(self, base_url: str) -> None:
        self.base_url: str = base_url 
        
    def search_glosa_task_id(self, glosa: str) -> int:
        """
        Search the glosa task id
        """
        url: str = self.base_url + f"?code={glosa}&page=1&limit=1"
        data: list[dict] = requests.get(url).json()["data"]

        if len(data) == 0:
            raise ValueError(f"'{glosa}' glosa not found.")

        task: dict = data.pop()
        return task["task_id"]


class Tasks:
    def __init__(self, base_url: str) -> None:
        self.blend_object_id = 3
        self.base_url: str = base_url

    def get_blend_path(self, task_id: int) -> str:
        url: str = self.base_url + f"/{task_id}/{self.blend_object_id}"
        response: list[dict] = requests.get(url).json()

        if len(response) == 0:
            raise ValueError(f"Task '{task_id}' don't have an object with id: {self.blend_object_id}")

        task_object: dict = response.pop()
        return task_object["path"]


class DownloadBlend:
    def __init__(self, base_url: str) -> None:
        self.base_url: str = base_url

    def download(self, path: str, output_path: Path) -> None:
        url: str = self.base_url + f"/{path}"
        
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

