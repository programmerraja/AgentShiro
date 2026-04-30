use std::path::PathBuf;
use chrono::Local;

pub struct LifeStorage {
    base_dir: PathBuf,
}

impl LifeStorage {
    pub fn new(base_dir: Option<String>) -> anyhow::Result<Self> {
        let base_dir = base_dir.unwrap_or_else(|| "./life-system".to_string());
        std::fs::create_dir_all(&base_dir)?;

        log::info!("LifeStorage initialized at: {}", base_dir);

        Ok(LifeStorage {
            base_dir: PathBuf::from(base_dir),
        })
    }

    pub fn generate_daily_template(&self, date: &str) -> anyhow::Result<String> {
        let path = self.base_dir.join("daily").join(date).with_extension("md");
        std::fs::create_dir_all(path.parent().unwrap())?;

        let template = format!(
            "# Daily Log - {}\n\n## Tasks\n\n## Reflection\n\n## Mistakes\n",
            date
        );

        std::fs::write(&path, template)?;

        log::debug!("Generated daily template for {}", date);

        Ok(path.to_string_lossy().to_string())
    }

    pub fn read_goals(&self) -> anyhow::Result<String> {
        let path = self.base_dir.join("goals").join("6monthgoal.md");
        std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("Failed to read goals: {}", e))
    }

    pub fn read_daily(&self, date: &str) -> anyhow::Result<String> {
        let path = self.base_dir.join("daily").join(date).with_extension("md");
        std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("Failed to read daily log for {}: {}", date, e))
    }

    pub fn read_today(&self) -> anyhow::Result<String> {
        let today = Local::now().format("%Y-%m-%d").to_string();
        self.read_daily(&today)
    }

    pub fn get_base_dir(&self) -> &PathBuf {
        &self.base_dir
    }
}
