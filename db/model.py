import pickle
import os

class MetadataDB:
    def __init__(self, save_path="metadata.pkl"):
        self.save_path = save_path
        if os.path.exists(save_path):
            with open(save_path, "rb") as f:
                self.metadata_store = pickle.load(f)
        else:
            self.metadata_store = {}

    def save(self, id: int, text: str, metadata: Dict[str, Any]):
        self.metadata_store[id] = {
            "text": text,
            "metadata": metadata
        }
        self._persist()

    def get(self, id: int) -> Dict[str, Any]:
        if id not in self.metadata_store:
            raise KeyError(f"ID {id}가 존재하지 않습니다.")
        return self.metadata_store[id]

    def delete(self, id: int):
        if id in self.metadata_store:
            del self.metadata_store[id]
            self._persist()

    def all(self):
        return self.metadata_store

    def _persist(self):
        with open(self.save_path, "wb") as f:
            pickle.dump(self.metadata_store, f)
