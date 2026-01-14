#!/bin/bash
# Generate Test JWT Credentials for Development
# Elite Implementation Standard v2.0.0

set -e

echo "=== Kong JWT Credentials Generator ==="
echo "Creating test credentials for agent-fleet consumers..."

# Generate RSA key pair
openssl genrsa -out agent-fleet-private.pem 2048
openssl rsa -in agent-fleet-private.pem -pubout -out agent-fleet-public.pem

# Extract public key for Kong
PUBLIC_KEY=$(cat agent-fleet-public.pem | sed '1d' | sed '$d' | tr -d '\n')

# Display credentials
echo ""
echo "=== Generated Credentials ==="
echo "Private Key: agent-fleet-private.pem"
echo "Public Key: agent-fleet-public.pem"
echo ""
echo "=== Kong Configuration Commands ==="
echo ""
echo "# Add JWT credential to consumer:"
echo "curl -s -X POST http://localhost:8001/consumers/agent-fleet/jwt \\"
echo "  --data \"algorithm=RS256\" \\"
echo "  --data \"key=$PUBLIC_KEY\""
echo ""
echo "# Test authentication:"
echo "curl -s http://localhost:8001/consumers/agent-fleet/jwt | jq"
echo ""
echo "=== Example JWT Header ==="
echo "Authorization: Bearer <JWT_TOKEN>"
echo ""
echo "Kong will verify the JWT using the public key and validate:"
echo "- issuer (iss): learnflow-agent-fleet"
echo "- subject (sub): agent-fleet"
echo "- audience (aud): learnflow-api"
echo ""

echo "Credentials generated successfully!"