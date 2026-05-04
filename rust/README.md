# AgentShiro - Rust Implementation

A production-ready, standalone Rust implementation of the AgentShiro agent framework and Life Assistant agent.

## Features

- **Async/Await Architecture**: Built on Tokio for high-performance concurrent operations
- **Multiple LLM Providers**: Support for Claude, OpenAI, and Ollama
- **Modular Tool System**: Easy to add and compose tools
- **Session Management**: Persist and resume conversations
- **Cross-Platform**: Single binary works on Linux, macOS, and Windows
- **Zero External Dependencies at Runtime**: All dependencies included in the binary

## Installation

### Prerequisites

- **Rust 1.70+** ([Install Rust](https://rustup.rs/))

### Build from Source

```bash
cd rust
cargo build --release
```

This creates optimized binaries in `target/release/`.

### Install System-Wide

```bash
sudo cp target/release/life-assistant-cli /usr/local/bin/
sudo cp target/release/agentshiro-cli /usr/local/bin/
```

Then use directly:
```bash
life-assistant-cli interactive
agentshiro-cli --provider claude --model claude-3-5-sonnet-20241022
```

## Configuration

All configuration is via environment variables (12-factor app):

```bash
# Provider credentials
export ANTHROPIC_API_KEY=sk-ant-...         # For Claude
export OPENAI_API_KEY=sk-...                # For OpenAI
export OLLAMA_BASE_URL=http://localhost:11434  # For Ollama (optional, default shown)

# Logging
export RUST_LOG=info                        # debug, info, warn, error

# Paths
export AGENTSHIRO_SESSIONS_DIR=~/.agentshiro/sessions
export LIFE_SYSTEM_DIR=./life-system

# Life Agent specific
export LIFE_AGENT_PROVIDER=claude
export LIFE_AGENT_MODEL=claude-3-5-sonnet-20241022
```

## Usage

### Life Assistant CLI

Interactive mode:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
./target/release/life-assistant-cli interactive
```

Analyze today:
```bash
./target/release/life-assistant-cli analyze
```

Weekly summary:
```bash
./target/release/life-assistant-cli summary
```

List sessions:
```bash
./target/release/life-assistant-cli list-sessions
```

### General Agent CLI

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./target/release/agentshiro-cli --provider claude --model claude-3-5-sonnet-20241022
```

With custom system prompt:
```bash
./target/release/agentshiro-cli \
  --provider claude \
  --model claude-3-5-sonnet-20241022 \
  --system "You are a helpful coding assistant"
```

List sessions:
```bash
./target/release/agentshiro-cli --list-sessions
```

## Project Structure

```
rust/
├── Cargo.toml                   # Dependencies and build config
├── src/
│   ├── main.rs                  # CLI entry point
│   ├── lib.rs                   # Library root
│   ├── agent/                   # Core agent framework
│   │   ├── core.rs              # Agent struct
│   │   ├── loop.rs              # Interactive loop
│   │   └── session.rs           # Session persistence
│   ├── providers/               # LLM provider implementations
│   │   ├── claude.rs
│   │   ├── openai.rs
│   │   └── ollama.rs
│   ├── tools/                   # Tool system
│   │   ├── mod.rs               # Registry
│   │   └── builtin/
│   │       └── file_ops.rs      # File read/write/insert
│   ├── life_agent/              # Life assistant implementation
│   │   ├── agent.rs
│   │   ├── tools.rs
│   │   ├── storage.rs
│   │   └── prompts.rs
│   ├── models/                  # Data structures
│   ├── utils/                   # Config, logging
│   ├── cli/                     # CLI argument parsing
│   └── bin/                     # Binary entry points
├── tests/                       # Integration tests
└── examples/                    # Example usage
```

## Development

### Run in Debug Mode

```bash
RUST_LOG=debug cargo run --bin life-assistant-cli -- interactive
```

### Run Tests

```bash
cargo test
cargo test -- --nocapture   # Show output
```

### Format Code

```bash
cargo fmt
```

### Check for Issues

```bash
cargo clippy
```

## Architecture

### Agent Core

The `Agent` struct is the heart of the system:
- Maintains conversation history
- Calls the provider with context
- Executes tools when requested by the provider
- Manages tool registry

### Providers

Each provider implements the `Provider` trait:
- `ClaudeProvider`: Anthropic's Claude API
- `OpenAIProvider`: OpenAI's ChatGPT API
- `OllamaProvider`: Local Ollama models

### Tools

Tools implement the `Tool` trait and are registered in a `ToolRegistry`. Built-in tools:
- `read_file`: Read file contents
- `write_file`: Write to file
- `insert_file`: Append to file

### Life Agent

Builds on top of the Agent framework with:
- Life-specific prompts
- Daily log management
- Goal tracking
- Reflection capabilities

## Performance

Rust binary characteristics:
- **Size**: ~15-20MB (release build with LTO)
- **Startup**: <100ms
- **Memory**: Minimal, no garbage collection
- **Concurrency**: Native async/await support

### Build Optimizations

The release build uses:
- Link-time optimization (`lto = true`)
- Single codegen unit for better optimization
- Binary stripping (`strip = true`)

## Examples

### Simple Agent Interaction

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./target/release/agentshiro-cli --provider claude --model claude-3-5-sonnet-20241022
```

Then type messages:
```
You> What is the capital of France?
Agent> The capital of France is Paris...
```

### Life Assistant Workflow

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Start interactive session
./target/release/life-assistant-cli interactive

# In the conversation, the agent can:
# - Read daily logs
# - Write new goals
# - Append reflections
# - Provide analysis
```

## Troubleshooting

### "Provider API key not set"

Make sure to export the appropriate API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

### Ollama connection refused

Make sure Ollama is running:
```bash
ollama serve
```

In another terminal:
```bash
ollama pull mistral  # or another model
```

### Debug logging

Enable debug logging:
```bash
RUST_LOG=debug ./target/release/life-assistant-cli interactive
```

Module-specific logging:
```bash
RUST_LOG=agentshiro::providers=debug ./target/release/life-assistant-cli interactive
```

## Feature Flags

Build with specific providers only:

```bash
# Only Claude
cargo build --release --no-default-features --features "claude"

# Only OpenAI
cargo build --release --no-default-features --features "openai"

# Only Ollama
cargo build --release --no-default-features --features "ollama"

# Claude + OpenAI
cargo build --release --no-default-features --features "claude,openai"
```

## Cross-Platform Compilation

Compile for different targets:

```bash
# Linux x86_64
cargo build --release --target x86_64-unknown-linux-gnu

# macOS (Intel)
cargo build --release --target x86_64-apple-darwin

# macOS (Apple Silicon)
cargo build --release --target aarch64-apple-darwin

# Windows
cargo build --release --target x86_64-pc-windows-gnu

# Linux ARM (Raspberry Pi)
cargo build --release --target aarch64-unknown-linux-gnu
```

## Integration with Python Version

The Rust and Python implementations are independent:
- No shared state
- No inter-process communication
- Separate session management
- Different configuration

To use both in parallel:
- Python version: `python life-assistant.py`
- Rust version: `./rust/target/release/life-assistant-cli interactive`

## Next Steps

1. **Install Rust**: https://rustup.rs/
2. **Build the project**: `cargo build --release`
3. **Set up credentials**: `export ANTHROPIC_API_KEY=sk-ant-...`
4. **Run**: `./target/release/life-assistant-cli interactive`

## Contributing

To add a new tool:

1. Create `src/tools/builtin/my_tool.rs`
2. Implement the `Tool` trait
3. Register in tool registry
4. Update module exports

To add a new provider:

1. Create `src/providers/my_provider.rs`
2. Implement the `Provider` trait
3. Handle API responses
4. Add feature flag if optional

## License

Same as main AgentShiro project

## Support

For issues or questions:
- Check the logs: `RUST_LOG=debug`
- Review the architecture diagram in the main documentation
- Compare with Python version behavior


cargo run --bin life-assistant-cli interactive

cargo build --release --target x86_64-unknown-linux-gnu --bin life-assistant-cli