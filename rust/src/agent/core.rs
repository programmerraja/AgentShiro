use std::sync::Arc;
use tokio::sync::Mutex;
use futures::StreamExt;
use crate::models::{Message, ToolCall};
use crate::providers::{Provider, ProviderStream};
use crate::tools::ToolRegistry;

pub struct Agent {
    provider: Arc<dyn Provider>,
    tools: Arc<Mutex<ToolRegistry>>,
    system_prompt: String,
    history: Arc<Mutex<Vec<Message>>>,
    max_iterations: usize,
}

impl Agent {
    pub async fn new(
        provider: Arc<dyn Provider>,
        tools: ToolRegistry,
        system_prompt: String,
    ) -> anyhow::Result<Self> {
        Ok(Agent {
            provider,
            tools: Arc::new(Mutex::new(tools)),
            system_prompt,
            history: Arc::new(Mutex::new(Vec::new())),
            max_iterations: 10,
        })
    }

    pub async fn call(&self, user_message: &str) -> anyhow::Result<String> {
        let mut hist = self.history.lock().await;
        hist.push(Message::user(user_message));

        let tools = self.tools.lock().await;
        let tool_schemas = tools.list_schemas();
        drop(tools);

        let response = self
            .provider
            .call(&hist, &self.system_prompt, tool_schemas)
            .await?;

        let final_response = if !response.tool_calls.is_empty() {
            self.process_tool_calls(&response.tool_calls).await?
        } else {
            response.content
        };

        hist.push(Message::assistant(&final_response));

        Ok(final_response)
    }

    async fn process_tool_calls(&self, tool_calls: &[ToolCall]) -> anyhow::Result<String> {
        let mut results = Vec::new();
        let tools = self.tools.lock().await;

        for call in tool_calls {
            match tools.execute(&call.name, &call.arguments).await {
                Ok(result) => results.push(format!("{}:\n{}", call.name, result)),
                Err(e) => results.push(format!("{}: ERROR - {}", call.name, e)),
            }
        }

        Ok(results.join("\n\n"))
    }

    pub async fn call_stream(&self, user_message: &str) -> anyhow::Result<ProviderStream> {
        let mut hist = self.history.lock().await;
        hist.push(Message::user(user_message));

        let tools = self.tools.lock().await;
        let tool_schemas = tools.list_schemas();
        drop(tools);

        let stream = self
            .provider
            .call_stream(&hist, &self.system_prompt, tool_schemas)
            .await?;

        Ok(stream)
    }

    pub async fn get_history(&self) -> Vec<Message> {
        self.history.lock().await.clone()
    }

    pub async fn reset(&self) {
        self.history.lock().await.clear();
    }

    pub fn set_max_iterations(&mut self, max: usize) {
        self.max_iterations = max;
    }
}
