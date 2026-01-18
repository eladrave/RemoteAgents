# WARP

## Testing with a clean Docker container
1. Build fresh images:
   docker compose build --no-cache
2. Start the stack:
   docker compose up -d
3. Run any tests inside a clean container (example for orchestrator):
   docker compose exec orchestrator /bin/sh -lc "timeout 120s python -m pytest -q"

## Using docker exec for testing inside a container
1. Find a running container:
   docker ps
2. Execute a test command inside the container (example for search agent):
   docker exec -it <container_id_or_name> /bin/sh -lc "timeout 120s python -m pytest -q"
