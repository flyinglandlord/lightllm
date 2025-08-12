import ctypes
import os
import shutil
import time
import threading
import psutil
import signal
from lightllm.server.core.objs.out_token_circlequeue import LIGHTLLM_OUT_TOKEN_QUEUE_SIZE, LIGHTLLM_TOKEN_MAX_BYTES
from lightllm.server.core.objs.req import ChunkedPrefillReq, TokenHealingReq
from lightllm.server.tokenizer import get_tokenizer
from lightllm.utils.config_utils import get_config_json
from lightllm.utils.log_utils import init_logger
from transformers import AutoTokenizer

logger = init_logger(__name__)


def get_shm_size_gb():
    """
    获取 /dev/shm 的总大小（以GB为单位）。
    """
    try:
        shm_path = "/dev/shm"
        if not os.path.exists(shm_path):
            logger.error(f"{shm_path} not exist, this may indicate a system or Docker configuration anomaly.")
            return 0

        # shutil.disk_usage 返回 (total, used, free)
        total_bytes = shutil.disk_usage(shm_path).total
        total_gb = total_bytes / (1024 ** 3)
        return total_gb
    except Exception as e:
        logger.error(f"Error getting /dev/shm size: {e}")
        return 0


def get_required_shm_size_gb(args, max_image_resolution=(3940, 2160), dtype_size=2):
    """
    获取所需的 /dev/shm 大小（以GB为单位）。
    """
    model_config = get_config_json(args.model_dir)
    tokenizer = get_tokenizer(args.model_dir, trust_remote_code=True)

    if not args.enable_multimodal:
        # by default, 非多模态 24 GB
        total_required_size_gb = 24
    else:
        num_channels = 3
        image_width, image_height = max_image_resolution
        image_size_bytes = image_width * image_height * num_channels

        # 假设加载最大分辨率图片时，通过 tokenizer 得到最多的 image_tokens
        if not hasattr(tokenizer, "get_image_token_length"):
            raise AttributeError("Tokenizer must have a 'get_image_token_length' method for multimodal models.")
        max_image_tokens = tokenizer.get_image_token_length(None)

        # 估算图片 token 所需的资源
        hidden_size = model_config.get("hidden_size")
        if hidden_size is None:
            logger.warning("Model config not contain 'hidden_size', using 4096 by default.")
            image_token_size_bytes = max_image_tokens * 4096 * dtype_size
        else:
            image_token_size_bytes = max_image_tokens * hidden_size * dtype_size

        # 估算Req所需的shm大小
        if args.token_healing_mode:
            req_class_size = ctypes.sizeof(TokenHealingReq)
        else:
            req_class_size = ctypes.sizeof(ChunkedPrefillReq)
        req_shm_size_bytes = req_class_size * args.running_max_req_size

        # 估算OutTokenQueue所需shm大小
        out_token_queue_size_bytes = LIGHTLLM_TOKEN_MAX_BYTES * LIGHTLLM_OUT_TOKEN_QUEUE_SIZE

        total_required_size = (
            args.cache_capacity * (image_size_bytes + image_token_size_bytes)
            + req_shm_size_bytes
            + out_token_queue_size_bytes
        )

        total_required_size_gb = total_required_size / (1024 ** 3) + 2

    return total_required_size_gb


def check_shm_size(args):
    RED = "\033[91m"
    ENDC = "\033[0m"
    shm_size = get_shm_size_gb()
    required_size = get_required_shm_size_gb(args)  # 128G
    if shm_size < required_size:
        logger.warning(f"{RED}Available shm size is less than 128G: {shm_size:.2f}G{ENDC}")
        return shm_size, required_size, False
    else:  # shm_size >= required_size
        return shm_size, required_size, True


def periodic_shm_warning(shm_size, required_shm_size):
    RED = "\033[91m"
    ENDC = "\033[0m"
    while True:
        logger.warning(
            f"{RED}Insufficient shared memory (SHM) available.",
            f"Required: {required_shm_size:.2f}G, Available: {shm_size:.2f}G.\n",
            "If running in Docker, you can increase SHM size with the `--shm-size` flag, ",
            f"like so: `docker run --shm-size=30g [your_image]`{ENDC}",
        )
        time.sleep(120)  # 每 120 秒打印一次警告日志


def start_shm_size_warning_thread(shm_size, required_shm_size):
    shm_warning_thread = threading.Thread(
        target=periodic_shm_warning,
        args=(
            shm_size,
            required_shm_size,
        ),
        daemon=True,
    )
    shm_warning_thread.start()
