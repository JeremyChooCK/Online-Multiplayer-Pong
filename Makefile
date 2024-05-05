# Makefile

# Define service names
SERVICES = db web

# Path to the docker-compose file
COMPOSE_FILE = ./docker-compose.yml

# Build the Docker images
build:
	docker-compose -f $(COMPOSE_FILE) build

# Start up the services
up:
	docker-compose -f $(COMPOSE_FILE) up -d

# Stop the services
down:
	docker-compose -f $(COMPOSE_FILE) down

# Rebuild the services
re: down build up

# Default target
all: build