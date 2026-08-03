# Vertical Slice 0018: Dev User And Role Switching

## Purpose

Let a local HiveSight user switch between seeded development Users and role/capability profiles from the Web UI, without implementing real registration or external login yet.

This slice proves that HiveSight can exercise owner, Dataset Curator, Reviewer, Contributor, and unprivileged paths deliberately. It gives us a practical bridge from the current `x-hivesight-dev-user-id` header to future real authentication, while keeping Google/Apple login as a later architecture decision.

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
And seeded development Users exist for owner, Dataset Curator, Reviewer, Contributor, and no-capability personas
When the developer chooses a different active persona in the Web UI
Then Web requests use that User identity
And the UI shows the selected User, Workspace Membership, and internal capabilities
And role-gated actions are available or blocked according to that User's permissions.

## Preconditions

- This slice is local-development-only.
- Core API continues to use `x-hivesight-dev-user-id` as the request identity seam.
- Postgres-backed local development remains the important path for persisted multi-user QA, but the fast in-memory path may keep deterministic seeded personas for tests.
- The selected User must be a real HiveSight `User` in the active store, not an arbitrary typed UUID.
- Workspace access remains enforced by Workspace Membership.
- Internal capabilities such as Dataset Curator and Reviewer remain separate from Workspace Membership.
- Contributor Access Scope does not grant Workspace Membership or broad workspace access.

## End-To-End Behaviour

The Web UI shows a compact "Development user" control near the existing Workspace gate. It lists seeded personas with human-readable labels:

- Workspace Owner
- Dataset Curator
- Reviewer
- External Contributor
- No Capability User

Each persona shows the User id or short stable code, Workspace Membership role where applicable, and capability badges such as `owner`, `dataset_curator`, `reviewer`, `contributor_access`, or `none`.

When the developer changes persona, the Web UI stores the selected dev User id in browser-local state and reloads the dev session from Core API. Subsequent Core API calls use that User id in `x-hivesight-dev-user-id`.

The active session panel must make it obvious who the UI is acting as. This is not presented as real login; it is a development switcher.

Core API exposes a local-only endpoint that lists the available seeded dev personas. The endpoint returns stable user ids, display labels, capabilities, and default workspace information. It must not create arbitrary users from user input. Existing `/v1/dev/session` remains the session-detail endpoint for the selected User.

Role-gated UI areas should react to the selected persona:

- Owner persona can use normal Workspace inspection flows for its Workspace.
- Dataset Curator persona can access dataset repository, crop annotation, model training, candidate pre-labelling, and benchmark evaluation controls for the seeded development workspace.
- Reviewer persona can exercise reviewer-gated annotation review behaviours where the current UI exposes them.
- No Capability User can load a session but sees clear unavailable states for curator/reviewer actions.
- External Contributor persona is listed and selectable, but broad Workspace screens either show no workspace or a clear restricted-access state until a future contributor-task workflow exists.

The current local owner/curator combined persona may still exist for continuity, but the UI must no longer require the developer to remember or manually paste a UUID.

## Layers Touched

- Web UI: Add development persona selector, active User/capability display, selected dev User persistence, and role-gated visibility/disabled states for existing local workflows.
- Core API: Add dev-persona listing endpoint and seed/read support for named development Users. Keep `/v1/dev/session` and current authorization checks.
- Analysis Service: Not touched.
- Storage: Seed dev Users, Workspace Memberships, and internal capabilities in both Postgres dev seed and fast in-memory test setup as needed.
- Queue or async boundary: Not touched.
- Contracts: Add response contract for dev persona list.
- Observability: Log or expose enough information in test/debug output to know which dev User is active; do not add production auth logging.

## Test Seams

- Seam: Core API dev persona listing.
- Behaviour verified: seeded personas are returned with stable ids, labels, Workspace Membership context, and capability flags.
- Test style: API unit/integration test.

- Seam: Core API authorization using selected dev User.
- Behaviour verified: Dataset Curator can access a curator-gated operation; No Capability User is rejected; Workspace access remains enforced.
- Test style: API acceptance or focused service test.

- Seam: Web UI persona selector.
- Behaviour verified: selecting a persona updates session display and subsequent Core API requests use that User id.
- Test style: Playwright acceptance test.

- Seam: Web UI role gating.
- Behaviour verified: curator-only model/dataset controls are visible or enabled for Dataset Curator and unavailable for No Capability User.
- Test style: Playwright acceptance test.

## Data Shape

Minimum dev persona response:

- `user_id`
- `display_name`
- `persona_key`
- `description`
- `workspace_id`
- `workspace_display_name`
- `workspace_membership_role`
- `reviewer_capability`
- `dataset_curator_capability`
- `contributor_access_scope`
- `is_default`

Minimum seeded personas:

| Persona | Workspace Membership | Internal Capability | Notes |
| --- | --- | --- | --- |
| Workspace Owner | `owner` | none by default | Exercises ordinary beekeeper/product owner flows. |
| Dataset Curator | `owner` or explicit dev membership in seeded workspace | `dataset_curator` | Exercises model-data and benchmark governance flows. |
| Reviewer | `owner` or explicit dev membership in seeded workspace | `reviewer` | Exercises review-decision flows. |
| External Contributor | none, unless future task scope requires it | none | Represents a registered contributor identity with restricted Contributor Access Scope. |
| No Capability User | optional isolated workspace, or no access to seeded workspace | none | Exercises authorization failures and restricted UI states. |

The exact UUIDs should be stable constants, documented in the user guide or developer docs, and seeded by `pnpm db:seed-dev` / `pnpm db:reset`.

## Out Of Scope

- Real registration.
- Passwords.
- Google login, Apple login, or any external identity provider.
- Production sessions, cookies, JWT validation, refresh tokens, or logout semantics.
- Multi-workspace invitation and membership administration.
- Editing user roles or capabilities from the UI.
- Contributor task assignment, Contribution Bundles, or contributor permission acceptance.
- Full security threat model for production auth.

## Follow-On Slices

- Auth Boundary Decision: document external identity provider strategy, registration semantics, session architecture, and the split between authentication and HiveSight authorization.
- First External Login Provider: implement the first real OpenID Connect provider, probably Google first, while leaving Apple as a later provider option.
- Contributor Access Workflow: let external contributors accept assigned Contribution Bundles and work only on permitted tasks.
- Real Role Administration: assign and revoke Workspace Memberships, reviewer capability, Dataset Curator capability, and contributor task access.

## Acceptance Criteria

- [ ] The Web UI lets a developer choose among seeded development personas without typing a UUID.
- [ ] The selected persona is persisted locally across browser refresh.
- [ ] The active session panel clearly shows selected User, Workspace Membership role, and capabilities.
- [ ] Core API exposes a local-only dev persona list with stable seeded persona data.
- [ ] Core API still rejects requests without a valid dev User identity.
- [ ] Dataset Curator-only API behaviour is allowed for the Dataset Curator persona and blocked for the No Capability User persona.
- [ ] Reviewer-only API behaviour is allowed for the Reviewer persona and blocked for the No Capability User persona.
- [ ] Workspace access remains enforced when switching Users.
- [ ] External Contributor persona does not gain broad Workspace access.
- [ ] Existing local workflows continue to work for the current default development persona.
- [ ] API and Playwright acceptance tests cover persona selection and at least one role-gated UI/API behaviour.
- [ ] `docs/user-guide.md` explains the development persona switcher and makes clear it is not real login.

## Open Questions

- Should the Dataset Curator and Reviewer personas share the seeded development Workspace, or should they have separate workspaces plus explicit membership where required?
- Should the default persona remain the current combined owner/curator/reviewer user for continuity, or should it become a plain Workspace Owner to make permission boundaries more visible?
- Should Contributor Access Scope have a placeholder data shape in this slice, or should the External Contributor persona simply show "restricted; no assigned tasks yet"?
- Should role-gated controls be hidden, disabled with explanation, or visible with an authorization-error proof point for non-capable users?
- Should the dev persona list endpoint be available only when a development setting is enabled, even in local builds?
