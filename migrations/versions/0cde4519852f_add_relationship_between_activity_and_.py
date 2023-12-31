"""add relationship between activity and location

Revision ID: 0cde4519852f
Revises: ec50bea773c5
Create Date: 2024-01-02 23:32:53.660756

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0cde4519852f'
down_revision = 'ec50bea773c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('LocationId', sa.Integer(), nullable=True))
        batch_op.alter_column('StartTime',
               existing_type=postgresql.TIME(),
               nullable=False)
        batch_op.alter_column('EndTime',
               existing_type=postgresql.TIME(),
               nullable=False)
        batch_op.create_foreign_key(None, 'Location', ['LocationId'], ['LocationId'])
        batch_op.drop_column('Location')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Location', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('EndTime',
               existing_type=postgresql.TIME(),
               nullable=True)
        batch_op.alter_column('StartTime',
               existing_type=postgresql.TIME(),
               nullable=True)
        batch_op.drop_column('LocationId')

    # ### end Alembic commands ###
