# Blog & Community

The core feature of the ReghTechLab application is its robust blogging and community engagement system.

## Posts

- **Rich Content:** Posts contain titles, slugs, plain text/markdown content, and excerpts.
- **Categorization:** Posts can be grouped by categories.
- **Read Time Estimation:** The app dynamically calculates the estimated read time of a post based on word count (assuming ~200 words per minute).

## Engagement (Comments & Likes)

- **Comments:** Registered users can leave comments on any published post.
- **Likes:** Users can "like" posts. A strict database unique constraint ensures a user can only like a specific post once.
- **Dynamic Counters:** Display real-time sums for comments and likes via configured SQLAlchemy relationships and properties (`like_count`, `comment_count`).
