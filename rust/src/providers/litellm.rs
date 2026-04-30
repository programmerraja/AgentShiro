use async_trait::async_trait;
use litellm_rs::CompletionOptions;
use futures::StreamExt;
use regex::Regex;
use serde_json::{json, Value};
use std::collections::HashMap;
use crate::models::{Message, ProviderResponse, ToolCall, ToolSchema, Usage};
use super::{Provider, ProviderStream};

pub struct LiteLLMProvider {
    model: String,
    options: CompletionOptions,
}

impl LiteLLMProvider {
    pub fn new(model: impl Into<String>) -> Self {
        LiteLLMProvider {
            model: model.into(),
            options: CompletionOptions::default(),
        }
    }

    pub fn with_api_base(mut self, url: impl Into<String>) -> Self {
        self.options.api_base = Some(url.into());
        self
    }

    pub fn with_api_key(mut self, key: impl Into<String>) -> Self {
        self.options.api_key = Some(key.into());
        self
    }

    pub fn with_max_tokens(mut self, n: u32) -> Self {
        self.options.max_tokens = Some(n);
        self
    }

    pub fn with_temperature(mut self, t: f32) -> Self {
        self.options.temperature = Some(t);
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
impl Provider for LiteLLMProvider {
    async fn call(
        &self,
        messages: &[Message],
        system_prompt: &str,
        tools: Vec<ToolSchema>,
    ) -> anyhow::Result<ProviderResponse> {
        log::debug!("Calling litellm with model: {}", self.model);

        let mut litellm_messages = vec![
            litellm_rs::system_message(system_prompt)
        ];

        for msg in messages {
            let litellm_msg = match msg.role.as_str() {
                "user" => litellm_rs::user_message(&msg.content),
                "assistant" => litellm_rs::assistant_message(&msg.content),
                "system" => litellm_rs::system_message(&msg.content),
                _ => litellm_rs::user_message(&msg.content),
            };
            litellm_messages.push(litellm_msg);
        }

        let mut opts = self.options.clone();
        opts.max_tokens = opts.max_tokens.or(Some(4096));

        let response = litellm_rs::completion(&self.model, litellm_messages, Some(opts))
            .await
            .map_err(|e| anyhow::anyhow!("litellm completion error: {}", e))?;

        let content = response
            .choices
            .first()
            .and_then(|choice| {
                choice.message.content.as_ref().map(|content| {
                    match content {
                        litellm_rs::MessageContent::Text(text) => text.clone(),
                        litellm_rs::MessageContent::Parts(parts) => {
                            parts
                                .iter()
                                .filter_map(|part| {
                                    if let litellm_rs::ContentPart::Text { text } = part {
                                        Some(text.clone())
                                    } else {
                                        None
                                    }
                                })
                                .collect::<Vec<_>>()
                                .join("")
                        }
                    }
                })
            })
            .unwrap_or_default();

        let tool_calls = if content.contains('[') && content.contains(']') {
            Self::parse_inline_tools(&content, &tools)
        } else {
            vec![]
        };

        let usage = response.usage.map(|u| Usage {
            input_tokens: u.prompt_tokens,
            output_tokens: u.completion_tokens,
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
        log::debug!("Calling litellm streaming with model: {}", self.model);

        let mut litellm_messages = vec![
            litellm_rs::system_message(system_prompt)
        ];

        for msg in messages {
            let litellm_msg = match msg.role.as_str() {
                "user" => litellm_rs::user_message(&msg.content),
                "assistant" => litellm_rs::assistant_message(&msg.content),
                "system" => litellm_rs::system_message(&msg.content),
                _ => litellm_rs::user_message(&msg.content),
            };
            litellm_messages.push(litellm_msg);
        }

        let mut opts = self.options.clone();
        opts.max_tokens = opts.max_tokens.or(Some(4096));
        opts.stream = true;

        let mut stream = litellm_rs::completion_stream(&self.model, litellm_messages, Some(opts))
            .await
            .map_err(|e| anyhow::anyhow!("litellm streaming error: {}", e))?;

        let stream = Box::pin(async_stream::stream! {
            while let Some(chunk_result) = stream.next().await {
                match chunk_result {
                    Ok(chunk) => {
                        if let Some(choice) = chunk.choices.first() {
                            if let Some(content) = &choice.delta.content {
                                yield Ok(content.clone());
                            }
                        }
                    }
                    Err(e) => {
                        yield Err(anyhow::anyhow!("stream error: {}", e));
                        break;
                    }
                }
            }
        });

        Ok(stream)
    }

    fn name(&self) -> &str {
        &self.model
    }
}
