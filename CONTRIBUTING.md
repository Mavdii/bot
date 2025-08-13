# Contributing to Islamic Azkar Telegram Bot

Thank you for your interest in contributing to this project! We welcome contributions from developers of all skill levels.

## 🤝 How to Contribute

### 1. Fork and Clone

```bash
git clone https://github.com/Mavdii/bot.git
cd bot
```

### 2. Set Up Development Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass

### 5. Test Your Changes

```bash
# Run tests
pytest

# Check code style
black src/
flake8 src/

# Type checking
mypy src/
```

### 6. Submit a Pull Request

- Write a clear description of your changes
- Reference any related issues
- Ensure CI passes

## 📝 Code Style Guidelines

### Python Code Style

- Follow PEP 8
- Use Black for formatting
- Maximum line length: 88 characters
- Use type hints
- Write docstrings for all functions and classes

### Commit Messages

Use conventional commit format:

```
type(scope): description

feat(admin): add new content management feature
fix(scheduler): resolve timezone handling issue
docs(readme): update installation instructions
```

### Documentation

- Write clear docstrings in Arabic and English
- Update README.md for new features
- Add inline comments for complex logic
- Include examples in docstrings

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new features
- Use pytest framework
- Mock external dependencies
- Aim for >80% code coverage

### Test Structure

```python
def test_feature_name():
    """Test description in Arabic and English"""
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_value
```

## 🐛 Bug Reports

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- Minimal code example

## 💡 Feature Requests

For feature requests, please provide:

- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Any relevant examples or mockups

## 📋 Development Setup

### Required Tools

- Python 3.11+
- Git
- Code editor (VS Code recommended)

### Recommended VS Code Extensions

- Python
- Black Formatter
- Flake8
- MyPy
- GitLens

### Environment Variables

Create a `.env` file for development:

```env
BOT_TOKEN=your_test_bot_token
ADMIN_ID=your_telegram_id
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🔍 Code Review Process

### What We Look For

- Code quality and readability
- Test coverage
- Documentation completeness
- Performance considerations
- Security best practices

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Security considerations addressed

## 🌍 Internationalization

### Adding New Languages

1. Create language file in `src/azkar_bot/locales/`
2. Follow existing Arabic/English pattern
3. Update constants.py with new messages
4. Test with different locales

### Translation Guidelines

- Maintain respectful Islamic terminology
- Consider cultural context
- Use formal language for religious content
- Provide both transliteration and native script

## 🔒 Security Guidelines

### Sensitive Data

- Never commit tokens or credentials
- Use environment variables
- Sanitize user inputs
- Validate file uploads

### Security Checklist

- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] File upload restrictions in place
- [ ] Error messages don't leak information

## 📚 Resources

### Documentation

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Python Asyncio](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)

### Islamic Resources

- [Fortress of the Muslim](https://www.hisnulmuslim.com/)
- [Sunnah.com](https://sunnah.com/)
- [Quran.com](https://quran.com/)

## 🤲 Islamic Guidelines

### Content Standards

- All Islamic content must be authentic
- Provide sources for Hadith and Quran verses
- Use proper Arabic transliteration
- Respect Islamic etiquette and terminology

### Review Process for Islamic Content

- Verify authenticity of sources
- Check Arabic text accuracy
- Ensure proper attribution
- Review for theological correctness

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Technical questions and bugs
- **GitHub Discussions**: General questions and ideas
- **Email**: [omarelmhdi@gmail.com](mailto:omarelmhdi@gmail.com)
- **Telegram**: [@Mavdiii](https://t.me/Mavdiii)

### Response Times

- Bug reports: 24-48 hours
- Feature requests: 1-2 weeks
- Pull requests: 2-5 days
- General questions: 24 hours

## 🏆 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- Special thanks in documentation

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**جزاكم الله خيراً** - May Allah reward you with good for your contributions! 🤲