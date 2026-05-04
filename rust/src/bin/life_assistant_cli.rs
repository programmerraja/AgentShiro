use clap::Parser;
use std::sync::Arc;
use agentshiro::agent::AgentLoop;
use agentshiro::life_agent::LifeAgent;
use agentshiro::providers::{Provider, NvidiaProvider};
use agentshiro::utils::{setup_logging, Config};
use agentshiro::cli::LifeAssistantCli;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    setup_logging();

    let cli = LifeAssistantCli::parse();

    if cli.verbose {
        std::env::set_var("RUST_LOG", "debug");
    }

    let config = Config::from_env()?;
    let api_base = std::env::var("OPENAI_API_BASE_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string());
    let model_id = cli.model.unwrap_or_else(|| "meta/llama-3.1-8b-instruct".to_string());
    let api_key = std::env::var("OPENAI_API_KEY").ok();

    log::info!("Starting Life Assistant with NVIDIA NIM provider at {}", api_base);

    let mut nvidia_provider = NvidiaProvider::new(&api_base, &model_id);
    if let Some(key) = api_key {
        nvidia_provider = nvidia_provider.with_api_key(key);
    }

    let provider: Arc<dyn Provider> = Arc::new(nvidia_provider);

    match cli.command {
        agentshiro::cli::LifeCommands::Interactive { session: _ } => {
            log::info!("Starting interactive mode");

            let life_agent =
                LifeAgent::new(provider, Some(config.sessions_dir.to_string_lossy().to_string()))
                    .await?;

            let agent_loop = AgentLoop::new(life_agent.inner).with_max_iterations(100);
            agent_loop.run().await?;
        }
        agentshiro::cli::LifeCommands::Analyze => {
            log::info!("Analyzing daily progress");

            let life_agent = LifeAgent::new(provider, None).await?;
            let storage = life_agent.get_storage();

            match storage.read_today() {
                Ok(daily_content) => {
                    let analysis_prompt = format!(
                        "Analyze today's progress:\n\n{}\n\n{}",
                        daily_content,
                        agentshiro::life_agent::daily_analyzer_prompt()
                    );

                    match life_agent.call(&analysis_prompt).await {
                        Ok(response) => println!("{}", response),
                        Err(e) => log::error!("Error: {}", e),
                    }
                }
                Err(e) => log::warn!("No daily log found: {}", e),
            }
        }
        agentshiro::cli::LifeCommands::Summary => {
            log::info!("Generating weekly summary");

            let life_agent = LifeAgent::new(provider, None).await?;

            let summary_prompt = agentshiro::life_agent::weekly_summary_prompt();

            match life_agent.call(&summary_prompt).await {
                Ok(response) => println!("{}", response),
                Err(e) => log::error!("Error: {}", e),
            }
        }
        agentshiro::cli::LifeCommands::ListSessions => {
            log::info!("Listing sessions");

            let session_manager = agentshiro::agent::SessionManager::new(Some(config.sessions_dir))?;
            let sessions = session_manager.list_sessions()?;

            if sessions.is_empty() {
                println!("No sessions found");
            } else {
                println!("Available sessions:");
                for session in sessions {
                    println!("  - {}", session);
                }
            }
        }
    }

    Ok(())
}
