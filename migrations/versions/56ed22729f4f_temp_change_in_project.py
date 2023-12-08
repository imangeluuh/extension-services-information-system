"""temp change in project

Revision ID: 56ed22729f4f
Revises: 977f16967457
Create Date: 2023-11-21 03:41:26.995988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56ed22729f4f'
down_revision = '977f16967457'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Project', schema=None) as batch_op:
        batch_op.alter_column('ProjectTeam',
               existing_type=sa.TEXT(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Project', schema=None) as batch_op:
        batch_op.alter_column('ProjectTeam',
               existing_type=sa.TEXT(),
               nullable=False)

    # ### end Alembic commands ###
