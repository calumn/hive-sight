# Stakeholders

## Primary Stakeholders

### Hobbyist or Small-Scale Beekeeper

The version-one primary user. The beekeeper needs a practical way to record hive inspections and assess possible Varroa mite burden from frame photos.

Key concerns:

- Fast capture during or shortly after an inspection.
- Clear decision-support results that can be used alongside normal inspection methods.
- Low friction when managing apiaries, hives, and inspection history.
- Confidence indicators and caveats for AI-generated analysis.
- Tagged-up photos that make it possible to inspect what the AI found.
- A lightweight way to correct obvious missed or incorrect detections.

### Apiary Owner or Manager

A person responsible for multiple hives, potentially across multiple apiaries.

Key concerns:

- Comparing Varroa risk across hives and apiaries.
- Maintaining inspection records over time.
- Seeing which hives need attention.

### System Builder or Maintainer

The person or team developing and operating the system.

Key concerns:

- Requirements traceability.
- Image analysis quality.
- Production observability.
- Data model integrity.
- Evidence of how AI affected the SDLC.

## Future Stakeholders

### Researcher or Advisor

May use aggregated or exported inspection data to understand Varroa patterns, treatment outcomes, or model performance.

### Mobile App User

May need offline or low-connectivity capture, camera integration, and later synchronisation.

### AI Model Reviewer

May review labelled images, false positives, false negatives, model confidence, and field performance.

Key concerns:

- Whether annotations can be traced back to original photos.
- Whether user corrections are captured as structured evidence.
- Whether model performance can be evaluated from inspection history.

## Open Stakeholder Questions

- Are future versions expected to support commercial teams, advisors, or researchers as first-class users?
- Will future users share data across apiaries, organisations, or advisory relationships?
- What collaboration permissions are needed after the single-user or simple-account version?
- Who validates whether Varroa detections are correct?
