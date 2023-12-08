"""add fund type in extension program model

Revision ID: 5a5b94fa34b0
Revises: 6d77ae8577dd
Create Date: 2023-10-17 01:49:00.009399

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a5b94fa34b0'
down_revision = '6d77ae8577dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ExtensionProgram', schema=None) as batch_op:
        batch_op.add_column(sa.Column('FundType', sa.String(length=20), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ExtensionProgram', schema=None) as batch_op:
        batch_op.drop_column('FundType')

    # ### end Alembic commands ###
