use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "life-assistant-cli")]
#[command(about = "Life Assistant Agent - Daily planning and reflection")]
pub struct LifeAssistantCli {
    #[command(subcommand)]
    pub command: LifeCommands,

    #[arg(short, long, global = true)]
    pub model: Option<String>,

    #[arg(short, long, global = true)]
    pub provider: Option<String>,

    #[arg(short, long, global = true)]
    pub session: Option<String>,

    #[arg(short, long, global = true)]
    pub verbose: bool,
}

#[derive(Subcommand)]
pub enum LifeCommands {
    /// Start interactive mode
    Interactive {
        #[arg(short, long)]
        session: Option<String>,
    },
    /// Analyze today
    Analyze,
    /// Weekly summary
    Summary,
    /// List sessions
    ListSessions,
}
