#!/bin/bash
set -e

# Initialize directories if they don't exist
mkdir -p /app/output /app/assets /app/generated_cache /app/batch_results

# Set proper permissions
chmod -R 755 /app/output /app/assets /app/generated_cache /app/batch_results

# Initialize costs.json if it doesn't exist
if [ ! -f /app/costs.json ]; then
    echo '{"total_cost": 0, "api_calls": [], "services": {}}' > /app/costs.json
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set. Pipeline will not be able to generate images."
fi

# Run the application with provided arguments
exec "$@"