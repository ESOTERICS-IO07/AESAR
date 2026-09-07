# Development Workflow

## TEAM OWNERSHIP

- **Person 1**: `feature/hardware-integration`
- **Person 2**: `feature/vision-ai`
- **Person 3**: `feature/ecosystem-intelligence`
- **Person 4**: `feature/mission-dashboard`

## Git Workflow

```text
feature branch
    ↓
commit
    ↓
push
    ↓
Pull Request
    ↓
integration
    ↓
test
    ↓
main
```

## Teammate Instructions

Clone the repository and get the integration branch:
```bash
git clone <REPOSITORY_URL>
cd AESAR
git fetch origin
git checkout integration
git pull origin integration
```

### Person 2
```bash
git checkout -b feature/vision-ai
git push -u origin feature/vision-ai
```

### Person 3
```bash
git checkout -b feature/ecosystem-intelligence
git push -u origin feature/ecosystem-intelligence
```

### Person 4
```bash
git checkout -b feature/mission-dashboard
git push -u origin feature/mission-dashboard
```

**IMPORTANT**: NEVER branch from another person's feature branch!

## PR Rules

- PRs target `integration`.
- `main` is only updated from `integration`.
- PR descriptions must explain:
  - what changed
  - files changed
  - interface changes
  - testing performed
  - integration impact
- Avoid giant PRs.
- Keep commits meaningful.
- Do not modify another team's subsystem unless necessary.
- If an interface must change, update `docs/INTERFACES.md` and inform the integration owner.

### Recommended Commit Style
- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`
- `chore:`

Examples:
- `feat: add MPU6050 telemetry`
- `feat: implement YOLO detection pipeline`
- `feat: implement AMRI calculation`
- `feat: add station mission state machine`
- `fix: handle stale sensor telemetry`
