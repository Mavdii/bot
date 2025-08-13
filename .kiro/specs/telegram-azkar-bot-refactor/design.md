# Design Document

## Overview

This design document outlines the architectural approach for refactoring the Islamic Azkar Telegram bot into a professional, maintainable, and well-structured Python project. The refactoring will transform a single-file monolithic application into a modular, object-oriented system following Python best practices while preserving all existing functionality.

## Architecture

### High-Level Architecture

The system will follow a layered architecture pattern:

```
telegram-azkar-bot/
├── src/
│   └── azkar_bot/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── bot.py              # Main bot class
│       │   ├── scheduler.py        # Prayer times and scheduling
│       │   └── config.py           # Configuration management
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── admin.py            # Admin command handlers
│       │   ├── messages.py         # Message handlers
│       │   └── callbacks.py        # Callback query handlers
│       ├── services/
│       │   ├── __init__.py
│       │   ├── content_manager.py  # Content management service
│       │   ├── file_manager.py     # File operations service
│       │   └── group_manager.py    # Group management service
│       ├── models/
│       │   ├── __init__.py
│       │   ├── content.py          # Content data models
│       │   └── group.py            # Group data models
│       └── utils/
│           ├── __init__.py
│           ├── logger.py           # Logging configuration
│           ├── helpers.py          # Utility functions
│           └── constants.py        # Application constants
├── data/
│   ├── content/
│   │   ├── azkar.txt
│   │   ├── images/
│   │   ├── voices/
│   │   ├── audios/
│   │   ├── morning/
│   │   ├── evening/
│   │   └── prayers/
│   └── groups/
│       └── active_groups.json
├── tests/
│   ├── __init__.py
│   ├── test_bot.py
│   ├── test_handlers.py
│   └── test_services.py
├── docs/
│   ├── README_AR.md
│   ├── CONTRIBUTING.md
│   ├── CHANGELOG.md
│   └── API.md
├── scripts/
│   ├── setup.sh
│   └── deploy.sh
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── main.py                         # Entry point
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

### Design Patterns

1. **Factory Pattern**: For creating different types of content handlers
2. **Observer Pattern**: For handling bot events and updates
3. **Strategy Pattern**: For different content delivery strategies
4. **Singleton Pattern**: For configuration and logging management

## Components and Interfaces

### Core Components

#### 1. AzkarBot (core/bot.py)
```python
class AzkarBot:
    """Main bot class responsible for initialization and coordination"""
    
    def __init__(self, config: Config)
    async def start(self) -> None
    async def stop(self) -> None
    def setup_handlers(self) -> None
    def setup_scheduler(self) -> None
```

#### 2. ConfigManager (core/config.py)
```python
class Config:
    """Configuration management with environment variables"""
    
    @property
    def bot_token(self) -> str
    @property
    def admin_id(self) -> int
    @property
    def channel_link(self) -> str
    def validate(self) -> bool
```

#### 3. SchedulerManager (core/scheduler.py)
```python
class SchedulerManager:
    """Handles all scheduling operations"""
    
    def setup_prayer_schedule(self) -> None
    def setup_azkar_schedule(self) -> None
    async def send_scheduled_content(self, content_type: str) -> None
```

### Service Layer

#### 1. ContentManager (services/content_manager.py)
```python
class ContentManager:
    """Manages all content operations"""
    
    def get_random_azkar(self) -> str
    def get_random_media(self, media_type: str) -> Optional[MediaContent]
    async def add_content(self, content: Content) -> bool
    def load_azkar_texts(self) -> List[str]
```

#### 2. FileManager (services/file_manager.py)
```python
class FileManager:
    """Handles file operations and media management"""
    
    async def download_file(self, file_id: str, folder: str) -> Optional[str]
    async def save_media_info(self, file_path: str, caption: str) -> None
    def get_random_file(self, folder: str, extensions: List[str]) -> Optional[str]
```

#### 3. GroupManager (services/group_manager.py)
```python
class GroupManager:
    """Manages group operations and persistence"""
    
    def add_group(self, group_id: int) -> None
    def remove_group(self, group_id: int) -> None
    def get_active_groups(self) -> Set[int]
    def save_groups(self) -> None
    def load_groups(self) -> None
```

### Handler Layer

#### 1. AdminHandler (handlers/admin.py)
```python
class AdminHandler:
    """Handles all admin-related commands and operations"""
    
    async def show_admin_panel(self, update: Update, context: CallbackContext)
    async def handle_media_upload(self, update: Update, context: CallbackContext)
    async def add_text_content(self, update: Update, context: CallbackContext)
    async def get_bot_stats(self, update: Update, context: CallbackContext)
```

#### 2. MessageHandler (handlers/messages.py)
```python
class MessageHandler:
    """Handles regular message processing"""
    
    async def handle_start(self, update: Update, context: CallbackContext)
    async def handle_group_message(self, update: Update, context: CallbackContext)
    async def process_new_group(self, update: Update, context: CallbackContext)
```

#### 3. CallbackHandler (handlers/callbacks.py)
```python
class CallbackHandler:
    """Handles callback query processing"""
    
    async def handle_admin_callbacks(self, update: Update, context: CallbackContext)
    async def handle_content_callbacks(self, update: Update, context: CallbackContext)
```

## Data Models

### Content Models (models/content.py)
```python
@dataclass
class Content:
    """Base content model"""
    id: str
    type: ContentType
    created_at: datetime
    caption: Optional[str] = None

@dataclass
class TextContent(Content):
    """Text-based content"""
    text: str

@dataclass
class MediaContent(Content):
    """Media-based content"""
    file_path: str
    file_type: str
    file_size: int

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    AUDIO = "audio"
    DOCUMENT = "document"
```

### Group Models (models/group.py)
```python
@dataclass
class Group:
    """Group information model"""
    id: int
    title: str
    type: str
    added_at: datetime
    is_active: bool = True
    last_activity: Optional[datetime] = None
```

## Error Handling

### Exception Hierarchy
```python
class AzkarBotException(Exception):
    """Base exception for the bot"""
    pass

class ConfigurationError(AzkarBotException):
    """Configuration-related errors"""
    pass

class ContentError(AzkarBotException):
    """Content management errors"""
    pass

class FileOperationError(AzkarBotException):
    """File operation errors"""
    pass
```

### Error Handling Strategy
1. **Graceful Degradation**: Bot continues operating even if some features fail
2. **Comprehensive Logging**: All errors are logged with context
3. **User-Friendly Messages**: Error messages in Arabic for admin users
4. **Retry Mechanisms**: Automatic retry for transient failures
5. **Fallback Content**: Default content when specific content fails to load

## Testing Strategy

### Unit Testing
- Test individual components in isolation
- Mock external dependencies (Telegram API, file system)
- Test error conditions and edge cases
- Achieve >80% code coverage

### Integration Testing
- Test component interactions
- Test with real file system operations
- Test scheduler functionality
- Test database operations

### End-to-End Testing
- Test complete user workflows
- Test admin panel functionality
- Test content delivery pipeline
- Test group management features

### Testing Tools
- **pytest**: Main testing framework
- **pytest-asyncio**: For async test support
- **pytest-mock**: For mocking dependencies
- **coverage.py**: For code coverage reporting

## Configuration Management

### Environment Variables
```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id_here
CHANNEL_LINK=https://t.me/your_channel

# Paths
DATA_DIR=./data
CONTENT_DIR=./data/content
GROUPS_FILE=./data/groups/active_groups.json

# Scheduling
TIMEZONE=Africa/Cairo
RANDOM_CONTENT_INTERVAL=5  # minutes
MORNING_AZKAR_TIMES=05:30,07:00,08:00
EVENING_AZKAR_TIMES=18:00,19:00,20:00

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/azkar_bot.log
```

### Configuration Validation
- Validate all required environment variables on startup
- Provide clear error messages for missing configuration
- Support default values for optional settings
- Validate file paths and permissions

## Security Considerations

### Data Protection
- Store sensitive configuration in environment variables
- Never commit tokens or credentials to version control
- Implement proper file permissions for data directories
- Sanitize user inputs to prevent injection attacks

### Access Control
- Verify admin permissions for sensitive operations
- Implement rate limiting for API calls
- Validate file uploads and types
- Restrict file system access to designated directories

### Logging Security
- Avoid logging sensitive information
- Implement log rotation to prevent disk space issues
- Secure log files with appropriate permissions
- Consider centralized logging for production deployments

## Performance Considerations

### Optimization Strategies
1. **Async Operations**: Use asyncio for all I/O operations
2. **Connection Pooling**: Reuse HTTP connections for Telegram API
3. **Caching**: Cache frequently accessed content
4. **Lazy Loading**: Load content only when needed
5. **Resource Management**: Proper cleanup of resources

### Monitoring and Metrics
- Track message processing times
- Monitor memory usage and file system space
- Log performance metrics for optimization
- Implement health checks for deployment

## Deployment Strategy

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Environment Setup
- Support for multiple environments (development, staging, production)
- Environment-specific configuration files
- Automated deployment scripts
- Health check endpoints

### Monitoring and Logging
- Structured logging with JSON format
- Log aggregation for production environments
- Error tracking and alerting
- Performance monitoring and metrics collection