use std::io::{self, BufRead, Write};
use futures::StreamExt;
use crate::agent::core::Agent;

pub struct AgentLoop {
    agent: Agent,
    max_iterations: usize,
}

impl AgentLoop {
    pub fn new(agent: Agent) -> Self {
        AgentLoop {
            agent,
            max_iterations: 10,
        }
    }

    pub fn with_max_iterations(mut self, max: usize) -> Self {
        self.max_iterations = max;
        self
    }

    pub async fn run(&self) -> anyhow::Result<()> {
        let stdin = io::stdin();
        let reader = stdin.lock();
        let mut lines = reader.lines();

        for iteration in 0..self.max_iterations {
            print!("You> ");
            io::stdout().flush()?;

            if let Some(Ok(user_input)) = lines.next() {
                if user_input.to_lowercase() == "exit" || user_input.to_lowercase() == "quit" {
                    log::info!("Exiting agent loop");
                    break;
                }

                match self.agent.call(&user_input).await {
                    Ok(response) => {
                        println!("\nAgent> {}\n", response);
                        log::debug!("Agent iteration {} completed", iteration + 1);
                    }
                    Err(e) => {
                        eprintln!("Error: {}", e);
                        log::error!("Agent error at iteration {}: {}", iteration + 1, e);
                    }
                }
            } else {
                break;
            }
        }

        Ok(())
    }

    pub async fn run_single(&self, input: &str) -> anyhow::Result<String> {
        self.agent.call(input).await
    }

    pub async fn run_streaming(&self) -> anyhow::Result<()> {
        let stdin = io::stdin();
        let reader = stdin.lock();
        let mut lines = reader.lines();

        for iteration in 0..self.max_iterations {
            print!("You> ");
            io::stdout().flush()?;

            if let Some(Ok(user_input)) = lines.next() {
                if user_input.to_lowercase() == "exit" || user_input.to_lowercase() == "quit" {
                    log::info!("Exiting agent loop");
                    break;
                }

                match self.agent.call_stream(&user_input).await {
                    Ok(mut stream) => {
                        println!("\nAgent> ", );
                        while let Some(chunk_result) = stream.next().await {
                            match chunk_result {
                                Ok(token) => {
                                    print!("{}", token);
                                    io::stdout().flush()?;
                                }
                                Err(e) => {
                                    eprintln!("\nStream error: {}", e);
                                    log::error!("Stream error at iteration {}: {}", iteration + 1, e);
                                }
                            }
                        }
                        println!("\n");
                        log::debug!("Agent streaming iteration {} completed", iteration + 1);
                    }
                    Err(e) => {
                        eprintln!("Error: {}", e);
                        log::error!("Agent error at iteration {}: {}", iteration + 1, e);
                    }
                }
            } else {
                break;
            }
        }

        Ok(())
    }
}
