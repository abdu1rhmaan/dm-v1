# dm-pro - Professional CLI Download Manager

A professional CLI Download Manager built with Clean Architecture principles, supporting direct file downloads, HTML page discovery, and HLS stream handling.

## Features

- **Clean Architecture**: Proper separation of concerns with domain, application, infrastructure, and CLI layers
- **Multiple Download Types**: Support for direct files, HTML page discovery, and HLS streams
- **Queue Management**: Advanced queue system with move, pause, resume operations
- **Progress Tracking**: Real-time progress reporting with console progress bars
- **Archive System**: Automatic archiving of completed downloads
- **Cross-Platform**: Works on Windows, Linux, macOS, and Termux

## Installation

### Prerequisites
- Python 3.8 or higher

### Install from source
```bash
git clone <repository-url>
cd dm-pro
pip install .
```

### Install in development mode
```bash
pip install -e .[development]
```

## Usage

### Add a download task
```bash
dm add <url>
```

### List all tasks
```bash
dm list
```

### Start a task by queue ID
```bash
dm start <queue_id>
```

### Start all tasks
```bash
dm start-all
```

### Remove a task by queue ID
```bash
dm remove <queue_id>
```

### Pause all downloads
```bash
dm pause-all
```

### Move task position in queue
```bash
dm move <from_queue_id> <to_queue_id>
```

## Architecture

The application follows Clean Architecture principles:

- **Domain**: Core business entities and interfaces
- **Application**: Use cases and business logic
- **Infrastructure**: External services (network, database, file system)
- **CLI**: User interface layer

## Supported Download Types

- **Direct Files**: Regular HTTP files with resume support
- **HTML Pages**: Extract downloadable links from web pages
- **HLS Streams**: m3u8 playlist support with quality selection

## Development

### Running tests
```bash
pip install -e .[test]
pytest
```

### Code formatting
```bash
pip install -e .[development]
black src/
```

## License

MIT