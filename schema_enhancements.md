# Schema Enhancements for Grant Deliverables

## Current Schema Analysis
Your existing schema is very sophisticated with vector embeddings and semantic clustering. Here's what we need to add to support your specific research objectives:

## Missing Tables/Fields for Grant Objectives:

### 1. Canadian User Identification
**New Table: `canadian_user_proxies`**
```sql
class CanadianUserProxy(Base):
    __tablename__ = 'canadian_user_proxies'
    
    id = Column(Integer, primary_key=True)
    study_user_id = Column(String(100), unique=True)  # Your hashed ID
    original_username_hash = Column(String(64))  # For emergency unblinding
    canadian_probability = Column(Float)  # 0-1 confidence score
    
    # Proxy indicators
    healthcare_references = Column(Integer, default=0)  # OHIP, MSP mentions
    canadian_spelling_score = Column(Float, default=0.0)  # colour, centre
    timezone_pattern = Column(String(50))  # EST/PST posting patterns
    subreddit_patterns = Column(Text)  # JSON of Canadian subreddit participation
    cultural_markers = Column(Text)  # JSON of Canadian cultural references
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Language Community Analysis
**Enhancement to RedditPost:**
```sql
# Add to RedditPost class:
non_official_language_indicators = Column(Text)  # JSON of detected patterns
code_switching_score = Column(Float)  # Mix of heritage language + eng/fra
translation_patterns = Column(Boolean, default=False)  # Translated content detected
cultural_health_references = Column(Text)  # Traditional medicine mentions
```

### 3. Misinformation Severity Classification
**New Table: `misinformation_severity`**
```sql
class MisinformationSeverity(Base):
    __tablename__ = 'misinformation_severity'
    
    id = Column(Integer, primary_key=True)
    annotation_id = Column(Integer, ForeignKey('post_annotations.id'))
    
    # Your severity spectrum
    severity_level = Column(Integer)  # 1-5 scale
    harm_potential = Column(String(50))  # low/medium/high/critical
    urgency_score = Column(Integer)  # How quickly needs correction
    
    # Categorization
    misinformation_type = Column(String(50))  # misconception/harmful/malicious
    health_topic = Column(String(100))  # PrEP/STI_testing/HIV_treatment
    target_population = Column(String(100))  # newcomers/youth/MSM/general
    
    # Intervention recommendations
    suggested_response = Column(String(50))  # educate/correct/urgent_intervention
    resource_needed = Column(Text)  # What kind of correction/resource
```

### 4. User Interaction Network (for Social Network Analysis)
**New Table: `user_interactions`**
```sql
class UserInteraction(Base):
    __tablename__ = 'user_interactions'
    
    id = Column(Integer, primary_key=True)
    source_user_id = Column(String(100), ForeignKey('canadian_user_proxies.study_user_id'))
    target_user_id = Column(String(100), ForeignKey('canadian_user_proxies.study_user_id'))
    
    interaction_type = Column(String(50))  # reply/mention/thread_participation
    post_id = Column(String(50), ForeignKey('reddit_posts.post_id'))
    comment_id = Column(String(50), ForeignKey('reddit_comments.comment_id'))
    
    interaction_timestamp = Column(DateTime)
    subreddit_context = Column(String(100))
    
    # Network analysis fields
    interaction_weight = Column(Float, default=1.0)  # Frequency/importance
    is_misinformation_related = Column(Boolean, default=False)
```

### 5. Intervention Tracking
**New Table: `intervention_responses`**
```sql
class InterventionResponse(Base):
    __tablename__ = 'intervention_responses'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey('reddit_posts.post_id'))
    severity_id = Column(Integer, ForeignKey('misinformation_severity.id'))
    
    # Generated response
    response_type = Column(String(50))  # fact_check/resource_link/community_alert
    generated_content = Column(Text)  # Auto-generated correction
    resource_links = Column(Text)  # JSON of relevant Canadian resources
    
    # Effectiveness tracking
    was_deployed = Column(Boolean, default=False)
    deployment_timestamp = Column(DateTime)
    effectiveness_score = Column(Float)  # If measurable
```

## Key Enhancements to Existing Tables:

### PostAnnotation - Add severity classification:
```sql
# Add these fields:
severity_level = Column(Integer)  # 1-5 your spectrum
misinformation_type = Column(String(50))  # misconception/harmful/malicious
target_community = Column(String(100))  # Which non-official language community affected
intervention_priority = Column(String(20))  # low/medium/high/urgent
```

### UserStats - Add community expertise:
```sql
# Add these fields:
community_expertise = Column(Text)  # JSON of expertise areas
language_communities = Column(Text)  # Which communities they understand
cultural_competency_score = Column(Float)  # How well they understand context
```

## This Schema Supports:
1. ✅ Canadian user identification through multiple proxy methods
2. ✅ Non-official language community mapping
3. ✅ Misinformation severity spectrum (your key innovation)
4. ✅ Social network analysis of misinformation spread
5. ✅ Intervention response pipeline
6. ✅ Community-specific analysis
7. ✅ Emergency unblinding protocol for safety

## Next Steps:
1. Create migration scripts for these new tables
2. Update your scraping pipeline to populate proxy fields
3. Enhance annotation interface to capture severity data
4. Build network analysis queries using user_interactions
