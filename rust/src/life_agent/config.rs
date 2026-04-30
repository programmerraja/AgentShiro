use std::path::PathBuf;

pub struct LifeAgentConfig {
    pub storage_dir: PathBuf,
    pub provider: String,
    pub model: String,
}

impl LifeAgentConfig {
    pub fn from_env() -> anyhow::Result<Self> {
        let storage_dir = std::env::var("LIFE_SYSTEM_DIR")
            .ok()
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("./life-system"));

        let provider = std::env::var("LIFE_AGENT_PROVIDER")
            .unwrap_or_else(|_| "claude".to_string());

        let model = std::env::var("LIFE_AGENT_MODEL")
            .unwrap_or_else(|_| "claude-3-5-sonnet-20241022".to_string());

        Ok(LifeAgentConfig {
            storage_dir,
            provider,
            model,
        })
    }
}
