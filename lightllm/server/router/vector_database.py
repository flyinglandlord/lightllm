from dataclasses import dataclass
import faiss
from lightllm.utils.log_utils import init_logger

logger = init_logger(__name__)

@dataclass
class Settings:
    def __init__(self):
        self.m: int = 512
        self.efConstruction: int = 16
        self.efSearch: int = 256
        

class VectorDatabase:
    def __init__(self, dtype, head_num, head_dim, layer_num, settings: Settings, max_request_num=1):
        self.max_request_num = max_request_num
        self.dtype = dtype
        self.head_num = head_num
        self.head_dim = head_dim
        self.layer_num = layer_num
        self._init_vec_db(max_request_num, dtype, head_num, head_dim, layer_num, settings)
    
    def _init_vec_db(self, max_request_num, dtype, head_num, head_dim, layer_num, settings: Settings):
        self.index = [
            [
                faiss.IndexHNSWFlat(
                    head_dim * head_num,
                    settings.m,
                    faiss.METRIC_INNER_PRODUCT
                )
                for _ in range(layer_num)
            ]
            for __ in range(max_request_num)
        ]
        for i in range(max_request_num):
            for j in range(layer_num):
                self.index[i][j].hnsw.efConstruction = settings.efConstruction
                self.index[i][j].hnsw.efSearch = settings.efSearch
                self.index[i][j].verbose = False
    
    def _free_vec_db(self, request_index):
        for layer in self.index[request_index]:
            faiss.reset()
    
    