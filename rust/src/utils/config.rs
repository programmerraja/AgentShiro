use std::path::PathBuf;

pub struct Config {
    pub anthropic_api_key: Option<String>,
    pub openai_api_key: Option<String>,
    pub ollama_base_url: String,
    pub sessions_dir: PathBuf,
    pub log_level: String,
}

impl Config {
    pub fn from_env() -> anyhow::Result<Self> {
        dotenv::dotenv().ok();

        let anthropic_api_key = std::env::var("ANTHROPIC_API_KEY").ok();
        let openai_api_key = std::env::var("OPENAI_API_KEY").ok();
        let ollama_base_url = std::env::var("OLLAMA_BASE_URL")
            .unwrap_or_else(|_| "http://localhost:11434".to_string());
        let log_level =
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());

        let sessions_dir = std::env::var("AGENTSHIRO_SESSIONS_DIR")
            .ok()
            .map(PathBuf::from)
            .unwrap_or_else(|| {
                let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
                PathBuf::from(format!("{}/.agentshiro/sessions", home))
            });

        Ok(Config {
            anthropic_api_key,
            openai_api_key,
            ollama_base_url,
            sessions_dir,
            log_level,
        })
    }
}
