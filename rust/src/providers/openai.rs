use super::{Provider, ProviderStream};
use crate::models::{Message, ProviderResponse, ToolCall, ToolSchema, Usage};
use async_trait::async_trait;
use async_openai::{
    config::OpenAIConfig,
    types::{ChatCompletionRequestMessage, CreateChatCompletionRequestArgs, Role},
    Client,
};
use regex::Regex;
use serde_json::{json, Value};
use std::collections::HashMap;

pub struct OpenAIProvider {
    client: Client<OpenAIConfig>,
    model: String,
    max_tokens: u32,
    temperature: f32,
}

impl OpenAIProvider {
    pub fn new(api_key: impl Into<String>, model: impl Into<String>) -> Self {
        let config = OpenAIConfig::default().with_api_key(api_key);
        OpenAIProvider {
            client: Client::with_config(config),
            model: model.into(),
            max_tokens: 4096,
            temperature: 0.7,
        }
    }

    pub fn with_api_base(
        api_key: impl Into<String>,
        api_base: impl Into<String>,
        model: impl Into<String>,
    ) -> Self {
        let config = OpenAIConfig::default()
            .with_api_key(api_key)
            .with_api_base(api_base);
        OpenAIProvider {
            client: Client::with_config(config),
            model: model.into(),
            max_tokens: 4096,
            temperature: 0.7,
        }
    }

    pub fn with_max_tokens(mut self, n: u32) -> Self {
        self.max_tokens = n;
        self
    }

    pub fn with_temperature(mut self, t: f32) -> Self {
        self.temperature = t;
        self
    }

    fn parse_inline_tools(content: &str, available_tools: &[ToolSchema]) -> Vec<ToolCall> {
        let pattern = Regex::new(r"\[([a-zA-Z0-9_\-]+)\((.*?)\)\]").unwrap();
        let valid_tool_names: Vec<&str> = available_tools.iter().map(|t| t.name.as_str()).collect();

        let mut tool_calls = Vec::new();

        for caps in pattern.captures_iter(content) {
            let tool_name = caps.get(1).map(|m| m.as_str()).unwrap_or("");
            let args_str = caps.get(2).map(|m| m.as_str()).unwrap_or("");

            if !valid_tool_names.contains(&tool_name) {
                continue;
            }

            let mut args_dict: HashMap<String, Value> = HashMap::new();

            if !args_str.is_empty() {
                let parts: Vec<&str> = args_str.split(',').collect();
                for part in parts {
                    if let Some((key, val)) = part.split_once('=') {
                        let key = key.trim();
                        let val = val.trim().trim_matches('"').trim_matches('\'');
                        args_dict.insert(key.to_string(), Value::String(val.to_string()));
                    }
                }
            }

            tool_calls.push(ToolCall {
                name: tool_name.to_string(),
                arguments: json!(args_dict),
            });
        }

        tool_calls
    }
}

#[async_trait]
impl Provider for OpenAIProvider {
    async fn call(
        &self,
        messages: &[Message],
        system_prompt: &str,
        tools: Vec<ToolSchema>,
    ) -> anyhow::Result<ProviderResponse> {
        log::debug!("Calling OpenAI provider with model: {}", self.model);

        let mut request_messages: Vec<ChatCompletionRequestMessage> = vec![
            ChatCompletionRequestMessage {
                role: Role::System,
                content: Some(system_prompt.to_string()),
                name: None,
                function_call: None,
            },
        ];

        for msg in messages {
            let role = match msg.role.as_str() {
                "assistant" => Role::Assistant,
                "user" => Role::User,
                _ => Role::User,
            };

            request_messages.push(ChatCompletionRequestMessage {
                role,
                content: Some(msg.content.clone()),
                name: None,
                function_call: None,
            });
        }

        let request = CreateChatCompletionRequestArgs::default()
            .model(&self.model)
            .messages(request_messages)
            .max_tokens(self.max_tokens as u16)
            .temperature(self.temperature)
            .build()?;

        log::debug!("Sending request: {:?}", request);

        let response = self.client.chat().create(request).await
            .map_err(|e| {
                log::error!("OpenAI API error: {:?}", e);
                anyhow::anyhow!("OpenAI API error: {}", e)
            })?;

        let content = response
            .choices
            .first()
            .and_then(|choice| choice.message.content.clone())
            .unwrap_or_default();

        if content.is_empty() {
            return Err(anyhow::anyhow!("OpenAI API returned empty content"));
        }

        let tool_calls = if content.contains('[') && content.contains(']') {
            Self::parse_inline_tools(&content, &tools)
        } else {
            vec![]
        };

        let usage = response.usage.map(|u| Usage {
            input_tokens: u.prompt_tokens as u32,
            output_tokens: u.completion_tokens as u32,
        });

        Ok(ProviderResponse {
            content,
            tool_calls,
            usage,
        })
    }

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

    fn name(&self) -> &str {
        &self.model
    }
}
