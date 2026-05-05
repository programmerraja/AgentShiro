use agentshiro::agent::AgentLoop;
use agentshiro::cli::LifeAssistantCli;
use agentshiro::life_agent::LifeAgent;
use agentshiro::providers::{OpenAIProvider, Provider};
use agentshiro::utils::{setup_logging, Config};
use clap::Parser;
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    setup_logging();

    let cli = LifeAssistantCli::parse();

    if cli.verbose {
        std::env::set_var("RUST_LOG", "debug");
    }

    let config = Config::from_env()?;
    let api_key = std::env::var("OPENAI_API_KEY")
        .unwrap_or_else(|_| "sk-default-key".to_string());
    let api_base = std::env::var("OPENAI_API_BASE_URL").ok();
    let model_id = std::env::var("MODEL_NAME")
        .unwrap_or_else(|_| "meta/llama-3.2-3b-instruct".to_string());

    log::info!(
        "Starting Life Assistant with OpenAI provider for model: {}",
        model_id
    );

    let openai_provider = if let Some(base) = api_base {
        log::info!("Using custom API base: {}", base);
        OpenAIProvider::with_api_base(&api_key, &base, &model_id)
    } else {
        OpenAIProvider::new(&api_key, &model_id)
    };

    let provider: Arc<dyn Provider> = Arc::new(openai_provider);

    match cli.command {
        agentshiro::cli::LifeCommands::Interactive { session: _ } => {
            log::info!("Starting interactive mode");

            let life_agent = LifeAgent::new(
                provider,
                Some(config.sessions_dir.to_string_lossy().to_string()),
            )
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

            let session_manager =
                agentshiro::agent::SessionManager::new(Some(config.sessions_dir))?;
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
