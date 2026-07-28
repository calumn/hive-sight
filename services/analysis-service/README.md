# Analysis Service

The Analysis Service is the private model-runtime boundary.

Responsibilities:

- Consume analysis work from the async boundary.
- Run the approved model pipeline.
- Store detailed analysis runs, detections, and review evidence.
- Generate tagged outputs.
- Record the Model Version used for each analysis run.

This scaffold returns deterministic stub results. Real inference, persistence, object-storage access, and queue consumption are follow-on implementation work.

