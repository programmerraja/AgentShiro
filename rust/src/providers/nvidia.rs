use super::{Provider, ProviderStream};
use crate::models::{Message, ProviderResponse, ToolCall, ToolSchema, Usage};
use async_trait::async_trait;
use regex::Regex;
use serde_json::{json, Value};
use std::collections::HashMap;

pub struct NvidiaProvider {
    api_base: String,
    model: String,
    api_key: Option<String>,
    max_tokens: u32,
    temperature: f32,
}

impl NvidiaProvider {
    pub fn new(api_base: impl Into<String>, model: impl Into<String>) -> Self {
        NvidiaProvider {
            api_base: api_base.into(),
            model: model.into(),
            api_key: None,
            max_tokens: 4096,
            temperature: 0.7,
        }
    }

    pub fn with_api_key(mut self, key: impl Into<String>) -> Self {
        self.api_key = Some(key.into());
        self
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
impl Provider for NvidiaProvider {
    async fn call(
        &self,
        messages: &[Message],
        system_prompt: &str,
        tools: Vec<ToolSchema>,
    ) -> anyhow::Result<ProviderResponse> {
        log::debug!(
            "Calling NVIDIA provider at {} with model: {}",
            self.api_base,
            self.model
        );

        let client = reqwest::Client::new();

        // Build OpenAI-compatible request
        let mut request_messages: Vec<Value> =
            vec![json!({ "role": "system", "content": system_prompt })];

        for msg in messages {
            request_messages.push(json!({
                "role": msg.role,
                "content": msg.content
            }));
        }

        let request_body = json!({
            "model": self.model,
            "messages": request_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": false,
        });

        let url = format!(
            "{}/v1/chat/completions",
            self.api_base.trim_end_matches('/')
        );

        // print!("{} {}", url, request_body);

        let mut req = client.post(&url).json(&request_body);

        if let Some(key) = &self.api_key {
            req = req.header("Authorization", format!("Bearer {}", key));
        }

        let response = req
            .send()
            .await
            .map_err(|e| anyhow::anyhow!("NVIDIA API request failed: {}", e))?;

        let status = response.status();
        if !status.is_success() {
            let error_text = response
                .text()
                .await
                .unwrap_or_else(|_| "Unknown error".to_string());
            return Err(anyhow::anyhow!(
                "NVIDIA API error ({}): {}",
                status,
                error_text
            ));
        }

        let response_json: Value = response
            .json()
            .await
            .map_err(|e| anyhow::anyhow!("Failed to parse NVIDIA response: {}", e))?;

        // Parse response
        let content = response_json
            .get("choices")
            .and_then(|choices| choices.get(0))
            .and_then(|choice| choice.get("message"))
            .and_then(|message| message.get("content"))
            .and_then(|content| content.as_str())
            .unwrap_or("")
            .to_string();

        if content.is_empty() {
            return Err(anyhow::anyhow!("NVIDIA API returned empty content"));
        }

        let tool_calls = if content.contains('[') && content.contains(']') {
            Self::parse_inline_tools(&content, &tools)
        } else {
            vec![]
        };

        let usage = response_json.get("usage").map(|u| Usage {
            input_tokens: u.get("prompt_tokens").and_then(|v| v.as_u64()).unwrap_or(0) as u32,
            output_tokens: u
                .get("completion_tokens")
                .and_then(|v| v.as_u64())
                .unwrap_or(0) as u32,
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
        // For now, fall back to non-streaming and return in a stream wrapper
        let response = self.call(messages, system_prompt, tools).await?;
        let content = response.content;
        let stream = futures::stream::once(async move { Ok(content) });
        Ok(Box::pin(stream))
    }

    fn name(&self) -> &str {
        &self.model
    }
}
