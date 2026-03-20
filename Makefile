.PHONY: install test lint format coverage start

# Install Python dependencies
install:
	pip install -r requirements.txt

# Install dev dependencies (adds ruff for linting)
install-dev:
	pip install -r requirements.txt ruff

# Run the full test suite
test:
	pytest test_msr_physical_ai_mcp_server.py -v

# Run tests with coverage report
coverage:
	pytest test_msr_physical_ai_mcp_server.py -v \
		--cov=msr_physical_ai_mcp_server \
		--cov=msr_robot_state \
		--cov-report=term-missing \
		--cov-fail-under=70

# Lint with ruff
lint:
	ruff check msr_physical_ai_mcp_server.py msr_robot_state.py
	ruff format --check msr_physical_ai_mcp_server.py msr_robot_state.py

# Auto-fix formatting
format:
	ruff format msr_physical_ai_mcp_server.py msr_robot_state.py

# Start the MCP server (reads JSON-RPC from stdin, writes to stdout)
start:
	python msr_physical_ai_mcp_server.py
