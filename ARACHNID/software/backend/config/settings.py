from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_yaml_config(filename: str) -> Dict[str, Any]:
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}


class Settings:
    def __init__(self) -> None:
        self.robot_config = load_yaml_config("robot.yaml")
        self.hardware_config = load_yaml_config("hardware.yaml")
        self.interfaces_config = load_yaml_config("interfaces.yaml")
        self.commands_config = load_yaml_config("commands.yaml")
        self.api_config = load_yaml_config("api.yaml")
        self.websocket_config = load_yaml_config("websocket.yaml")
        self.aesa_config = load_yaml_config("aesa.yaml")

        backend_cfg = self.robot_config.get("backend", {})
        self.host: str = backend_cfg.get("host", "0.0.0.0")
        self.port: int = backend_cfg.get("port", 8000)

        frontend_cfg = self.robot_config.get("frontend", {})
        self.websocket_path: str = frontend_cfg.get("websocket_path", "/ws")

        logging_cfg = self.robot_config.get("logging", {})
        self.log_level: str = logging_cfg.get("level", "INFO")

        # AESAR Core Mode
        aesar_cfg = self.hardware_config.get("aesar", {})
        self.aesar_mode: str = os.environ.get("AESAR_MODE", aesar_cfg.get("mode", "DEMO")).upper()

        # Environmental Sensor Settings
        self.environmental_config = self.hardware_config.get("environmental", {})
        dht_cfg = self.environmental_config.get("dht22", {})
        sm_cfg = self.environmental_config.get("soil_moisture", {})
        self.environmental_dht22_temp_min_c: float = float(dht_cfg.get("temp_min_c", -40.0))
        self.environmental_dht22_temp_max_c: float = float(dht_cfg.get("temp_max_c", 80.0))
        self.environmental_dht22_humidity_min_percent: float = float(dht_cfg.get("humidity_min_pct", 0.0))
        self.environmental_dht22_humidity_max_percent: float = float(dht_cfg.get("humidity_max_pct", 100.0))
        self.environmental_soil_dry_adc: int = int(sm_cfg.get("raw_dry", 3200))
        self.environmental_soil_wet_adc: int = int(sm_cfg.get("raw_wet", 1400))
        self.environmental_soil_invert: bool = bool(sm_cfg.get("invert", True))
        self.environmental_soil_min_adc: int = int(sm_cfg.get("min_valid_raw", 100))
        self.environmental_soil_max_adc: int = int(sm_cfg.get("max_valid_raw", 4095))

        # Camera Settings
        camera_cfg = self.hardware_config.get("camera", {})
        self.camera_enabled: bool = os.environ.get("AESAR_CAMERA_ENABLED", str(camera_cfg.get("enabled", True))).lower() in ("true", "1")
        self.camera_provider: str = os.environ.get("CAMERA_PROVIDER", camera_cfg.get("provider", "local")).lower()
        self.local_camera_index: int = int(os.environ.get("LOCAL_CAMERA_INDEX", camera_cfg.get("local_camera_index", 0)))
        self.camera_stream_url: str = os.environ.get("AESAR_CAMERA_STREAM_URL", camera_cfg.get("stream_url", ""))
        self.camera_snapshot_url: str = os.environ.get("AESAR_CAMERA_SNAPSHOT_URL", camera_cfg.get("snapshot_url", ""))
        self.camera_timeout_seconds: float = float(os.environ.get("AESAR_CAMERA_TIMEOUT", camera_cfg.get("timeout_seconds", 3.0)))
        self.camera_timeout: float = self.camera_timeout_seconds
        self.camera_max_retries: int = int(camera_cfg.get("max_retries", 2))
        self.camera_analysis_interval_seconds: int = int(camera_cfg.get("analysis_interval_seconds", 0))

        # Vision Settings
        vision_cfg = self.hardware_config.get("vision", {})
        self.vision_provider: str = os.environ.get("AESAR_VISION_PROVIDER", vision_cfg.get("provider", "mock")).lower()
        self.vision_model_path: str = os.environ.get("VISION_MODEL_PATH", vision_cfg.get("yolo_model_path", ""))
        self.vision_confidence_threshold: float = float(os.environ.get("VISION_CONFIDENCE_THRESHOLD", vision_cfg.get("confidence_threshold", 0.25)))
        self.vision_device: str = os.environ.get("VISION_DEVICE", vision_cfg.get("device", "cpu"))
        self.gemini_model: str = os.environ.get("GEMINI_MODEL", vision_cfg.get("gemini_model", "gemini-2.5-flash"))
        self.gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
        self.vision_timeout_seconds: float = float(vision_cfg.get("timeout_seconds", 12.0))
        self.vision_timeout: float = self.vision_timeout_seconds
        self.aesar_vision_url: str = os.environ.get("AESAR_VISION_URL", vision_cfg.get("remote_url", "http://localhost:8001")).rstrip("/")

        # Storage Settings
        storage_cfg = self.hardware_config.get("storage", {})
        db_rel = storage_cfg.get("database_path", "software/backend/data/aesar_missions.db")
        img_rel = storage_cfg.get("images_directory", "software/backend/data/images")
        base_dir = Path(__file__).resolve().parent.parent.parent.parent  # ARACHNID-main root
        self.db_path: Path = Path(os.environ.get("AESAR_DB_PATH", base_dir / db_rel))
        self.images_dir: Path = Path(os.environ.get("AESAR_IMAGE_DIR", base_dir / img_rel))
        self.storage_database_path: str = str(self.db_path)
        self.storage_image_dir: str = str(self.images_dir)

        # Ensure storage directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # AESA Engine Settings
        pdr_cfg = self.aesa_config.get("pdr", {})
        weights_cfg = pdr_cfg.get("weights", {})
        self.aesa_pdr_pest_weights: Dict[str, float] = weights_cfg.get("pests", {"aphid": 1.0, "thrips": 1.0})
        self.aesa_pdr_defender_weights: Dict[str, float] = weights_cfg.get("defenders", {"ladybird": 1.0, "spider": 1.0})
        self.aesa_pdr_epsilon: float = float(pdr_cfg.get("epsilon", 0.001))
        self.aesa_abiotic_thresholds: Dict[str, Any] = self.aesa_config.get("abiotic_risk", {})
        self.aesa_recommendations: Dict[str, str] = self.aesa_config.get("recommendations", {})


settings = Settings()
