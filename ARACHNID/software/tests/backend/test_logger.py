from backend.logging.logger import RoverLogger


def test_rover_logger():
    logger = RoverLogger(max_entries=10)
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    logger.debug("Test debug message")

    logs = logger.get_logs()
    assert len(logs) == 4
    assert logs[0].message == "Test info message"
    assert logs[0].level == "INFO"
    assert logs[1].level == "WARNING"
    assert logs[2].level == "ERROR"
    assert logs[3].level == "DEBUG"


def test_rover_logger_max_entries():
    logger = RoverLogger(max_entries=3)
    for i in range(5):
        logger.info(f"Message {i}")

    logs = logger.get_logs()
    assert len(logs) == 3
    assert logs[-1].message == "Message 4"
