# Gyanova AI Tutor App - Core Instructions

**Tech Stack**: Next.js 15 (frontend) + Python FastAPI (backend) + LangGraph/LangSmith (AI workflows)

**Monorepo Structure**:
- `app/` → Next.js frontend
- `apps/api-server/` → Python FastAPI backend
- `apps/web/` → Web components
- `components/` → Shared React components

---

## 🚀 Load Instructions on Demand

This guide uses **modular instructions** loaded only when needed. No context bloat.

### Decision Tree - Which instructions to load?

| Task | Load This |
|------|-----------|
| Working in `app/`, `components/`, `*.tsx`, `*.jsx` | `nextjs-development.md` |
| Working in `apps/api-server/`, `*.py` API code | `fastapi-development.md` |
| General project standards, naming, patterns | `project-standards.md` |
| Uncertain? | Check `/memories/repo/quick-reference.md` |

---

## 🔧 Quick Reference (Always Apply)

### Project Structure
```
Frontend → app/ (Next.js App Router)
Backend  → apps/api-server/ (FastAPI + LangGraph)
Shared   → components/, lib/
Config   → .github/ (instructions, agents, prompts)
```

### Naming Conventions
- **Files**: kebab-case (`lesson-content.tsx`, `student-service.py`)
- **Components**: PascalCase (`LessonCard.tsx`, `StudentDashboard.tsx`)
- **Functions/vars**: camelCase (`getUserLessons()`, `studentProgress`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `MAX_RETRIES`)

### Tech Stack Rules
- **Frontend**: React 19 (Server Components when possible), TypeScript, Tailwind CSS
- **Backend**: FastAPI, async/await, Pydantic models
- **AI**: LangGraph workflows, LangSmith tracing (auto-enabled)

---

## 📋 Development Workflow

### Starting Development
```bash
npm run dev:all  # Starts both web (3000) and API (8000)
```

### File Routing (Frontend)
- `app/page.tsx` → `/`
- `app/lesson/[id]/page.tsx` → `/lesson/:id`
- `app/api/lesson/route.ts` → `POST /api/lesson`

### API Development (Backend)
- Endpoints in `apps/api-server/app/routes/`
- Models in `apps/api-server/app/models/`
- Services in `apps/api-server/app/services/`
- All requests auto-traced to LangSmith

---

## 🔍 When Adding Features

1. **Check existing patterns** in the codebase first (don't reinvent)
2. **Load domain instructions** using the decision tree above
3. **Reference `/memories/repo/`** for common patterns
4. **Test locally** before committing

---

## ⚠️ Critical Rules (Always Follow)

- ✅ Use TypeScript everywhere (frontend + backend types)
- ✅ Single Responsibility Principle (one module = one job)
- ✅ Async/await in Python (never blocking I/O)
- ✅ Server Components by default in Next.js (client: only when interactive)
- ✅ Error handling: catch, log, return meaningful messages
- ✅ Environment variables: use `.env`, never commit secrets

---

## 📚 Domain-Specific Instructions

Need detailed guidance? Load the appropriate file:
- [Next.js Development](./instructions/nextjs-development.md)
- [FastAPI Development](./instructions/fastapi-development.md)
- [Project Standards & Patterns](./instructions/project-standards.md)

---

*Last updated: March 2026 | Keep this file ≤200 lines for efficient context usage*

---

## ⚠️ DEPRECATED - Code Review Guidance Below (Archive Only)

## README updates

- [ ] The new file should be added to the `docs/README.<type>.md`.

## Prompt file guide

**Only apply to files that end in `.prompt.md`**

- [ ] The prompt has markdown front matter.
- [ ] The prompt has a `agent` field specified of either `agent`, `ask`, or `Plan`.
- [ ] The prompt has a `description` field.
- [ ] The `description` field is not empty.
- [ ] The file name is lower case, with words separated by hyphens.
- [ ] Encourage the use of `tools`, but it's not required.
- [ ] Strongly encourage the use of `model` to specify the model that the prompt is optimised for.
- [ ] Strongly encourage the use of `name` to set the name for the prompt.

## Instruction file guide

**Only apply to files that end in `.instructions.md`**

- [ ] The instruction has markdown front matter.
- [ ] The instruction has a `description` field.
- [ ] The `description` field is not empty.
- [ ] The file name is lower case, with words separated by hyphens.
- [ ] The instruction has an `applyTo` field that specifies the file or files to which the instructions apply. If they wish to specify multiple file paths they should formatted like `'**.js, **.ts'`.

## Agent file guide

**Only apply to files that end in `.agent.md`**

- [ ] The agent has markdown front matter.
- [ ] The agent has a `description` field.
- [ ] The `description` field is not empty.
- [ ] The file name is lower case, with words separated by hyphens.
- [ ] Encourage the use of `tools`, but it's not required.
- [ ] Strongly encourage the use of `model` to specify the model that the agent is optimised for.
- [ ] Strongly encourage the use of `name` to set the name for the agent.

## Agent Skills guide

**Only apply to folders in the `skills/` directory**

- [ ] The skill folder contains a `SKILL.md` file.
- [ ] The SKILL.md has markdown front matter.
- [ ] The SKILL.md has a `name` field.
- [ ] The `name` field value is lowercase with words separated by hyphens.
- [ ] The `name` field matches the folder name.
- [ ] The SKILL.md has a `description` field.
- [ ] The `description` field is not empty, at least 10 characters, and maximum 1024 characters.
- [ ] The `description` field value is wrapped in single quotes.
- [ ] The folder name is lower case, with words separated by hyphens.
- [ ] Any bundled assets (scripts, templates, data files) are referenced in the SKILL.md instructions.
- [ ] Bundled assets are reasonably sized (under 5MB per file).

## Plugin guide

**Only apply to directories in the `plugins/` directory**

- [ ] The plugin directory contains a `.github/plugin/plugin.json` file.
- [ ] The plugin directory contains a `README.md` file.
- [ ] The plugin.json has a `name` field matching the directory name.
- [ ] The plugin.json has a `description` field.
- [ ] The `description` field is not empty.
- [ ] The directory name is lower case, with words separated by hyphens.
- [ ] If `tags` is present, it is an array of lowercase hyphenated strings.
- [ ] If `items` is present, each item has `path` and `kind` fields.
- [ ] The `kind` field value is one of: `prompt`, `agent`, `instruction`, `skill`, or `hook`.
- [ ] The plugin does not reference non-existent files.
