pub fn setup_logging() {
    env_logger::builder()
        .format_timestamp_millis()
        .try_init()
        .ok();
}
