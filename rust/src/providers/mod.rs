use async_trait::async_trait;
use std::pin::Pin;
use futures::Stream;
use crate::models::{Message, ProviderResponse, ToolSchema};

pub mod litellm;
pub mod shiro_custom;

pub type ProviderStream = Pin<Box<dyn Stream<Item = anyhow::Result<String>> + Send>>;

#[async_trait]
pub trait Provider: Send + Sync {
    async fn call(
        &self,
        messages: &[Message],
        system_prompt: &str,
        tools: Vec<ToolSchema>,
    ) -> anyhow::Result<ProviderResponse>;

    async fn call_stream(
        &self,
        messages: &[Message],
        system_prompt: &str,
        tools: Vec<ToolSchema>,
    ) -> anyhow::Result<ProviderStream> {
        let response = self.call(messages, system_prompt, tools).await?;
        let content = response.content;
        let stream = futures::stream::once(async move { Ok(content) });
        Ok(Box::pin(stream))
    }

    fn name(&self) -> &str;
}

pub use litellm::LiteLLMProvider;
pub use shiro_custom::ShiroCustomProvider;
