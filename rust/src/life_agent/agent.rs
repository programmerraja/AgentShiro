use std::sync::Arc;
use crate::agent::Agent;
use crate::providers::Provider;
use crate::tools::ToolRegistry;
use crate::life_agent::prompts::build_system_prompt;
use crate::life_agent::tools::*;
use crate::life_agent::storage::LifeStorage;

pub struct LifeAgent {
    pub inner: Agent,
    pub storage: LifeStorage,
}

impl LifeAgent {
    pub async fn new(
        provider: Arc<dyn Provider>,
        storage_dir: Option<String>,
    ) -> anyhow::Result<Self> {
        let mut tools = ToolRegistry::new();

        tools.register(Box::new(LifeReadFileTool));
        tools.register(Box::new(LifeWriteFileTool));
        tools.register(Box::new(LifeInsertFileTool));

        let system_prompt = build_system_prompt();

        let agent = Agent::new(provider, tools, system_prompt).await?;
        let storage = LifeStorage::new(storage_dir)?;

        log::info!("LifeAgent initialized");

        Ok(LifeAgent {
            inner: agent,
            storage,
        })
    }

    pub async fn call(&self, message: &str) -> anyhow::Result<String> {
        self.inner.call(message).await
    }

    pub fn get_storage(&self) -> &LifeStorage {
        &self.storage
    }

    pub async fn get_history(&self) -> Vec<crate::models::Message> {
        self.inner.get_history().await
    }

    pub async fn reset(&self) {
        self.inner.reset().await
    }
}
