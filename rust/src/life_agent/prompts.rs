pub fn build_system_prompt() -> String {
    r#"You are a life assistant agent helping with daily planning, reflection, and goal tracking.

Your responsibilities:
- Help analyze daily progress and logs
- Provide reflection and insights on accomplishments
- Track progress towards goals and milestones
- Suggest improvements and next steps
- Ask thoughtful questions to encourage deeper reflection
- Celebrate wins and learn from challenges

Use the available tools to read and write life system files as needed.
Always be supportive, constructive, and focused on continuous improvement."#
        .to_string()
}

pub fn daily_analyzer_prompt() -> String {
    r#"Analyze today's progress based on the daily log.

Please:
1. Identify what went well today
2. Note any challenges or obstacles
3. Highlight patterns or trends
4. Suggest one thing to focus on tomorrow
5. Provide encouragement and recognition of effort"#
        .to_string()
}

pub fn weekly_summary_prompt() -> String {
    r#"Provide a comprehensive summary of the week.

Include:
1. Major accomplishments
2. Challenges faced and how they were handled
3. Patterns observed throughout the week
4. Progress towards 6-month goals
5. Key learnings and insights
6. Recommendations for the coming week"#
        .to_string()
}

pub fn reflection_prompt() -> String {
    r#"Guide a deep reflection on the current state.

Explore:
1. What has changed in the last week?
2. How am I progressing towards my goals?
3. What am I proud of?
4. What needs adjustment?
5. What am I grateful for?
6. What's the next right step?"#
        .to_string()
}
