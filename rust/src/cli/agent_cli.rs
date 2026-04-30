use clap::Parser;

#[derive(Parser)]
#[command(name = "agentshiro-cli")]
#[command(about = "AgentShiro Agent - Generic agent framework")]
pub struct AgentCli {
    #[arg(short, long, default_value = "claude")]
    pub provider: String,

    #[arg(short, long, required = true)]
    pub model: String,

    #[arg(short, long)]
    pub system: Option<String>,

    #[arg(long)]
    pub list_sessions: bool,

    #[arg(short, long)]
    pub session: Option<String>,

    #[arg(short, long)]
    pub verbose: bool,

    #[arg(long)]
    pub api_base: Option<String>,

    #[arg(long)]
    pub api_key: Option<String>,
}
