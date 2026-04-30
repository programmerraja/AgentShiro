use clap::Parser;
use std::sync::Arc;
use agentshiro::agent::AgentLoop;
use agentshiro::life_agent::LifeAgent;
use agentshiro::providers::{Provider, LiteLLMProvider};
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
    let provider_name = cli.provider.unwrap_or_else(|| "nvidia_nim".to_string());
    let model_id = cli.model.unwrap_or_else(|| "nvidia_nim/qwen/qwen3-next-80b-a3b-instruct".to_string());

    log::info!("Starting Life Assistant with provider: {}", provider_name);

    let model_string = format!("{}/{}", provider_name, model_id);
    let provider: Arc<dyn Provider> = Arc::new(
        LiteLLMProvider::new(model_string)
    );

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
