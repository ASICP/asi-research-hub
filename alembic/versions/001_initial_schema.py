"""Initial database schema for ARA v2

Revision ID: 001
Revises:
Create Date: 2025-12-13

Creates all tables for ARA v2:
- users
- papers
- tags
- paper_tags
- tag_combos (with array_sort function)
- citations
- novelty_evals
- bookmarks
- user_activity

Also creates all indexes and constraints from the specification.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create array_sort function for tag_combos
    op.execute("""
    CREATE OR REPLACE FUNCTION array_sort(anyarray)
    RETURNS anyarray AS $$
        SELECT ARRAY(SELECT unnest($1) ORDER BY 1)
    $$ LANGUAGE SQL IMMUTABLE;
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('region', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_active', sa.DateTime(), nullable=False),
        sa.CheckConstraint("tier IN ('student', 'researcher', 'institutional')", name='check_user_tier'),
        sa.CheckConstraint("region IN ('NA', 'EU', 'ASIA', 'OTHER')", name='check_user_region'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_tier', 'users', ['tier'])
    op.create_index('idx_users_region', 'users', ['region'])

    # Create papers table
    op.create_table(
        'papers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('authors', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('tag_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('citation_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('novelty_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('holmes_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('is_diamond', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('scored_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "source IN ('google_scholar', 'crossref', 'semantic_scholar', 'arxiv', 'internal')",
            name='check_paper_source'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_id', name='uq_paper_source_id')
    )
    op.create_index('idx_papers_source', 'papers', ['source'])
    op.create_index('idx_papers_year', 'papers', ['year'])
    op.create_index('idx_papers_holmes_score', 'papers', [sa.text('holmes_score DESC')],
                    postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_papers_is_diamond', 'papers', ['is_diamond'],
                    postgresql_where=sa.text('is_diamond = TRUE AND deleted_at IS NULL'))
    op.create_index('idx_papers_title_search', 'papers', [sa.text("to_tsvector('english', title)")],
                    postgresql_using='gin')
    op.create_index('idx_papers_scored_at', 'papers', [sa.text('scored_at DESC')],
                    postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_papers_created_year', 'papers', ['created_at', 'year'],
                    postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_papers_not_deleted', 'papers', ['deleted_at'],
                    postgresql_where=sa.text('deleted_at IS NULL'))

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('growth_rate', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_tags_name', 'tags', ['name'])
    op.create_index('idx_tags_frequency', 'tags', [sa.text('frequency DESC')])

    # Create paper_tags table
    op.create_table(
        'paper_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('is_novel_combo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'tag_id', name='uq_paper_tag')
    )
    op.create_index('idx_paper_tags_paper', 'paper_tags', ['paper_id'])
    op.create_index('idx_paper_tags_tag', 'paper_tags', ['tag_id'])

    # Create tag_combos table
    op.create_table(
        'tag_combos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tag_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False),
        sa.Column('first_paper_id', sa.Integer(), nullable=True),
        sa.Column('is_novel', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('tag_ids = array_sort(tag_ids)', name='tag_ids_sorted'),
        sa.ForeignKeyConstraint(['first_paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_ids', name='uq_tag_combo_ids')
    )
    op.create_index('idx_tag_combos_tags', 'tag_combos', ['tag_ids'], postgresql_using='gin')
    op.create_index('idx_tag_combos_novel', 'tag_combos', ['is_novel'],
                    postgresql_where=sa.text('is_novel = TRUE'))
    op.create_index('idx_tag_combos_frequency', 'tag_combos', [sa.text('frequency DESC')])

    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('citing_paper_id', sa.Integer(), nullable=False),
        sa.Column('cited_paper_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['citing_paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cited_paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('citing_paper_id', 'cited_paper_id', name='uq_citation')
    )
    op.create_index('idx_citations_citing', 'citations', ['citing_paper_id'])
    op.create_index('idx_citations_cited', 'citations', ['cited_paper_id'])

    # Create novelty_evals table
    op.create_table(
        'novelty_evals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('prompt_sent', sa.Text(), nullable=False),
        sa.Column('claude_response', sa.Text(), nullable=True),
        sa.Column('novelty_verdict', sa.String(length=20), nullable=True),
        sa.Column('confidence', sa.DECIMAL(precision=3, scale=2), nullable=True),
        sa.Column('api_cost', sa.DECIMAL(precision=8, scale=6), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "novelty_verdict IN ('highly_novel', 'moderately_novel', 'incremental', 'derivative')",
            name='check_novelty_verdict'
        ),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_novelty_evals_paper', 'novelty_evals', ['paper_id'])
    op.create_index('idx_novelty_evals_verdict', 'novelty_evals', ['novelty_verdict'])
    op.create_index('idx_novelty_evals_date', 'novelty_evals', [sa.text('evaluated_at DESC')])

    # Create bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'paper_id', name='uq_user_paper_bookmark')
    )
    op.create_index('idx_bookmarks_user', 'bookmarks', ['user_id'])

    # Create user_activity table
    op.create_table(
        'user_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=True),
        sa.Column('action_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "action_type IN ('search', 'view_paper', 'bookmark', 'unbookmark', "
            "'export_notebooklm', 'view_mindmap', 'adjust_weights')",
            name='check_action_type'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_activity_user', 'user_activity', ['user_id'])
    op.create_index('idx_user_activity_type', 'user_activity', ['action_type'])
    op.create_index('idx_user_activity_time', 'user_activity', [sa.text('created_at DESC')])
    op.create_index('idx_user_activity_metadata', 'user_activity', ['action_metadata'],
                    postgresql_using='gin')
    op.create_index('idx_user_activity_user_time', 'user_activity',
                    ['user_id', sa.text('created_at DESC')])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_activity')
    op.drop_table('bookmarks')
    op.drop_table('novelty_evals')
    op.drop_table('citations')
    op.drop_table('tag_combos')
    op.drop_table('paper_tags')
    op.drop_table('tags')
    op.drop_table('papers')
    op.drop_table('users')

    # Drop array_sort function
    op.execute("DROP FUNCTION IF EXISTS array_sort(anyarray);")
