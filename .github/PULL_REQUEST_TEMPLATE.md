# Pull Request Template

## 📝 Description

<!-- Provide a clear and concise description of the changes in this PR -->
<!-- Include what problem this solves and how -->

Related Issue: Closes #[issue number]

---

## 🔄 Type of Change

Please delete options that are not relevant:

- [ ] 🐛 **Bug fix** (non-breaking change which fixes an issue)
- [ ] ✨ **New feature** (non-breaking change which adds functionality)
- [ ] 💥 **Breaking change** (fix or feature that would cause existing functionality to not work as expected)
- [ ] 🔧 **Refactor** (code restructuring without changing functionality)
- [ ] ⚡ **Performance improvement** (optimization without changing behavior)
- [ ] 📖 **Documentation update** (docs, comments, README changes)

---

## 🧪 Testing

### How Has This Been Tested?

<!-- Describe the tests you ran to verify your changes -->

**Test Environment:**
- OS: [e.g., macOS Sonoma 14.2]
- Python: [e.g., 3.11.6]
- Node.js: [e.g., 20.10.0]

**Test Cases:**

1. **Test Case 1: [Description]**
   - Steps: [What did you do?]
   - Expected: [What should happen?]
   - Actual: [What happened?]
   - Status: ✅ Pass / ❌ Fail

2. **Test Case 2: [Description]**
   - Steps:
   - Expected:
   - Actual:
   - Status: ✅ Pass / ❌ Fail

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass locally (`pytest`, `npm test`)

---

## 📸 Screenshots (if applicable)

<!-- Add screenshots for UI/frontend changes -->

### Before
<!-- Add screenshot of before state -->

### After
<!-- Add screenshot of after state -->

---

## ✅ Checklist

### Code Quality

- [ ] My code follows the project's coding style guidelines ([CONTRIBUTING.md](../CONTRIBUTING.md))
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors
- [ ] I have checked for security vulnerabilities (no hardcoded secrets, proper input validation)

### Backend Specific

- [ ] Python code follows PEP 8 style guide
- [ ] Type hints are used for all function signatures
- [ ] Docstrings are present for public functions/classes
- [ ] API endpoints updated with OpenAPI/Swagger docs
- [ ] Database migrations included (if schema changed)

### Frontend Specific

- [ ] TypeScript strict mode enabled (no `any` types)
- [ ] Components follow React best practices (functional components + hooks)
- [ ] Responsive design tested on different screen sizes
- [ ] Accessibility considerations addressed (ARIA labels, keyboard navigation)

### DevOps & Deployment

- [ ] Docker build succeeds: `docker build -t supramas-test .`
- [ ] No breaking changes to environment variables
- [ ] Dependencies updated in `requirements.txt` / `package.json`
- [ ] New configuration documented in README

---

## 🔗 Related Issues / PRs

<!-- Link any related issues or pull requests -->

- Related: #[issue number]
- Blocks: #[PR number]
- Blocked by: #[issue number]

---

## 📚 Additional Notes

<!-- Add any additional context for reviewers here -->

### Key Changes Summary

1. **Change 1**: [Brief description]
2. **Change 2**: [Brief description]
3. **Change 3**: [Brief description]

### Potential Risks

- [ ] Risk 1: [Description and mitigation]
- [ ] Risk 2: [Description and mitigation]

### Performance Impact

- [ ] No performance impact expected
- [ ] Minor performance improvement/degradation
- [ ] Significant performance change (please describe):
  <!-- Describe performance impact with benchmarks if available -->

---

## 👀 Reviewers

<!-- @mention specific reviewers if needed -->

@liuyang0508

---

## 🙏 Acknowledgments

<!-- Credit anyone who helped you or inspired this change -->

---

> **Note**: Please ensure all CI checks pass before requesting review. Maintainers will review within 48 hours.
