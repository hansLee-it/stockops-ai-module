# StockOps Admin and Settings Implementation Goals

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` before implementing this plan task-by-task.

**Goal:** Turn the admin and settings area from partial/mock UI into a usable operations admin console, with user management, Microsoft Teams notifications, audit logs, notice management, and real dashboard metrics.

**Architecture:** Keep the current React/Vite/TypeScript structure and add focused API hooks, types, and page-level UI flows. Do not hide P0 settings features as the default solution; implement them where backend contracts exist or define the smallest backend contract needed. External notification integration scope is Microsoft Teams only.

**Tech Stack:** React 19, TypeScript, Vite, React Query, Zustand auth store, Axios API client, Vitest, React Testing Library, Playwright where workflow coverage is useful.

---

## Scope Decisions

- Implement admin/settings features as real functionality whenever practical.
- Prioritize user creation and user administration.
- Keep Microsoft Teams as the only planned external notification integration.
- Remove Slack, KakaoTalk, and other external-service integration plans from this implementation scope.
- Keep API key and backup/restore screens out of the first implementation wave unless backend contracts already exist.
- Make audit, notice, and dashboard pages useful for actual admin operation rather than placeholder summaries.
- Fix broken strings, mojibake, stale English labels, and misleading placeholder copy before and after feature implementation.

## Current Baseline

- Repository for source implementation: `/Users/hans/Documents/git_repository/stockops-admin-web`
- Repository for this document: `/Users/hans/Documents/git_repository/stockops-ai-module`
- Latest checked admin-web commit during planning: `5eab2de chore: support aws nginx config`
- Pull status during planning on 2026-06-05: `Already up to date.`

## Target Routes

- `/settings`
- `/settings/notification-channels`
- `/admin`
- `/admin/notices`
- `/admin/audit-logs`

## High-Level Delivery Order

0. Broken text and copy-quality cleanup
1. User management
2. Microsoft Teams notification settings
3. Notice management completion
4. Audit log viewer
5. Admin dashboard real metrics
6. General settings and role permissions

This order gives the most visible product value first while keeping each slice independently testable.

---

## Phase 0: Baseline Stabilization

**Objective:** Make sure the current app has a known quality baseline before changing admin/settings behavior.

**Implementation Goals**

- Confirm the repository is up to date.
- Run lint, build, and unit tests before functional work.
- Record any existing failures separately from this feature plan.

**Commands**

```bash
git pull --ff-only
npm run lint
npm run build
npm run test:run
```

**Acceptance Criteria**

- The repo is on the latest `origin/main`.
- Existing test/build failures, if any, are documented before implementation starts.
- No admin/settings feature work starts from an unknown baseline.

---

## Phase 0.5: Broken Text and Copy-Quality Cleanup

**Objective:** Fix broken strings, mojibake, encoding artifacts, stale English labels, and misleading placeholder copy before expanding the admin/settings feature set.

**Current Problem**

- Some UI strings may contain broken Korean text, stale English labels, emoji-heavy section labels, or placeholder copy left from earlier prototypes.
- Admin/settings work will add many new labels, so string quality should be normalized before and after each implementation phase.

**Implementation Goals**

- Search admin/settings and shared layout files for broken text and encoding artifacts.
- Replace mojibake and corrupted strings with clear Korean operational copy.
- Normalize Microsoft Teams naming as `Microsoft Teams` or `Teams` consistently.
- Remove Slack, KakaoTalk, and other external-service copy from this plan's target UI.
- Replace misleading placeholder labels with accurate copy, especially where functionality is newly implemented.
- Keep domain codes such as `ADMIN`, `MANAGER`, `OPERATOR`, `TEAMS`, and API paths in English where they are real data values.
- Add regression tests for representative Korean labels in the changed screens.

**Suggested Files**

- Modify: `src/pages/SettingsPage.tsx`
- Modify: `src/pages/settings/NotificationChannelPage.tsx`
- Modify: `src/pages/admin/AdminPage.tsx`
- Modify: `src/pages/admin/NoticeManagement.tsx`
- Modify: `src/pages/admin/AuditLogViewer.tsx`
- Modify if needed: `src/components/MainLayout.tsx`
- Test: relevant page tests touched by each phase

**Suggested Search Commands**

```bash
rg -n "�|ì|ë|ê|Ã|Â|ð|TODO|준비중|coming soon|placeholder|Slack|Kakao|카카오|슬랙|sk_live|sk_test|2024-05" src/pages src/components src/hooks
rg -n "Actions|Loading|Error|Save|Cancel|Edit|Delete|Create|Update" src/pages src/components
```

**Copy Rules**

- Use Korean for user-facing admin/settings copy.
- Use `Microsoft Teams` for the full integration name in page titles and first mentions.
- Use `Teams` only in compact labels, badges, and table cells.
- Use `저장`, `취소`, `수정`, `삭제`, `비활성화`, `활성화`, `테스트 전송`, `다시 시도` consistently for actions.
- Use `로딩 중...`, `데이터를 불러오지 못했습니다`, and `표시할 데이터가 없습니다` consistently for state copy.
- Do not show fake dates, fake API keys, fake users, or fake service connection statuses.

**Acceptance Criteria**

- No broken-character patterns such as `�`, `ì`, `ë`, `ê`, `Ã`, `Â`, or `ð` remain in user-facing admin/settings files.
- No Slack or KakaoTalk copy remains in the target routes.
- No fake API key examples remain in the implemented settings UI.
- No fake backup history remains in the implemented settings UI.
- Page tests assert at least one stable Korean title or primary action label for each changed route.

**Validation**

```bash
rg -n "�|ì|ë|ê|Ã|Â|ð|Slack|Kakao|카카오|슬랙|sk_live|sk_test|2024-05" src/pages src/components src/hooks
npm run test:run
npm run lint
npm run build
```

---

## Phase 1: User Management

**Objective:** Replace the mocked user list in `SettingsPage` with real user administration, especially user creation.

**Current Problem**

- `SettingsPage` uses `mockUsers`.
- The `사용자 추가`, `수정`, and `비활성화` buttons are UI-only.

**Implementation Goals**

- Add an API-backed user list.
- Add user creation modal.
- Add user edit modal.
- Add user activate/deactivate flow with confirmation.
- Support role selection.
- Support scope metadata enough for current auth model: global, center IDs, warehouse IDs.
- Show loading, empty, error, success, and validation states.

**Suggested Files**

- Modify: `src/pages/SettingsPage.tsx`
- Create: `src/types/adminUser.ts`
- Create: `src/hooks/useAdminUsers.ts`
- Test: `src/pages/SettingsPage.test.tsx` or focused component tests if the page becomes large

**Suggested API Contract**

```text
GET    /v1/admin/users
POST   /v1/admin/users
PUT    /v1/admin/users/{id}
POST   /v1/admin/users/{id}/activate
POST   /v1/admin/users/{id}/deactivate
```

**Suggested Types**

```ts
export type AdminUserRole = 'ADMIN' | 'MANAGER' | 'OPERATOR' | 'AUDITOR'

export interface AdminUser {
  id: number
  name: string
  email: string
  role: AdminUserRole
  active: boolean
  scopeMetadata?: {
    global: boolean
    centerIds: number[]
    warehouseIds: number[]
  }
  createdAt?: string
  updatedAt?: string
}

export interface AdminUserRequest {
  name: string
  email: string
  role: AdminUserRole
  password?: string
  scopeMetadata: {
    global: boolean
    centerIds: number[]
    warehouseIds: number[]
  }
}
```

**Acceptance Criteria**

- `mockUsers` is removed.
- Admin can create a user from `/settings`.
- Admin can edit name, role, active scope metadata, and related center/warehouse scope where available.
- Admin can deactivate and reactivate users.
- Validation prevents empty name, invalid email, missing role, and missing password for new users if password is required.
- Failed API calls show recoverable errors.

**Validation**

```bash
npm run test:run -- src/pages/SettingsPage.test.tsx
npm run lint
npm run build
```

---

## Phase 2: Microsoft Teams Notification Settings

**Objective:** Make Teams the only external notification integration in the settings scope.

**Current Problem**

- `SettingsPage` shows Slack and KakaoTalk examples.
- Notification-channel functionality exists separately, but the settings page still communicates multiple external integrations.

**Implementation Goals**

- Remove Slack and KakaoTalk planning/UI from settings.
- Present Microsoft Teams as the external notification integration.
- Allow Teams webhook configuration.
- Allow alert-type selection for Teams.
- Allow center/warehouse scoping where current notification channel settings support it.
- Add test webhook action.
- Display enabled/disabled status and last test result where the API returns it.

**Suggested Files**

- Modify: `src/pages/SettingsPage.tsx`
- Modify: `src/pages/settings/NotificationChannelPage.tsx`
- Modify: `src/hooks/useNotificationChannelConfigs.ts`
- Modify: `src/types/notificationChannel.ts`
- Test: `src/pages/settings/NotificationChannelPage.test.tsx`

**Suggested API Contract**

```text
GET    /v1/notification-channel-configs?providerType=TEAMS
POST   /v1/notification-channel-configs
PUT    /v1/notification-channel-configs/{id}
DELETE /v1/notification-channel-configs/{id}
POST   /v1/notification-channel-configs/{id}/test-webhook
```

**Suggested Teams Payload**

```ts
export interface TeamsNotificationChannelRequest {
  providerType: 'TEAMS'
  webhookUrl: string
  alertTypes: string[]
  enabled: boolean
  centerId?: number | null
  warehouseId?: number | null
}
```

**Acceptance Criteria**

- Settings no longer shows Slack or KakaoTalk as planned integrations.
- Microsoft Teams is the only external-service integration shown.
- Teams webhook can be created, updated, deleted, enabled, disabled, and test-sent.
- Test webhook success/failure is visible.
- Offline state disables Teams mutation actions.

**Validation**

```bash
npm run test:run -- src/pages/settings/NotificationChannelPage.test.tsx
npm run lint
npm run build
```

---

## Phase 3: Notice Management Completion

**Objective:** Complete notice CRUD so the admin page can manage notices end to end.

**Current Problem**

- Notice create and delete exist.
- Edit button has no action.
- Active/inactive status is displayed but not managed.

**Implementation Goals**

- Add notice edit flow.
- Add active/inactive toggle.
- Add notice type selection.
- Add title/content validation.
- Add visible success/failure feedback.
- Refresh admin dashboard notice summaries after notice mutations.

**Suggested Files**

- Modify: `src/pages/admin/NoticeManagement.tsx`
- Consider Create: `src/types/notice.ts`
- Test: `src/pages/admin/NoticeManagement.test.tsx`

**Suggested API Contract**

```text
GET    /v1/notices
GET    /v1/notices/active
POST   /v1/notices
PUT    /v1/notices/{id}
DELETE /v1/notices/{id}
POST   /v1/notices/{id}/activate
POST   /v1/notices/{id}/deactivate
```

**Acceptance Criteria**

- Pencil button opens an edit form with the selected notice data.
- Saving an edited notice calls the update endpoint.
- Notice active state can be toggled.
- Empty title and empty content are blocked before API submission.
- Delete confirmation remains in place.

**Validation**

```bash
npm run test:run -- src/pages/admin/NoticeManagement.test.tsx
npm run lint
npm run build
```

---

## Phase 4: Audit Log Viewer

**Objective:** Replace the empty local audit log array with a real audit log search screen.

**Current Problem**

- `AuditLogViewer` initializes `logs` to an empty array.
- There is no API query, filter, pagination, or detail display.

**Implementation Goals**

- Fetch audit logs from the backend.
- Add date range filters.
- Add actor, action, and target filters.
- Add pagination.
- Add loading, empty, and error states.
- Show useful audit details: actor, action, target, target ID, IP address, timestamp.
- Optionally add CSV export if backend or frontend-only export is acceptable.

**Suggested Files**

- Modify: `src/pages/admin/AuditLogViewer.tsx`
- Create: `src/types/auditLog.ts`
- Create: `src/hooks/useAuditLogs.ts`
- Test: `src/pages/admin/AuditLogViewer.test.tsx`

**Suggested API Contract**

```text
GET /v1/admin/audit-logs?page=0&size=20&actor=&action=&target=&from=&to=
```

**Suggested Types**

```ts
export interface AuditLog {
  id: number
  actor: string
  action: string
  target: string
  targetId?: string
  ipAddress?: string
  userAgent?: string
  createdAt: string
}

export interface AuditLogFilter {
  page: number
  size: number
  actor?: string
  action?: string
  target?: string
  from?: string
  to?: string
}
```

**Acceptance Criteria**

- `/admin/audit-logs` loads audit data from API.
- Filters trigger a refetch.
- Pagination works.
- Empty state clearly says no logs matched the filter.
- API failures show a retry action.

**Validation**

```bash
npm run test:run -- src/pages/admin/AuditLogViewer.test.tsx
npm run lint
npm run build
```

---

## Phase 5: Admin Dashboard Real Metrics

**Objective:** Remove placeholder admin dashboard cards and show real administrator operating metrics.

**Current Problem**

- System log count is `-`.
- Menu count is hardcoded to `12`.
- Dashboard only partially reflects backend data.

**Implementation Goals**

- Add dashboard summary query.
- Show total users.
- Show inactive users.
- Show active notices.
- Show recent audit log count.
- Show Microsoft Teams channel status.
- Show recent notices.
- Show recent audit logs.

**Suggested Files**

- Modify: `src/pages/admin/AdminPage.tsx`
- Create: `src/hooks/useAdminDashboard.ts`
- Create: `src/types/adminDashboard.ts`
- Test: `src/pages/admin/AdminPage.test.tsx`

**Suggested API Contract**

```text
GET /v1/admin/dashboard/summary
GET /v1/admin/audit-logs?size=5
GET /v1/notices/active
GET /v1/notification-channel-configs?providerType=TEAMS
```

**Suggested Summary Type**

```ts
export interface AdminDashboardSummary {
  totalUsers: number
  inactiveUsers: number
  activeNotices: number
  auditLogCountToday: number
  teamsChannelEnabled: boolean
}
```

**Acceptance Criteria**

- Placeholder `-` and hardcoded `12` are removed.
- Dashboard cards are backed by API data.
- Teams status is visible.
- Recent audit logs link to `/admin/audit-logs`.
- Recent notices link to `/admin/notices`.

**Validation**

```bash
npm run test:run -- src/pages/admin/AdminPage.test.tsx
npm run lint
npm run build
```

---

## Phase 6: General Settings and Role Permissions

**Objective:** Implement the remaining settings tabs as real persisted admin configuration.

**Current Problem**

- General settings fields are static defaults.
- Permission checkboxes use hardcoded role/feature arrays and do not persist.

**Implementation Goals**

- Load and save general admin settings.
- Load and save role-permission matrix.
- Keep sidebar route visibility consistent with saved role policies if backend supports it.
- If dynamic route permissions are not supported yet, persist the matrix as admin-visible configuration and leave actual route guard integration for a follow-up.

**Suggested Files**

- Modify: `src/pages/SettingsPage.tsx`
- Create: `src/hooks/useAdminSettings.ts`
- Create: `src/hooks/useRolePermissions.ts`
- Create: `src/types/adminSettings.ts`
- Test: `src/pages/SettingsPage.test.tsx`

**Suggested API Contract**

```text
GET /v1/admin/settings
PUT /v1/admin/settings
GET /v1/admin/roles/permissions
PUT /v1/admin/roles/permissions
```

**Acceptance Criteria**

- General settings load from API.
- Save persists general settings.
- Permission matrix loads from API.
- Save persists permission matrix.
- Save failures show recoverable errors.

**Validation**

```bash
npm run test:run -- src/pages/SettingsPage.test.tsx
npm run lint
npm run build
```

---

## Out of Scope for This Plan

- Slack integration
- KakaoTalk integration
- Generic API key management
- Backup and restore implementation
- Full dynamic route guard rewrite unless role-permission backend is ready
- Non-admin inventory workflow improvements such as FEFO explanation, outbound draft cleanup, and inventory transfer cancellation reason

These can be handled in later dedicated plans after the admin/settings console is functional.

---

## Final Verification

Run after all phases:

```bash
rg -n "�|ì|ë|ê|Ã|Â|ð|Slack|Kakao|카카오|슬랙|sk_live|sk_test|2024-05" src/pages src/components src/hooks
npm run lint
npm run build
npm run test:run
```

Recommended route checks:

```text
/settings
/settings/notification-channels
/admin
/admin/notices
/admin/audit-logs
```

Recommended smoke scenarios:

- Admin creates a user.
- Admin edits a user.
- Admin deactivates and reactivates a user.
- Admin creates a Teams notification channel.
- Admin sends a Teams test webhook.
- Admin creates, edits, deactivates, and deletes a notice.
- Admin searches audit logs by date and actor.
- Admin dashboard loads real summary values.
- Admin/settings pages do not show broken Korean text, fake API keys, fake users, fake backup history, Slack copy, or KakaoTalk copy.

---

## Execution Recommendation

Start with Phase 0.5, Phase 1, and Phase 2. Broken text cleanup, user management, and Teams notification settings produce immediate value and remove the largest mock surfaces from `/settings`.

After that, implement Phase 3 through Phase 5 together as the admin-console completion slice: notices, audit logs, and dashboard metrics.
