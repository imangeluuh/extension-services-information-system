"""change survey to evaluation

Revision ID: 977f16967457
Revises: f3afe38ce134
Create Date: 2023-11-21 01:38:38.198115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '977f16967457'
down_revision = 'f3afe38ce134'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Evaluation',
    sa.Column('EvaluationId', sa.Integer(), nullable=False),
    sa.Column('EvaluationName', sa.Text(), nullable=False),
    sa.Column('ActivityId', sa.Integer(), nullable=False),
    sa.Column('State', sa.Integer(), nullable=False),
    sa.Column('Questions', sa.Text(), nullable=False),
    sa.Column('CreatedAt', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['ActivityId'], ['Activity.ActivityId'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('EvaluationId')
    )
    op.drop_table('Survey')
    with op.batch_alter_table('Response', schema=None) as batch_op:
        batch_op.add_column(sa.Column('EvaluationId', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'Evaluation', ['EvaluationId'], ['EvaluationId'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Response', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('EvaluationId')

    op.create_table('Survey',
    sa.Column('SurveyId', sa.INTEGER(), server_default=sa.text('nextval(\'"Survey_SurveyId_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('SurveyName', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('ActivityId', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('State', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('Questions', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('CreatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['ActivityId'], ['Activity.ActivityId'], name='Survey_ActivityId_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('SurveyId', name='Survey_pkey')
    )
    op.drop_table('Evaluation')
    # ### end Alembic commands ###