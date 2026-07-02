# Rich Dashboard: Professional CLI Monitoring Tool

A comprehensive guide and implementation of professional-grade CLI dashboards using the **Rich** library in Python. This project demonstrates three progressive levels of complexity: from basic progress bars to multi-panel layouts to production-ready monitoring systems.

## Quick Start

```bash
git clone https://github.com/jasonnorman67889-code/rich-dashboard.git
cd rich-dashboard
pip install -e .

# V1: Basic progress bars
python -m v1_basic.dashboard

# V2: Multi-panel layout
python -m v2_multipanel.dashboard

# V3: Production-ready monitoring
python -m v3_production.dashboard
```

## Project Structure

- **v1_basic/**: Basic progress bars
- **v2_multipanel/**: Multi-panel layouts with logs and statistics  
- **v3_production/**: Production-ready with error handling, retries, and persistence
- **tests/**: Comprehensive test suite
- **examples/**: Real-world usage examples
- **docs/**: Extended documentation

## Key Features

- Native Rich progress bars with automatic refresh
- Dynamic terminal layouts (tasks, logs, metrics)
- Real-time status updates without full screen redraws
- Professional color schemes with emoji indicators
- Error handling and automatic retry logic
- Persistent file logging for audit trails
- Thread-safe operations
- Extensible plugin architecture

## Installation

```bash
pip install -e .
```

## Running Tests

```bash
pytest              # All tests
pytest --cov        # With coverage
pytest -v           # Verbose
```

## Documentation

See the [docs/](docs/) directory for:
- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

MIT License - see [LICENSE](LICENSE) for details
