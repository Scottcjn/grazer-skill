# Contributing Guide

Thank you for contributing to Grazer! 🎉

## Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/grazer-skill.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Test** your changes
6. **Commit** with clear messages
7. **Push** to your fork
8. **Open a Pull Request**

## Development Setup

```bash
# Python development
pip install -e .

# Node.js development  
npm install

# Run tests
npm test
# or
python -m pytest
```

## Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **JavaScript/TypeScript**: Follow ESLint config, use Prettier
- Write clear, readable code with appropriate comments
- Use meaningful variable and function names

## Commit Messages

We follow conventional commit messages:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation is updated (if needed)
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains what and why

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #ISSUE_NUMBER

## Testing
How to test these changes

## Checklist
- [ ] Code reviewed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Works on my machine (tested locally)
```

## Bug Reports

When reporting bugs, please include:

1. **Steps to reproduce** - Specific, numbered steps
2. **Expected behavior** - What should happen
3. **Actual behavior** - What actually happened
4. **Environment** - OS, Python/Node version, Grazer version
5. **Screenshots/Logs** - If applicable

Use the [Bug Report template](ISSUE_TEMPLATE.md)!

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues to avoid duplicates
2. Describe the feature and use case clearly
3. Explain why it's valuable for users
4. Consider API design impact

## Platform-Specific Notes

### BoTTube Integration
- Requires API key from bottube.ai
- Test with `--dry-run` flag first

### Moltbook Integration  
- Requires API key from moltbook.com
- Check rate limits in INTEGRATION.md

### ClawHub Skills
- Use `/skills add grazer` in Claude Code
- Report skill issues to clawhub.ai

## Questions?

- Check existing issues and documentation
- Open a new issue for questions
- Join the community discussions

---

Thanks for contributing! Every contribution makes this project better. 🚀
