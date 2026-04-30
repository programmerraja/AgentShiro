# Rust Implementation - Quick Start

## 1. Install Rust (if not already installed)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

Verify installation:
```bash
rustc --version
cargo --version
```

## 2. Build the Project

```bash
cd /home/boopathik/Documents/Personal\ Code/AgentShiro/rust
cargo build --release
```

This will take a few minutes on first build. The compiled binaries will be in `target/release/`.

## 3. Set Up Environment Variables

Create a `.env` file or export variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export RUST_LOG=info
```

Or for OpenAI:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or for Ollama (local):
```bash
export OLLAMA_BASE_URL=http://localhost:11434
```

## 4. Run Life Assistant

**Interactive mode:**
```bash
./target/release/life-assistant-cli interactive
```

Then type your messages:
```
You> Hello, help me plan my day
Agent> I'd be happy to help you plan your day...
```

Type `exit` or `quit` to stop.

**Analyze today:**
```bash
./target/release/life-assistant-cli analyze
```

**Weekly summary:**
```bash
./target/release/life-assistant-cli summary
```

**List sessions:**
```bash
./target/release/life-assistant-cli list-sessions
```

## 5. Run General Agent

```bash
./target/release/agentshiro-cli --provider claude --model claude-3-5-sonnet-20241022
```

With custom system prompt:
```bash
./target/release/agentshiro-cli \
  --provider claude \
  --model claude-3-5-sonnet-20241022 \
  --system "You are a helpful programming assistant"
```

## 6. Optional: Install System-Wide

```bash
sudo cp target/release/life-assistant-cli /usr/local/bin/
sudo cp target/release/agentshiro-cli /usr/local/bin/
```

Then use directly from anywhere:
```bash
life-assistant-cli interactive
agentshiro-cli --provider claude --model claude-3-5-sonnet-20241022
```

## Common Issues

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Ollama connection refused
Make sure Ollama is running in another terminal:
```bash
ollama serve
```

Then in another terminal:
```bash
ollama pull mistral
```

### Debug logging
```bash
RUST_LOG=debug ./target/release/life-assistant-cli interactive
```

## Project Structure

```
rust/
├── Cargo.toml          # Dependencies
├── README.md           # Full documentation
├── src/
│   ├── agent/          # Core agent framework
│   ├── providers/      # Claude, OpenAI, Ollama
│   ├── tools/          # Tool system
│   ├── life_agent/     # Life assistant
│   └── bin/            # CLI binaries
└── target/release/     # Compiled binaries
    ├── life-assistant-cli
    └── agentshiro-cli
```

## Next: Explore the Implementation

1. **Core Agent** (`src/agent/core.rs`) - How inference works
2. **Providers** (`src/providers/`) - API integrations
3. **Tools** (`src/tools/`) - Tool system
4. **Life Agent** (`src/life_agent/`) - Life-specific logic
5. **CLI** (`src/bin/`) - Entry points

## Performance

- **Binary size**: ~20MB (release)
- **Startup**: <10ms
- **Memory**: Minimal
- **Async**: Native support

## Features

✅ Multiple LLM providers (Claude, OpenAI, Ollama)
✅ Interactive multi-turn conversations
✅ Tool execution (read/write files)
✅ Session persistence
✅ Life assistant with daily logs
✅ Environment-based configuration
✅ Cross-platform binary (Linux, macOS, Windows)
✅ Async/await architecture
✅ Type-safe error handling

## For More Information

- See `README.md` for full documentation
- See `RUST_IMPLEMENTATION_PLAN.md` for architecture details
- See `RUST_IMPLEMENTATION_SUMMARY.md` for complete file listing
