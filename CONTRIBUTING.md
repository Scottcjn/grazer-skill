# Contributing to Grazer

Thank you for your interest in contributing to Grazer - the AI agent discovery layer!

## How to Contribute

### Development Setup

```bash
# Clone and install
git clone https://github.com/Scottcjn/grazer-skill.git
cd grazer-skill

# Install dependencies
npm install

# Build TypeScript
npm run build

# Or use Python version
pip install -e .
```

### Adding New Platforms

1. Check `src/` for existing platform implementations
2. Follow the pattern in `clawhub.ts` or `intelligence.ts`
3. Add CLI commands in `src/cli.ts`
4. Update README.md with platform examples

### Code Style

- TypeScript: Follow existing patterns, use interfaces for types
- Python: Use type hints, follow PEP 8
- Add JSDoc comments for public APIs

### Pull Request Process

1. Fork the repo
2. Create a feature branch
3. Add tests if applicable
4. Update documentation
5. Submit PR with description

## Project Structure

- `src/cli.ts` - CLI commands
- `src/agent-loop.ts` - Main discovery loop
- `src/intelligence.ts` - Content scoring
- `src/notifications.ts` - Alert system
- `grazer/` - Python implementation

## License

MIT - see LICENSE file
