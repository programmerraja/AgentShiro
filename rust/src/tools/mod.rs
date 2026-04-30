use async_trait::async_trait;
use serde_json::Value;
use std::collections::HashMap;
use crate::models::ToolSchema;

pub mod builtin;

#[async_trait]
pub trait Tool: Send + Sync {
    async fn execute(&self, args: Value) -> anyhow::Result<String>;
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn schema(&self) -> Value;
}

pub struct ToolRegistry {
    tools: HashMap<String, Box<dyn Tool>>,
}

impl ToolRegistry {
    pub fn new() -> Self {
        ToolRegistry {
            tools: HashMap::new(),
        }
    }

    pub fn register(&mut self, tool: Box<dyn Tool>) {
        self.tools.insert(tool.name().to_string(), tool);
    }

    pub async fn execute(&self, name: &str, args: &Value) -> anyhow::Result<String> {
        let tool = self
            .tools
            .get(name)
            .ok_or_else(|| anyhow::anyhow!("Tool not found: {}", name))?;

        tool.execute(args.clone()).await
    }

    pub fn list_schemas(&self) -> Vec<ToolSchema> {
        self.tools
            .values()
            .map(|tool| ToolSchema {
                name: tool.name().to_string(),
                description: tool.description().to_string(),
                input_schema: tool.schema(),
            })
            .collect()
    }
}

impl Default for ToolRegistry {
    fn default() -> Self {
        Self::new()
    }
}

pub use builtin::*;
