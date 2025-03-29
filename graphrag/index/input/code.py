# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
from pathlib import Path

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.util import load_files
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.base import ProgressLogger
from graphrag.storage.pipeline_storage import PipelineStorage

log = logging.getLogger(__name__)


"""
We define all modulenames from the project root - module/package name!
"""


async def load_code(
    config: InputConfig,
    progress: ProgressLogger | None,
    storage: PipelineStorage,
) -> pd.DataFrame:
    """Load code inputs from a directory."""

    async def load_file(path: str, group: dict | None = None) -> pd.DataFrame:
        if group is None:
            group = {}
        text = await storage.get(path, encoding=config.encoding)
        new_item = {**group, "text": text}
        new_item["id"] = gen_sha512_hash(new_item, new_item.keys())
        new_item["title"] = str(path)   
        new_item["creation_date"] = await storage.get_creation_date(path)
        new_item["metadata"] = {"repository": str(path).split('/')[0], "filename": str(path)}
        return pd.DataFrame([new_item])

    return await load_files(load_file, config, storage, progress)
