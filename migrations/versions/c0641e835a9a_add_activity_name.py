"""add activity name

Revision ID: c0641e835a9a
Revises: 0348814d067d
Create Date: 2023-09-09 15:27:54.121408

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0641e835a9a'
down_revision = '0348814d067d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ActivityName', sa.String(length=255), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.drop_column('ActivityName')

    # ### end Alembic commands ###
