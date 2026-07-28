# Local Infrastructure

`docker-compose.yml` starts the first local infrastructure shape:

- PostgreSQL for service data stores.
- Redis as the initial local queue candidate.
- MinIO as S3-compatible object storage.

This is not yet a production deployment model. The architecture still has open follow-on decisions for database topology, queue technology, object-storage provider, authentication provider, gateway/edge layer, and hosting platform.

