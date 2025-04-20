.PHONY: all test test-logs clean

# Variables
PYTHON = python3
TEST_DIR = ai_agent/tests
UI_SRC=ui
PYTEST = pytest
PYTEST_ARGS = -xvs

all: api

api:
	$(PYTHON) start.py

fe:
	cd ${UI_SRC} && npm run dev

# Run all tests
test:
	$(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)

# Run specific agent tests
test-logs:
	$(PYTEST) $(PYTEST_ARGS) $(TEST_DIR)/test_log_summarization_agent.py

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install dependencies
install:
	pip install -r requirements.txt