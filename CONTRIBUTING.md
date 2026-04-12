# Contributing to SupraMAS

Thank you for considering contributing to **SupraMAS** (Supervisor Multi-Agent System)! This document provides guidelines and instructions for contributing to this project.

---

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Workflow](#-development-workflow)
- [Coding Standards](#-coding-standards)
- [Testing Guidelines](#-testing-guidelines)
- [Documentation](#-documentation)
- [Submitting Changes](#-submitting-changes)
- [Pull Request Process](#-pull-request-process)

---

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We are committed to providing a welcoming and harassment-free experience for everyone.

### Our Pledge

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 20.10+ (optional, for containerized development)
- **Git**: Latest version
- **Code Editor**: VS Code (recommended) with extensions:
  - Python (Microsoft)
  - ESLint
  - Prettier
  - EditorConfig

### Setup Development Environment

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then clone your fork
git clone https://github.com/{your-username}/SupraMAS.git
cd SupraMAS

# Add upstream remote
git remote add upstream https://github.com/liuyang0508/SupraMAS.git
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks (if configured)
pre-commit install
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. Docker Environment (Optional)

```bash
cd docker
docker-compose -f docker-compose.dev.yml up -d
```

---

## 🔨 Development Workflow

### Branch Naming Convention

We follow a structured branch naming system:

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feature/` | `feature/add-memory-agent` |
| Bugfix | `bugfix/` | `bugfix/fix-routing-error` |
| Hotfix | `hotfix/` | `hotfix/security-patch` |
| Documentation | `docs/` | `docs/update-api-docs` |
| Refactor | `refactor/` | `refactor/optimize-rag-retrieval` |
| Test | `test/` | `test/add-unit-tests-for-dispatcher` |

### Git Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without feature changes or bug fixes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

#### Examples

```bash
# Good examples
feat(agent): add memory subagent with long-term storage capability
fix(supervisor): resolve race condition in task dispatcher
docs(readme): update installation instructions for macOS
test(domain): add unit tests for ecommerce agent workflows
refactor(rag): optimize hybrid retrieval algorithm performance

# Bad examples (avoid these)
"fixed bug"
"update stuff"
"wip"
"asdfghjkl"
```

### Workflow Steps

1. **Create a branch** from `main`
   ```bash
   git checkout -b feature/amazing-feature main
   ```

2. **Make your changes** following coding standards

3. **Test your changes** thoroughly

4. **Commit your changes** with clear messages
   ```bash
   git commit -m "feat(component): add amazing feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**

7. **Address review feedback** if needed

8. **Merge after approval** (maintainers will handle this)

---

## 📏 Coding Standards

### Python (Backend)

Follow [PEP 8](https://pep8.org/) style guide:

```python
# ✅ Good: Clear naming, type hints, docstrings
from typing import Optional, List
from pydantic import BaseModel


class UserInput(BaseModel):
    """Represents user input to the Supervisor."""

    user_id: str
    content: str
    input_type: str = "text"

    def validate_content(self) -> bool:
        """Validate input content length and format."""
        return len(self.content) > 0 and len(self.content) <= 10000


async def process_input(
    input_data: UserInput,
    context: Optional[ConversationContext] = None
) -> SupervisorResponse:
    """
    Process user input through the supervisor pipeline.

    Args:
        input_data: Validated user input object
        context: Optional conversation context for multi-turn dialogue

    Returns:
        SupervisorResponse containing generated content and metadata
    """
    # Implementation here
    pass
```

#### Key Rules:

- Maximum line length: **120 characters**
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions/classes
- Use **f-strings** for string formatting (not `.format()` or `%`)
- Import order: **stdlib → third-party → local**
- Use **absolute imports** over relative imports

### TypeScript/React (Frontend)

Follow [Airbnb Style Guide](https://airbnb.io/javascript/react/) with TypeScript:

```tsx
// ✅ Good: Functional components, hooks, proper types
import React, { useState, useCallback } from 'react';
import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
  onAction?: (actionId: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onAction,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const handleAction = useCallback((actionId: string) => {
    if (onAction) {
      onAction(actionId);
    }
  }, [onAction]);

  return (
    <div className="chat-message">
      <p>{message.content}</p>
      {message.actions?.map((action) => (
        <button
          key={action.id}
          onClick={() => handleAction(action.id)}
          type="button"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
};
```

#### Key Rules:

- Use **functional components** with hooks (no class components)
- Use **TypeScript strict mode** - no `any` types
- Component names: **PascalCase**, file names: **PascalCase.tsx**
- Utility functions: **camelCase.ts**
- Prefer **const** over **let**, avoid **var**
- Use **destructuring** for props and state

### Configuration Files

- **YAML/JSON**: 2-space indentation
- **Dockerfile**: Follow best practices (multi-stage builds, non-root user)
- **Shell scripts**: POSIX-compliant, use `#!/usr/bin/env bash`

---

## 🧪 Testing Guidelines

### Backend Tests (Python)

Use **pytest** with **pytest-asyncio** for async code:

```python
# tests/test_supervisor.py
import pytest
from core.supervisor import WukongSupervisor
from core.supervisor.state import SupervisorState


class TestWukongSupervisor:
    """Test suite for Supervisor orchestration."""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor instance for testing."""
        config = {
            "input_router": {"mode": "rule_based"},
            "query_optimizer": {"context_window_size": 5},
            "task_planner": {"max_task_depth": 2},
            "dispatcher": {"scheduling_strategy": "round_robin"},
            "security": {"enable_permission_intersection": False}
        }
        return WukongSupervisor(config)

    @pytest.mark.asyncio
    async def test_process_user_input(self, supervisor):
        """Test basic user input processing."""
        # Arrange
        user_input = UserInput(
            user_id="test-user",
            content="Hello SupraMAS",
            input_type="text"
        )

        # Act
        response = await supervisor.process_user_input(
            user_input=user_input,
            context=None
        )

        # Assert
        assert response.success is True
        assert response.content is not None
        assert response.trace_id is not None
```

#### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=core --cov-report=html

# Run specific test file
pytest tests/test_supervisor.py::TestWukongSupervisor::test_process_user_input -v
```

### Frontend Tests (TypeScript)

Use **Vitest** + **React Testing Library**:

```tsx
// src/components/__tests__/ChatInterface.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ChatInterface } from '../chat/ChatInterface';

describe('ChatInterface', () => {
  it('renders chat messages correctly', () => {
    const messages = [
      { role: 'assistant', content: 'Hello! How can I help?' },
      { role: 'user', content: 'I need help with e-commerce' }
    ];

    render(<ChatInterface messages={messages} />);

    expect(screen.getByText('Hello! How can I help?')).toBeInTheDocument();
    expect(screen.getByText('I need help with e-commerce')).toBeInTheDocument();
  });

  it('calls onSubmit when send button is clicked', async () => {
    const user = userEvent.setup();
    const mockSubmit = vi.fn();

    render(<ChatInterface onSubmit={mockSubmit} />);

    const input = screen.getByPlaceholderText('Type your message...');
    const button = screen.getByRole('button', { name: /send/i });

    await user.type(input, 'Test message');
    await user.click(button);

    expect(mockSubmit).toHaveBeenCalledWith('Test message');
  });
});
```

#### Running Tests

```bash
# Frontend tests
cd frontend
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Core Supervisor | 80%+ |
| SubAgents | 75%+ |
| Domain Agents | 70%+ |
| API Endpoints | 85%+ |
| React Components | 70%+ |

---

## 📝 Documentation

### Code Documentation

- All **public functions/methods** must have docstrings
- Use **Google-style docstrings** for Python
- Use **JSDoc** comments for TypeScript

### API Documentation

Update OpenAPI/Swagger docs in `main.py` when adding new endpoints:

```python
@app.post("/api/v1/new-endpoint")
async def new_endpoint(request: NewRequest):
    """
    Brief description of what this endpoint does.

    More detailed explanation if needed.

    Args:
        request: Description of request body

    Returns:
        Response model description

    Raises:
        HTTPException: When and why this error occurs

    Example:
        >>> Request JSON structure
        >>> Response JSON structure
    """
    pass
```

### README Updates

When adding major features:
1. Update **Features** section
2. Add to **Tech Stack** table if using new technology
3. Update **Project Statistics**
4. Add **screenshots/GIFs** if UI changes

---

## 📤 Submitting Changes

### Before Submitting

Run through this checklist:

- [ ] Code follows project style guidelines
- [ ] Self-review completed (read your own code!)
- [ ] Comments added for complex logic
- [ ] Documentation updated (docstrings, README, etc.)
- [ ] New features include tests
- [ ] All tests pass locally (`pytest`, `npm test`)
- [ ] No new warnings or errors introduced
- [ ] Docker build succeeds (`docker build -t supramas .`)

### Pull Request Template

When opening a PR, fill out the template completely:

```markdown
## Description
[Clear description of changes]

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
[Describe testing performed and how to verify]

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed self-review
- [ ] I have commented my code where necessary
- [ ] I have updated documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix works
- [ ] Any dependent changes have been merged
```

---

## 🔀 Pull Request Process

### Review Criteria

Maintainers will review PRs based on:

1. ✅ **Code Quality**: Clean, readable, well-documented code
2. ✅ **Test Coverage**: Adequate tests for new functionality
3. ✅ **Performance**: No significant regressions
4. ✅ **Security**: No vulnerabilities introduced
5. ✅ **Documentation**: Updated docs and inline comments
6. ✅ **Consistency**: Matches existing codebase patterns

### Merge Requirements

- At least **1 maintainer approval** required
- All CI checks must **pass** (tests, linting, build)
- No **merge conflicts**
- Discussion threads **resolved**

### After Merge

- Delete your feature branch (keep repo clean)
- Update your fork's `main` branch:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

---

## 🐛 Reporting Bugs

Found a bug? Please open an issue with:

1. **Clear title** describing the bug
2. **Steps to reproduce** the issue
3. **Expected behavior** vs **actual behavior**
4. **Screenshots** if applicable
5. **Environment details** (OS, Python version, Node version, etc.)

Use our **Bug Report template** for consistent issue reporting.

---

## 💡 Suggesting Features

Have an idea? We'd love to hear it!

1. Check existing issues to avoid duplicates
2. Open a **Feature Request** with:
   - Clear problem statement
   - Proposed solution (if you have one)
   - Use cases and benefits
   - Mockups/wireframes (for UI features)

---

## 🙏 Recognition

Contributors will be recognized in:
- **README.md** Contributors section
- **Release notes** for significant contributions
- **GitHub's Contributors graph** automatically

Thank you for making SupraMAS better! 🎉

---

## ❓ Questions?

- Open a **Discussion** for general questions
- Check existing **Issues** and **Discussions** first
- Maintainers will respond as soon as possible

**Happy contributing!** 🚀
