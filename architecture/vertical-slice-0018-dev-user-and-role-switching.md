# Vertical Slice 0018: Dev User And Role Switching

## Purpose

Let a local HiveSight developer switch between seeded development Users from the Web UI, without implementing real registration or external login yet.

This slice is about **User switching**, not role switching. Each selectable entry is a real seeded development User with a stable User id, its own default Workspace, its own Workspace Membership, and its own internal capabilities. Switching development User acts as a proxy for logging out and logging in as someone else.

The slice gives HiveSight a practical bridge from the current `x-hivesight-dev-user-id` header toward future real authentication, while keeping Google/Apple/OpenID Connect provider selection as a later architecture decision.

## Source Inputs

- `CONTEXT.md`
- `requirements/roadmap.md`
- `requirements/model-requirements.md`
- `architecture/parking-lot.md`, especially PARK-0007
- `architecture/vertical-slice-0013-review-recommendations-architecture-decision-pass.md`
- `architecture/vertical-slice-0016-workspace-resume-and-apiary-hive-selection.md`
- `architecture/vertical-slice-0017-resume-training-inspections-and-crops.md`
- Current Core API dev auth seam: `x-hivesight-dev-user-id`
- Current Web API seam: `CoreApiClient`

## User Path

Given HiveSight is running in the local development stack
And seeded development Users exist with stable names, User ids, Workspaces, and capabilities
When the developer chooses a different development User in the Web UI
Then Web requests use that selected User identity
And all user-scoped UI state from the previous User is cleared
And the UI loads the selected User's own default Workspace
And product workflow areas are visible only when the selected User can use them.

## Preconditions

- This slice is local-development-only.
- Core API continues to use `x-hivesight-dev-user-id` as the request identity seam.
- Dev User switching is not production authentication and is not a security boundary.
- The dev User switcher is available only when a development setting enables it.
- Postgres-backed local development remains the important path for persisted multi-user QA, but the fast in-memory path must use the same deterministic seeded development User catalogue for tests.
- The selected User must be a known seeded development User in the active store, not an arbitrary typed UUID.
- An unknown dev User id returns `401 not_authenticated`.
- Each seeded development User has its own default Workspace.
- Each seeded Workspace has the Workspace Data Use Agreement accepted by default for this slice.
- Workspace access remains enforced by Workspace Membership.
- Internal capabilities such as Dataset Curator and Reviewer remain separate from Workspace Membership.
- One User may hold multiple capabilities at the same time.
- Contributor Access Scope is separate from Workspace Membership and does not grant broad Workspace access.

## End-To-End Behaviour

The Web UI shows a compact "Development User" control in the main app shell or sidebar, before the Workspace gate. It lists seeded development Users with human-readable stable names and short display codes. UUIDs may appear in secondary detail, but the main selector should be usable without remembering or pasting an id.

Minimum seeded development Users:

- `DEV-OWNER-CURATOR`: default continuity User with owner Workspace Membership and the current convenient curator/reviewer capabilities.
- `OWNER-A`: Workspace Owner A, with an owner membership in Owner A Workspace and no internal capability.
- `OWNER-B`: Workspace Owner B, with an owner membership in Owner B Workspace and no internal capability.
- `CURATOR-1`: Dataset Curator User, with its own Workspace and Dataset Curator capability.
- `REVIEWER-1`: Reviewer User 1, with its own Workspace and Reviewer capability.
- `REVIEWER-2`: Reviewer User 2, with its own Workspace and Reviewer capability.
- `REVIEWER-3`: Reviewer User 3 / future adjudicator, with its own Workspace and Reviewer capability.
- `CONTRIBUTOR-1`: External Contributor User, with its own Workspace and no broad Workspace access to anyone else's evidence.
- `NO-CAPABILITY`: valid User with its own Workspace and no internal capability.

The Reviewer Users are distinct Users because future Blind Independent Review and Third-Party Adjudication must be able to prove that different people acted. Slice 0018 does not add adjudication rules or a separate adjudicator capability.

Each seeded User's Workspace has a tiny recognisable Apiary and Hive so switching User visibly proves Workspace separation. Seeded Workspaces do not include photos, crops, Dataset Items, Dataset Versions, Training Runs, Model Candidates, or Benchmark Evaluations.

When the developer changes development User, the Web UI treats it like logout plus login as another person:

- clear selected Apiary, Hive, Inspection, Inspection Photo, Training Crop, Dataset Item, Dataset Version, Training Run, Model Candidate, Benchmark Evaluation, filters, local editor state, and other user-scoped UI state;
- persist only the selected dev User id in browser-local state;
- reload the dev session from Core API;
- load the selected User's own default Workspace and its Apiaries/Hives.

The selected development User persists across browser refresh. On app startup the Web UI revalidates the remembered User against Core API. If the User no longer exists or dev personas are disabled, the UI falls back to the default development User or shows a clear development configuration message.

The active session panel is renamed from "Workspace gate" to "Development session". It shows:

- selected User display name and short code;
- selected Workspace display name;
- Workspace Membership role;
- diagnostic capability status, including absent capabilities;
- a small warning that this is development identity switching, not real login.

Product workflow UI follows a stricter rule: do not show capabilities the selected User cannot possibly activate. For example, a No Capability User may see diagnostic capability status in the Development session panel, but should not see disabled model-training controls sitting in the main workflow. Dataset curation/model governance surfaces are shown only to Users with Dataset Curator capability. Reviewer-only surfaces are shown only to Users with Reviewer capability.

Core API exposes a local-only endpoint that lists the available seeded development Users. The endpoint returns stable user ids, display labels, short codes, default Workspace information, Workspace Membership role, internal capabilities, and Contributor Access Scope status. It must not create arbitrary users from user input. Existing `/v1/dev/session` remains the session-detail endpoint for the selected User.

If the dev User list endpoint is disabled, it should disappear as a dev-only route, preferably `404`. The Web UI hides the switcher when the endpoint is unavailable. If the app still depends on dev auth and cannot establish a valid development session, it shows a clear local-development configuration error.

## Layers Touched

- Web UI: Add development User selector, Development session panel, selected dev User persistence, full user-scoped state clearing on switch, and capability-aware product-surface visibility.
- Core API: Add dev User listing endpoint, restrict dev session to known seeded development Users when dev personas are enabled, and preserve existing authorization checks.
- Analysis Service: Not touched.
- Storage: Seed deterministic Users, Workspaces, Workspace Memberships, internal capabilities, and tiny Apiary/Hive records in both Postgres dev seed and fast in-memory setup.
- Queue or async boundary: Not touched.
- Contracts: Add response contract for dev User list.
- Observability: Expose enough local debug information to know which development User is active; do not add production auth logging.

## Test Seams

- Seam: Core API dev User listing.
- Behaviour verified: seeded development Users are returned with stable ids, labels, short codes, default Workspace context, Workspace Membership role, and capability flags.
- Test style: API unit/integration test.

- Seam: Core API dev session identity.
- Behaviour verified: known dev User ids create sessions; unknown dev User ids return `401 not_authenticated`; dev User endpoint returns unavailable when disabled.
- Test style: API test.

- Seam: Core API authorization using selected dev User.
- Behaviour verified: Dataset Curator can access a curator-gated operation; No Capability User is rejected; Workspace access remains enforced.
- Test style: API acceptance or focused service test.

- Seam: Web UI development User selector.
- Behaviour verified: selecting a User updates the Development session panel, clears previous user-scoped state, persists across refresh, and revalidates on startup.
- Test style: Playwright acceptance test.

- Seam: Web UI Workspace separation.
- Behaviour verified: User A's selected Apiary/Hive/Inspection/crop state does not remain visible after switching to User B; User B's own seeded Apiary/Hive context loads instead.
- Test style: Playwright acceptance test.

- Seam: Web UI capability visibility.
- Behaviour verified: curator-only model/dataset controls are visible for Dataset Curator and absent for No Capability User.
- Test style: Playwright acceptance test.

- Seam: Dev-only switcher gate.
- Behaviour verified: when dev personas are enabled, the selector is shown; when disabled, the endpoint is unavailable and the selector is hidden or a clear local-development configuration error is shown.
- Test style: API and Playwright acceptance tests.

## Data Shape

Minimum dev User response:

- `user_id`
- `display_name`
- `dev_user_code`
- `description`
- `workspace_id`
- `workspace_display_name`
- `workspace_membership_role`
- `reviewer_capability`
- `dataset_curator_capability`
- `contributor_access_scope`
- `is_default`

Minimum seeded development Users:

| Dev User | Workspace Membership | Internal Capability | Workspace | Notes |
| --- | --- | --- | --- | --- |
| `DEV-OWNER-CURATOR` | `owner` | `dataset_curator`, `reviewer` | Dev Owner Curator Workspace | Default continuity User for current local workflows. |
| `OWNER-A` | `owner` | none | Owner A Workspace | Ordinary beekeeper/product owner boundary. |
| `OWNER-B` | `owner` | none | Owner B Workspace | Second ordinary owner for switching and separation checks. |
| `CURATOR-1` | `owner` of own Workspace | `dataset_curator` | Dataset Curator Workspace | Curator is a normal User plus internal capability. |
| `REVIEWER-1` | `owner` of own Workspace | `reviewer` | Reviewer 1 Workspace | Distinct future blind-review User. |
| `REVIEWER-2` | `owner` of own Workspace | `reviewer` | Reviewer 2 Workspace | Distinct future blind-review User. |
| `REVIEWER-3` | `owner` of own Workspace | `reviewer` | Reviewer 3 Workspace | Future adjudicator identity, no separate adjudicator capability yet. |
| `CONTRIBUTOR-1` | `owner` of own Workspace | none | Contributor Workspace | Contributor can also be a beekeeper; assigned contributor work comes later. |
| `NO-CAPABILITY` | `owner` | none | No Capability Workspace | Valid User for restricted-product-surface checks. |

Each Workspace should have one recognisable seeded Apiary/Hive pair and an accepted Workspace Data Use Agreement.

## Out Of Scope

- Real registration.
- Passwords.
- Google login, Apple login, or any external identity provider.
- Production sessions, cookies, JWT validation, refresh tokens, or logout semantics.
- Real security claims.
- Multi-user Workspace collaboration, invitations, sharing, or Workspace administration.
- A User belonging to multiple Workspaces or a Workspace selector.
- Cross-user review access.
- Review task queues or contributor task inboxes.
- Editing user roles or capabilities from the UI.
- Contributor task assignment, Contribution Bundles, or contributor permission acceptance.
- Adjudication-specific review rules or capabilities.
- Full security threat model for production auth.

## Follow-On Slices

- Auth Boundary Decision: document external identity provider strategy, registration semantics, session architecture, and the split between authentication and HiveSight authorization. This should produce an ADR before external login is implemented.
- First External Login Provider: implement the first real OpenID Connect provider, probably Google first, while leaving Apple as a later provider option.
- Workspace Collaboration And Membership Model: decide how multiple Users share one Workspace, and whether one User can later belong to multiple Workspaces.
- Assigned Review And Contribution Task Inbox: let reviewers or contributors see assigned work from another User's Workspace without broad Workspace Membership.
- Contributor Access Workflow: let external contributors accept assigned Contribution Bundles and work only on permitted tasks.
- Real Role Administration: assign and revoke Workspace Memberships, reviewer capability, Dataset Curator capability, and contributor task access.

## Acceptance Criteria

- [x] The Web UI lets a developer choose among seeded development Users without typing a UUID.
- [x] The default selected development User preserves the current convenient owner/curator/reviewer local workflow.
- [x] The selected development User is persisted locally across browser refresh and revalidated against Core API on startup.
- [x] Switching development User clears all user-scoped UI state and reloads the selected User's own default Workspace.
- [x] The Development session panel clearly shows selected User, Workspace, Workspace Membership role, and diagnostic capability status.
- [x] Product workflow UI hides curator/reviewer capabilities the selected User cannot activate.
- [x] Core API exposes a local-only dev User list with stable seeded User data when dev personas are enabled.
- [x] Core API dev User list is unavailable when dev personas are disabled, and the Web UI hides the switcher or shows a clear local-development configuration error.
- [x] Core API rejects unknown dev User ids with `401 not_authenticated`.
- [x] Core API still rejects requests without a valid dev User identity.
- [x] Dataset Curator-only API behaviour is allowed for the Dataset Curator User and blocked for the No Capability User.
- [x] Reviewer-only API behaviour is allowed for Reviewer Users and blocked for the No Capability User.
- [x] Workspace access remains enforced when switching Users.
- [x] Reviewer and Contributor Users do not gain broad access to another User's Workspace.
- [x] Every seeded development User has a deterministic User id, display code, default Workspace, accepted Workspace Data Use Agreement, and recognisable Apiary/Hive context in both in-memory and Postgres dev modes.
- [x] Existing local workflows continue to work for the default development User.
- [x] Records created after switching User record the selected User id wherever the domain already has an actor/creator/reviewer/assigned-by field.
- [x] API and Playwright acceptance tests cover User switching, state clearing, role-gated visibility, and dev-only endpoint availability.
- [x] `CONTEXT.md` defines Development User / Development Persona as local testing language, not a product role.
- [x] `docs/user-guide.md` explains the development User switcher and includes a short manual QA scenario.

## Open Questions

- Closed: the dev User list endpoint returns `404 dev_users_disabled` when disabled.
- Closed: deterministic ids use the `000...010x`, `000...020x`, `000...030x`, and `000...040x` ranges for Users, Workspaces, Apiaries, and Hives respectively.
- Closed: the compact switcher sits in the sidebar Development session panel while dev personas are enabled.

## Implementation Notes

- The local stack enables dev User switching by setting `HIVESIGHT_DEV_USERS_ENABLED=true` for the Core API.
- The Web UI hides the switcher if `/v1/dev/users` is unavailable.
- The selected development User id is stored in browser local storage under `hivesight.developmentUserId`.
- Postgres seed/reset uses the same deterministic dev User catalogue as the in-memory store.

## Verification

- `services/core-api/.venv/bin/python -m pytest services/core-api/tests/test_dev_user_switching_slice.py -q`: 4 passed.
- `HIVESIGHT_TEST_DATABASE_URL=postgresql://hive_sight:hive_sight@localhost:5432/hive_sight_core_test services/core-api/.venv/bin/python -m pytest services/core-api/tests/test_postgres_persistence_slice.py::test_postgres_store_seeds_development_users_with_separate_workspaces -q`: 1 passed.
- `pnpm --filter @hive-sight/web exec playwright test tests/acceptance/slice-0018-dev-user-switching.spec.ts`: 1 passed.
- `pnpm verify:slice`: passed; report written to `reports/slice-verification/latest.md`.
