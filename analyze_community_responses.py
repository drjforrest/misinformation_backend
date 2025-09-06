#!/usr/bin/env python3
"""
Analyze community responses and interactions in the collected data
"""

from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment
from collections import Counter

def analyze_community_responses():
    """Analyze the community responses (comments) in the database"""
    print("💬 Analyzing Community Responses")
    print("=" * 50)

    db = DataPersistenceManager()
    session = db.get_session()

    # Get comment statistics
    total_comments = session.query(RedditComment).count()
    total_posts = session.query(RedditPost).count()

    print(f"📊 Overview:")
    print(f"  Total posts: {total_posts}")
    print(f"  Total comments: {total_comments}")
    print(f"  Average comments per post: {total_comments/total_posts:.1f}")

    # Analyze comment engagement by subreddit
    print(f"\n💬 Comment Engagement by Subreddit:")
    subreddit_comments = {}

    for post in session.query(RedditPost).all():
        comment_count = session.query(RedditComment).filter_by(post_id=post.post_id).count()
        if post.subreddit not in subreddit_comments:
            subreddit_comments[post.subreddit] = {'posts': 0, 'comments': 0, 'total_score': 0}

        subreddit_comments[post.subreddit]['posts'] += 1
        subreddit_comments[post.subreddit]['comments'] += comment_count

    # Sort by engagement
    for subreddit, data in sorted(subreddit_comments.items(), key=lambda x: x[1]['comments'], reverse=True):
        avg_comments = data['comments'] / data['posts'] if data['posts'] > 0 else 0
        print(f"  r/{subreddit}: {data['comments']} comments across {data['posts']} posts (avg: {avg_comments:.1f})")

    # Show sample community responses
    print(f"\n🗣️  Sample Community Responses:")

    # Get posts with most comments
    popular_posts = []
    for post in session.query(RedditPost).all():
        comment_count = session.query(RedditComment).filter_by(post_id=post.post_id).count()
        if comment_count > 5:  # Posts with substantial discussion
            popular_posts.append((post, comment_count))

    popular_posts.sort(key=lambda x: x[1], reverse=True)

    for i, (post, comment_count) in enumerate(popular_posts[:5]):
        print(f"\n{i+1}. r/{post.subreddit} - {comment_count} comments")
        print(f"   POST: {post.title[:80]}...")

        # Show top 3 comments for this post
        comments = session.query(RedditComment).filter_by(post_id=post.post_id).order_by(RedditComment.score.desc()).limit(3).all()

        for j, comment in enumerate(comments):
            comment_preview = comment.body.replace('\n', ' ')[:100] + "..." if len(comment.body) > 100 else comment.body.replace('\n', ' ')
            print(f"   RESPONSE {j+1} (score: {comment.score}): {comment_preview}")

    # Analyze response patterns
    print(f"\n📈 Response Patterns:")

    # Comment length analysis
    comment_lengths = []
    comment_scores = []

    for comment in session.query(RedditComment).limit(1000).all():  # Sample to avoid memory issues
        comment_lengths.append(len(comment.body))
        comment_scores.append(comment.score)

    if comment_lengths:
        avg_length = sum(comment_lengths) / len(comment_lengths)
        avg_score = sum(comment_scores) / len(comment_scores)
        print(f"  Average comment length: {avg_length:.0f} characters")
        print(f"  Average comment score: {avg_score:.1f}")

    # Find most active commenters
    print(f"\n👥 Most Active Community Members:")
    author_counts = Counter()

    for comment in session.query(RedditComment).all():
        if comment.author and comment.author != '[deleted]':
            author_counts[comment.author] += 1

    for author, count in author_counts.most_common(10):
        print(f"  {author}: {count} comments")

    # Health-related discussion analysis
    print(f"\n🏥 Health-Related Community Discussions:")
    health_keywords = ['health', 'doctor', 'medicine', 'treatment', 'symptoms', 'therapy', 'medical', 'hospital', 'clinic', 'hiv', 'prep', 'std', 'mental health', 'anxiety', 'depression']

    health_comments = 0
    total_analyzed = 0

    for comment in session.query(RedditComment).limit(1000).all():
        total_analyzed += 1
        comment_text = comment.body.lower()
        if any(keyword in comment_text for keyword in health_keywords):
            health_comments += 1

    health_percentage = (health_comments / total_analyzed * 100) if total_analyzed > 0 else 0
    print(f"  Health-related comments: {health_comments}/{total_analyzed} ({health_percentage:.1f}%)")

    # Sample health-related responses
    print(f"\n💊 Sample Health-Related Community Responses:")
    health_response_count = 0

    for comment in session.query(RedditComment).limit(2000).all():
        comment_text = comment.body.lower()
        if any(keyword in comment_text for keyword in health_keywords) and len(comment.body) > 50:
            if health_response_count < 3:
                response_preview = comment.body.replace('\n', ' ')[:150] + "..." if len(comment.body) > 150 else comment.body.replace('\n', ' ')
                print(f"  • (score: {comment.score}) {response_preview}")
                health_response_count += 1

    session.close()

    print(f"\n" + "=" * 50)
    print(f"✅ Community Response Analysis Complete!")
    print(f"💡 You have substantial community discussion data with {total_comments} responses")
    print(f"   to analyze for community resilience and peer support patterns.")

if __name__ == "__main__":
    analyze_community_responses()
