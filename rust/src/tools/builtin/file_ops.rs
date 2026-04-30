use async_trait::async_trait;
use serde_json::{json, Value};
use crate::tools::Tool;

pub struct ReadFileTool;

#[async_trait]
impl Tool for ReadFileTool {
    async fn execute(&self, args: Value) -> anyhow::Result<String> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("path required"))?;

        let content = std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("Failed to read {}: {}", path, e))?;

        Ok(content)
    }

    fn name(&self) -> &str {
        "read_file"
    }

    fn description(&self) -> &str {
        "Read contents of a file"
    }

    fn schema(&self) -> Value {
        json!({
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to file"
                }
            },
            "required": ["path"]
        })
    }
}

pub struct WriteFileTool;

#[async_trait]
impl Tool for WriteFileTool {
    async fn execute(&self, args: Value) -> anyhow::Result<String> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("path required"))?;
        let content = args["content"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("content required"))?;

        std::fs::write(path, content)?;
        Ok(format!("Written to {}", path))
    }

    fn name(&self) -> &str {
        "write_file"
    }

    fn description(&self) -> &str {
        "Write content to a file"
    }

    fn schema(&self) -> Value {
        json!({
            "type": "object",
            "properties": {
                "path": { "type": "string" },
                "content": { "type": "string" }
            },
            "required": ["path", "content"]
        })
    }
}

pub struct InsertFileTool;

#[async_trait]
impl Tool for InsertFileTool {
    async fn execute(&self, args: Value) -> anyhow::Result<String> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("path required"))?;
        let content = args["content"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("content required"))?;

        let mut file_content = std::fs::read_to_string(path)?;
        file_content.push('\n');
        file_content.push_str(content);

        std::fs::write(path, file_content)?;
        Ok(format!("Appended to {}", path))
    }

    fn name(&self) -> &str {
        "insert_file"
    }

    fn description(&self) -> &str {
        "Append content to a file"
    }

    fn schema(&self) -> Value {
        json!({
            "type": "object",
            "properties": {
                "path": { "type": "string" },
                "content": { "type": "string" }
            },
            "required": ["path", "content"]
        })
    }
}
