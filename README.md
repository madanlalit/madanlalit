```python
from typing import List

class LalitMadan(SoftwareEngineer):
    """
    Building scalable data systems and clean APIs.
    """
    
    location: str = "Remote"
    available_for_hire: bool = True
    
    stack: List[str] = [
        "Python", "FastAPI", "Langchain",
        "Docker", "AWS"
    ]

    def connect(self) -> None:
        """Reach out to me"""
        github = "github.com/yourusername"
        twitter = "twitter.com/yourusername"
