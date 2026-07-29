# Contracts

This folder holds shared contracts between HiveSight services and clients.

Initial contract discipline:

- The Web App talks to the Core API only.
- The Core API exposes OpenAPI from FastAPI.
- The Core API submits analysis work asynchronously.
- The Analysis Service owns detailed analysis outputs.
- Event payloads shared across service boundaries should be documented here before they become implementation details.

