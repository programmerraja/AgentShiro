pub mod agent;
pub mod tools;
pub mod storage;
pub mod prompts;
pub mod config;

pub use agent::LifeAgent;
pub use storage::LifeStorage;
pub use prompts::{build_system_prompt, daily_analyzer_prompt, weekly_summary_prompt};
