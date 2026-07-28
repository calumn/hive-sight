# Core API

The Core API is the protected product-facing service boundary.

Responsibilities:

- Workspace-scoped product data.
- Apiaries, hives, inspections, frame labels, and inspection-photo metadata.
- Workspace Data Use Agreement state.
- User-facing analysis status and summaries.
- Authorization decisions before upload, view, or analysis actions.

This scaffold uses in-memory placeholders only. Persistence, authentication, queue publishing, and signed object-storage URLs are follow-on implementation work.

