use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use uuid::Uuid;
use chrono::Utc;
use crate::models::Message;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub created_at: String,
    pub last_updated: String,
    pub messages: Vec<Message>,
}

pub struct SessionManager {
    base_dir: PathBuf,
}

impl SessionManager {
    pub fn new(base_dir: Option<PathBuf>) -> anyhow::Result<Self> {
        let base_dir = base_dir.unwrap_or_else(|| {
            let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
            PathBuf::from(format!("{}/.agentshiro/sessions", home))
        });

        std::fs::create_dir_all(&base_dir)?;

        Ok(SessionManager { base_dir })
    }

    pub fn create_session(&self) -> anyhow::Result<String> {
        let session_id = Uuid::new_v4().to_string();
        let session = Session {
            id: session_id.clone(),
            created_at: Utc::now().to_rfc3339(),
            last_updated: Utc::now().to_rfc3339(),
            messages: vec![],
        };

        let path = self.base_dir.join(&session_id);
        let json = serde_json::to_string_pretty(&session)?;
        std::fs::write(path, json)?;

        log::info!("Created session: {}", session_id);
        Ok(session_id)
    }

    pub fn load_session(&self, session_id: &str) -> anyhow::Result<Session> {
        let path = self.base_dir.join(session_id);
        let json = std::fs::read_to_string(&path)
            .map_err(|e| anyhow::anyhow!("Failed to load session {}: {}", session_id, e))?;
        let session: Session = serde_json::from_str(&json)?;
        log::info!("Loaded session: {}", session_id);
        Ok(session)
    }

    pub fn save_session(&self, session: &Session) -> anyhow::Result<()> {
        let path = self.base_dir.join(&session.id);
        let json = serde_json::to_string_pretty(session)?;
        std::fs::write(path, json)?;
        log::debug!("Saved session: {}", session.id);
        Ok(())
    }

    pub fn list_sessions(&self) -> anyhow::Result<Vec<String>> {
        let mut sessions = Vec::new();
        for entry in std::fs::read_dir(&self.base_dir)? {
            if let Ok(entry) = entry {
                if let Some(name) = entry.file_name().to_str() {
                    if !name.starts_with('.') {
                        sessions.push(name.to_string());
                    }
                }
            }
        }
        Ok(sessions)
    }
}
