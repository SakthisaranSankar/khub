# Makefile for Dockerized FastAPI app

# -------------------------
# Docker image and container
# -------------------------
IMAGE_NAME = khub_alpha
CONTAINER_NAME = khub_alpha
PORT = 8000

# -------------------------
# Phony targets
# -------------------------
.PHONY: help build run stop logs clean shell health check-env

# -------------------------
# Help
# -------------------------
help:
	@echo "FastAPI Docker Makefile"
	@echo "======================="
	@echo ""
	@echo "Available commands:"
	@echo "  build        - Build Docker image"
	@echo "  run          - Run container in detached mode using .env"
	@echo "  stop         - Stop and remove container"
	@echo "  logs         - Show container logs (last 50 lines, follow)"
	@echo "  shell        - Open shell in running container"
	@echo "  health       - Check /health endpoint of the app"
	@echo "  check-env    - Verify required environment variables in .env"
	@echo "  clean        - Stop container and remove image"

# -------------------------
# Build Docker image
# -------------------------
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .
	@echo " Image built successfully"

# -------------------------
# Run container in detached mode
# -------------------------
run: stop 
	@echo "Starting container in foreground mode..."
	docker run \
		-p $(PORT):8000 \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-e PYTHONUNBUFFERED=1 \
		-e PYTHONDONTWRITEBYTECODE=1 \
		$(IMAGE_NAME)
		@echo "container started"
	

# -------------------------
# Stop container
# -------------------------
stop:
	-@docker stop $(CONTAINER_NAME)
	-@docker rm $(CONTAINER_NAME)

# -------------------------
# Follow logs
# -------------------------
logs:
	docker logs -f --tail 50 $(CONTAINER_NAME)

# -------------------------
# Open shell
# -------------------------
shell:
	docker exec -it $(CONTAINER_NAME) bash || docker run -it --rm \
		--env-file .env \
		$(IMAGE_NAME) bash

# -------------------------
# Health check
# -------------------------
health:
	@echo "Fetching health endpoint..."
	@curl -s http://127.0.0.1:$(PORT)/health | python -m json.tool

# -------------------------
# Check environment variables
# -------------------------
check-env:
	@echo "Checking required environment variables in .env..."
	@grep -v '^#' .env | while IFS='=' read -r key val; do \
		if [ -z "$$val" ]; then \
			echo " $$key is empty"; \
		fi; \
	done
	@echo " Environment check done"

# -------------------------
# Clean Docker image
# -------------------------
clean: stop
	@echo "Removing Docker image..."
	docker rmi -f $(IMAGE_NAME)
	@echo " Cleaned up"
