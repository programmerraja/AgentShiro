use clap::Parser;
use std::sync::Arc;
use agentshiro::agent::{Agent, AgentLoop, SessionManager};
use agentshiro::providers::OpenAIProvider;
use agentshiro::tools::ToolRegistry;
use agentshiro::tools::builtin::{ReadFileTool, WriteFileTool, InsertFileTool};
use agentshiro::utils::setup_logging;
use agentshiro::cli::AgentCli;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    setup_logging();

    let cli = AgentCli::parse();

    if cli.verbose {
        std::env::set_var("RUST_LOG", "debug");
    }

    log::info!("Starting AgentShiro CLI with model: {}", cli.model);

    let api_key = cli.api_key
        .or_else(|| std::env::var("OPENAI_API_KEY").ok())
        .unwrap_or_else(|| "sk-default-key".to_string());

    let provider = if let Some(api_base) = cli.api_base {
        OpenAIProvider::with_api_base(&api_key, &api_base, &cli.model)
    } else {
        OpenAIProvider::new(&api_key, &cli.model)
    };

    let provider: Arc<dyn agentshiro::providers::Provider> = Arc::new(provider);

    if cli.list_sessions {
        let session_manager = SessionManager::new(None)?;
        let sessions = session_manager.list_sessions()?;

        if sessions.is_empty() {
            println!("No sessions found");
        } else {
            println!("Available sessions:");
            for session in sessions {
                println!("  - {}", session);
            }
        }
        return Ok(());
    }

    let mut tools = ToolRegistry::new();
    tools.register(Box::new(ReadFileTool));
    tools.register(Box::new(WriteFileTool));
    tools.register(Box::new(InsertFileTool));

    let system_prompt = cli
        .system
        .unwrap_or_else(|| "You are a helpful assistant. Use the available tools as needed.".to_string());

    let agent = Agent::new(provider, tools, system_prompt).await?;

    let agent_loop = AgentLoop::new(agent).with_max_iterations(100);
    agent_loop.run().await?;

    Ok(())
}
