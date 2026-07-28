# Vision

BeehiveMonitor is a Varroa-focused inspection support system for beekeepers.

The primary product goal is to help a hobbyist or small-scale beekeeper assess possible Varroa mite presence from photos of brood frames, super frames, or other inspected hive material. The system should support uploading one or more photos from an inspection, estimating the number of visible bees, detecting likely Varroa mites on bees, and producing an understandable photo-visible infection-rate estimate for that inspection context.

The system is not intended to diagnose hive health, prescribe treatment, or produce an official infestation measurement in its first version. It should present AI-assisted visual estimates and supporting evidence so the beekeeper can use them alongside normal inspection methods.

The primary learning goal is to use this project as a live case study for understanding how AI affects the software development lifecycle, from requirements gathering through production operation.

## Product Direction

The first useful version should focus on:

- Defining apiaries and hives.
- Recording inspection events for individual hives.
- Associating one or more frame photos with an inspection event.
- Running image analysis on submitted photos.
- Estimating complete visible bee count and tracking partial visible bees separately where possible.
- Detecting likely Varroa mites on visible bees.
- Presenting a Varroa estimate as mites per 100 complete visible bees in uploaded photos.
- Presenting tagged-up photos that show likely infected bees and, optionally, other detected bees.
- Allowing lightweight human correction of false positives and missed Varroa markers.
- Keeping original photos and reusable annotation data so tagged images can be re-rendered and reviewed later.

The system will likely begin as a web UI. Native Android and Apple applications are desirable later, especially for field use where beekeepers may capture photos during inspections.

## Success Measures

- A beekeeper can create an apiary, create hives within it, and record an inspection.
- A beekeeper can upload multiple photos for an inspection.
- The system produces a visible bee count and likely Varroa count per image and per inspection.
- The system produces tagged-up image evidence showing the detections behind the estimate.
- The beekeeper can correct obvious tagging errors.
- The system explains the basis and limitations of the infection-rate estimate.
- Model training, evaluation, consent, benchmark, and release-gate requirements are documented separately from product behaviour.
- Requirements, design decisions, implementation, tests, and production evidence can be traced through the project.
